from django.db import IntegrityError, transaction

from apps.discussions.content import extract_comment_text
from apps.discussions.models import Comment, CommentRevision, CommentVote
from apps.publications.models import Publication


MAX_COMMENT_DEPTH = 8


def create_comment_revision(comment, editor):
    return CommentRevision.objects.create(
        comment=comment,
        revision_number=comment.current_revision,
        editor=editor,
        content=comment.content,
    )


@transaction.atomic
def create_root_comment(*, publication, author, content):
    publication = (
        Publication.objects
        .select_for_update()
        .get(pk=publication.pk)
    )

    if publication.visibility != Publication.Visibility.PUBLISHED:
        raise ValueError("Publication is not available.")

    if publication.kind == Publication.Type.TOPIC:
        kind = Comment.Kind.ANSWER
    else:
        kind = Comment.Kind.COMMENT

    try:
        comment = Comment.objects.create(
            publication=publication,
            author=author,
            parent=None,
            kind=kind,
            content=content,
            content_text=extract_comment_text(content),
            depth=0,
        )
    except IntegrityError as exc:
        if kind == Comment.Kind.ANSWER:
            raise ValueError(
                "You already have an answer in this topic."
            ) from exc
        raise

    create_comment_revision(comment, author)
    return comment


@transaction.atomic
def create_reply(*, parent, author, content):
    parent = (
        Comment.objects
        .select_for_update()
        .select_related("publication")
        .get(pk=parent.pk)
    )

    if parent.visibility != Comment.Visibility.PUBLISHED:
        raise ValueError("Cannot reply to hidden comment.")

    if parent.publication.visibility != Publication.Visibility.PUBLISHED:
        raise ValueError("Publication is not available.")

    depth = parent.depth + 1
    if depth > MAX_COMMENT_DEPTH:
        raise ValueError("Maximum discussion depth reached.")

    comment = Comment.objects.create(
        publication=parent.publication,
        author=author,
        parent=parent,
        kind=Comment.Kind.REPLY,
        content=content,
        content_text=extract_comment_text(content),
        depth=depth,
    )

    create_comment_revision(comment, author)
    return comment


@transaction.atomic
def update_comment(*, comment, editor, content):
    comment = (
        Comment.objects
        .select_for_update()
        .get(pk=comment.pk)
    )

    if comment.author_id != editor.pk:
        raise ValueError("Only the author can edit this comment.")

    if comment.visibility != Comment.Visibility.PUBLISHED:
        raise ValueError("Hidden comments cannot be edited.")

    if comment.content == content:
        return comment

    comment.content = content
    comment.content_text = extract_comment_text(content)
    comment.current_revision += 1
    comment.save(
        update_fields=[
            "content",
            "content_text",
            "current_revision",
            "updated_at",
        ]
    )

    create_comment_revision(comment, editor)
    return comment


@transaction.atomic
def set_comment_vote(*, comment, user, value):
    """Set +1/-1 vote and update the cached comment score atomically."""
    if value not in (-1, 1):
        raise ValueError("Vote must be either -1 or 1.")

    comment = (
        Comment.objects
        .select_for_update()
        .get(pk=comment.pk)
    )

    if comment.visibility != Comment.Visibility.PUBLISHED:
        raise ValueError("Cannot vote on a hidden comment.")

    if comment.author_id == user.pk:
        raise ValueError("You cannot vote for your own comment.")

    vote = (
        CommentVote.objects
        .filter(comment=comment, user=user)
        .first()
    )

    if vote is None:
        CommentVote.objects.create(
            comment=comment,
            user=user,
            value=value,
        )
        delta = value
    elif vote.value == value:
        # PUT is idempotent: requesting the current state changes nothing.
        return comment, value
    else:
        old_value = vote.value
        vote.value = value
        vote.save(update_fields=["value", "updated_at"])
        delta = value - old_value

    comment.score += delta
    comment.save(update_fields=["score", "updated_at"])

    return comment, value


@transaction.atomic
def remove_comment_vote(*, comment, user):
    """Remove the user's vote, if any, and repair the cached score."""
    comment = (
        Comment.objects
        .select_for_update()
        .get(pk=comment.pk)
    )

    vote = (
        CommentVote.objects
        .filter(comment=comment, user=user)
        .first()
    )

    if vote is None:
        # DELETE is idempotent.
        return comment

    comment.score -= vote.value
    vote.delete()
    comment.save(update_fields=["score", "updated_at"])

    return comment
