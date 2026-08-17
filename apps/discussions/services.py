from django.db import IntegrityError, transaction

from apps.discussions.content import extract_comment_text
from apps.discussions.models import Comment, CommentRevision, CommentVote
from apps.publications.models import Publication
from apps.social.services import users_have_block_between


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

    if users_have_block_between(author, publication.author):
        raise ValueError("Interaction is unavailable because a user block is active.")

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

    if users_have_block_between(author, parent.author):
        raise ValueError("Interaction is unavailable because a user block is active.")

    if users_have_block_between(author, parent.publication.author):
        raise ValueError("Interaction is unavailable on a blocked user's publication.")

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
        .select_related("publication")
        .get(pk=comment.pk)
    )

    if comment.visibility != Comment.Visibility.PUBLISHED:
        raise ValueError("Cannot vote on a hidden comment.")

    if comment.publication.visibility != Publication.Visibility.PUBLISHED:
        raise ValueError("Publication is not available.")

    if comment.author_id == user.pk:
        raise ValueError("You cannot vote for your own comment.")

    if users_have_block_between(user, comment.author):
        raise ValueError("Interaction is unavailable because a user block is active.")

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
    comment.save(update_fields=["score"])

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
    comment.save(update_fields=["score"])

    return comment

@transaction.atomic
def accept_answer(*, answer, actor):
    """Accept a root Topic answer. The Topic author is the only manager.

    The publication row is locked first so two concurrent attempts to accept
    different answers for the same Topic are serialized without relying only
    on the partial unique constraint.
    """
    publication_id = answer.publication_id

    publication = (
        Publication.objects
        .select_for_update()
        .get(pk=publication_id)
    )

    answer = (
        Comment.objects
        .select_for_update()
        .get(pk=answer.pk)
    )

    if publication.kind != Publication.Type.TOPIC:
        raise ValueError("Accepted answers are available only for topics.")

    if publication.visibility != Publication.Visibility.PUBLISHED:
        raise ValueError("Publication is not available.")

    if publication.author_id != actor.pk:
        raise PermissionError("Only the topic author can accept an answer.")

    if answer.publication_id != publication.pk:
        raise ValueError("Answer does not belong to this topic.")

    if answer.kind != Comment.Kind.ANSWER or answer.parent_id is not None:
        raise ValueError("Only a root topic answer can be accepted.")

    if answer.visibility != Comment.Visibility.PUBLISHED:
        raise ValueError("A hidden answer cannot be accepted.")

    if users_have_block_between(actor, answer.author):
        raise ValueError("A blocked user's answer cannot be accepted while the block is active.")

    previous = (
        Comment.objects
        .select_for_update()
        .filter(
            publication=publication,
            is_accepted=True,
        )
        .exclude(pk=answer.pk)
        .first()
    )

    if previous is not None:
        previous.is_accepted = False
        previous.save(update_fields=["is_accepted"])

    if not answer.is_accepted:
        answer.is_accepted = True
        answer.save(update_fields=["is_accepted"])

    return answer


@transaction.atomic
def unaccept_answer(*, answer, actor):
    """Remove accepted state from an answer. DELETE semantics are idempotent."""
    publication_id = answer.publication_id

    publication = (
        Publication.objects
        .select_for_update()
        .get(pk=publication_id)
    )

    answer = (
        Comment.objects
        .select_for_update()
        .get(pk=answer.pk)
    )

    if publication.kind != Publication.Type.TOPIC:
        raise ValueError("Accepted answers are available only for topics.")

    if publication.author_id != actor.pk:
        raise PermissionError("Only the topic author can unaccept an answer.")

    if answer.kind != Comment.Kind.ANSWER or answer.parent_id is not None:
        raise ValueError("Only a root topic answer can be accepted.")

    if answer.is_accepted:
        answer.is_accepted = False
        answer.save(update_fields=["is_accepted"])

    return answer

