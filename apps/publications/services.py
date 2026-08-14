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
    links = PublicationMedia.objects.filter(publication=publication).select_related("asset").order_by("role", "sort_order", "id")
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

@transaction.atomic
def create_publication(*, author, kind, title, content, community, tag_names):
    publication = Publication.objects.create(
        author=author, community=community, kind=kind, title=title.strip(), content=content,
        content_text=extract_plain_text(content), current_revision=1,
    )
    publication.tags.set(get_or_create_tags(tag_names))
    create_revision_snapshot(publication, author)
    return publication

@transaction.atomic
def update_publication(*, publication, editor, changes):
    publication = Publication.objects.select_for_update().get(pk=publication.pk)
    if publication.author_id != editor.pk:
        raise PermissionError("Only the author can edit this publication.")
    changed = False
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
    if "tag_names" in changes:
        tags = get_or_create_tags(changes["tag_names"])
        old_ids = set(publication.tags.values_list("id", flat=True))
        new_ids = {tag.id for tag in tags}
        if old_ids != new_ids:
            publication.tags.set(tags)
            changed = True
    if not changed:
        return publication
    publication.current_revision += 1
    publication.save()
    create_revision_snapshot(publication, editor)
    return publication
