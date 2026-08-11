from django.db import transaction
from django.utils.text import slugify

from apps.publications.content import (
    extract_plain_text,
)
from apps.publications.models import (
    Publication,
    PublicationRevision,
    Tag,
)

def get_or_create_tags(tag_names):
    tags = []

    for raw_name in tag_names:
        name = raw_name.strip()

        if not name:
            continue

        slug = slugify(
            name,
            allow_unicode=True,
        ).lower()

        if not slug:
            continue

        tag, _ = Tag.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
            },
        )

        tags.append(tag)

    return tags

def build_tags_snapshot(publication):
    return list(
        publication.tags
        .order_by("slug")
        .values(
            "name",
            "slug",
        )
    )

@transaction.atomic
def create_publication(
    *,
    author,
    kind,
    title,
    content,
    community,
    tag_names,
):
    publication = Publication.objects.create(
        author=author,
        community=community,
        kind=kind,
        title=title.strip(),
        content=content,
        content_text=extract_plain_text(
            content
        ),
        current_revision=1,
    )

    tags = get_or_create_tags(
        tag_names
    )

    publication.tags.set(tags)

    PublicationRevision.objects.create(
        publication=publication,
        revision_number=1,
        editor=author,
        title=publication.title,
        content=publication.content,
        tags_snapshot=build_tags_snapshot(
            publication
        ),
    )

    return publication

@transaction.atomic
def update_publication(
    *,
    publication,
    editor,
    changes,
):
    publication = (
        Publication.objects
        .select_for_update()
        .get(pk=publication.pk)
    )

    if publication.author_id != editor.pk:
        raise PermissionError(
            "Only the author can edit this publication."
        )

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
            publication.content_text = (
                extract_plain_text(
                    new_content
                )
            )
            changed = True

    if "tag_names" in changes:
        tags = get_or_create_tags(
            changes["tag_names"]
        )

        old_tag_ids = set(
            publication.tags.values_list(
                "id",
                flat=True,
            )
        )

        new_tag_ids = {
            tag.id
            for tag in tags
        }

        if old_tag_ids != new_tag_ids:
            publication.tags.set(tags)
            changed = True

    if not changed:
        return publication

    publication.current_revision += 1

    publication.save()

    PublicationRevision.objects.create(
        publication=publication,
        revision_number=(
            publication.current_revision
        ),
        editor=editor,
        title=publication.title,
        content=publication.content,
        tags_snapshot=build_tags_snapshot(
            publication
        ),
    )

    return publication