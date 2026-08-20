from django.db import transaction
from django.utils.text import slugify

from apps.publications.content import extract_plain_text
from apps.publications.models import Publication, PublicationRevision, Tag


def get_or_create_tags(tag_names):
    tags = []
    seen = set()
    for raw_name in tag_names:
        name = raw_name.strip()
        if not name:
            continue
        slug = slugify(name, allow_unicode=True).lower()
        if not slug or slug in seen:
            continue
        seen.add(slug)
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
        tags.append(tag)
    return tags


def build_tags_snapshot(publication):
    return list(publication.tags.order_by("slug").values("name", "slug"))


def build_media_snapshot(publication):
    from apps.media.models import PublicationMedia

    links = (
        PublicationMedia.objects
        .filter(publication=publication)
        .select_related("asset")
        .order_by("role", "sort_order", "id")
    )
    return [
        {
            "asset_id": str(link.asset.public_id),
            "role": link.role,
            "sort_order": link.sort_order,
            "name": link.asset.original_name,
            "kind": link.asset.kind,
            "size_bytes": link.asset.size_bytes,
        }
        for link in links
    ]


def create_revision_snapshot(publication, editor):
    return PublicationRevision.objects.create(
        publication=publication,
        revision_number=publication.current_revision,
        editor=editor,
        title=publication.title,
        content=publication.content,
        tags_snapshot=build_tags_snapshot(publication),
        media_snapshot=build_media_snapshot(publication),
    )


def _content_media_spec(content):
    result = []
    order = 0
    for block in content:
        block_type = block.get("type")
        if block_type not in {"image", "video", "attachment"}:
            continue
        role = "attachment" if block_type == "attachment" else "inline"
        result.append((str(block["asset_id"]), role, order, block_type))
        order += 1
    return result


def sync_content_media(*, publication, owner, content):
    """Make current inline/attachment links match structured content.

    Old revision snapshots remain immutable; only current PublicationMedia links are
    synchronized. Preview image/video links are managed by the explicit media API.
    """
    from apps.media.models import MediaAsset, PublicationMedia

    specs = _content_media_spec(content)
    ids = [asset_id for asset_id, _, _, _ in specs]
    assets = {
        str(asset.public_id): asset
        for asset in MediaAsset.objects.filter(public_id__in=ids)
    }

    for asset_id, _, _, block_type in specs:
        asset = assets.get(asset_id)
        if asset is None:
            raise ValueError(f"Media asset {asset_id} was not found.")
        if asset.owner_id != owner.pk:
            raise ValueError("All content media must belong to the publication author.")
        if asset.status != MediaAsset.Status.READY:
            raise ValueError(f"Media asset {asset.original_name} is not ready.")
        if block_type == "image" and asset.kind != MediaAsset.Kind.IMAGE:
            raise ValueError("Image block must reference an image asset.")
        if block_type == "video" and asset.kind != MediaAsset.Kind.VIDEO:
            raise ValueError("Video block must reference a video asset.")

    current_links = PublicationMedia.objects.filter(
        publication=publication,
        role__in=[PublicationMedia.Role.INLINE, PublicationMedia.Role.ATTACHMENT],
    )
    wanted = {(asset_id, role) for asset_id, role, _, _ in specs}
    for link in list(current_links.select_related("asset")):
        key = (str(link.asset.public_id), link.role)
        if key not in wanted:
            link.delete()

    for asset_id, role, sort_order, _ in specs:
        asset = assets[asset_id]
        link, _ = PublicationMedia.objects.get_or_create(
            publication=publication,
            asset=asset,
            role=role,
            defaults={"sort_order": sort_order},
        )
        if link.sort_order != sort_order:
            link.sort_order = sort_order
            link.save(update_fields=["sort_order"])


@transaction.atomic
def create_publication(*, author, kind, title, content, community, tag_names):
    publication = Publication.objects.create(
        author=author,
        community=community,
        kind=kind,
        title=title.strip(),
        content=content,
        content_text=extract_plain_text(content),
        current_revision=1,
    )
    publication.tags.set(get_or_create_tags(tag_names))
    sync_content_media(publication=publication, owner=author, content=content)
    create_revision_snapshot(publication, author)

    from apps.notifications.events import emit_notification_event
    from apps.notifications.models import NotificationEvent

    emit_notification_event(
        kind=NotificationEvent.Kind.NEW_PUBLICATION,
        actor=author,
        publication=publication,
    )
    from apps.identity.services import sync_identity_state
    sync_identity_state(author)
    return publication


@transaction.atomic
def update_publication(*, publication, editor, changes):
    publication = Publication.objects.select_for_update().get(pk=publication.pk)
    if publication.author_id != editor.pk:
        raise PermissionError("Only the author can edit this publication.")
    changed = False
    content_changed = False
    if "title" in changes:
        new_title = changes["title"].strip()
        if new_title != publication.title:
            publication.title = new_title
            changed = True
    if "content" in changes:
        new_content = changes["content"]
        if new_content != publication.content:
            publication.content = new_content
            publication.content_text = extract_plain_text(new_content)
            changed = True
            content_changed = True
    if "tag_names" in changes:
        tags = get_or_create_tags(changes["tag_names"])
        old_ids = set(publication.tags.values_list("id", flat=True))
        new_ids = {tag.id for tag in tags}
        if old_ids != new_ids:
            publication.tags.set(tags)
            changed = True
    if not changed:
        return publication
    if content_changed:
        sync_content_media(publication=publication, owner=editor, content=publication.content)
    publication.current_revision += 1
    publication.save()
    create_revision_snapshot(publication, editor)
    return publication
