from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.discussions.models import Comment
from apps.moderation.models import ModerationAction, Report
from apps.publications.models import Publication


@transaction.atomic
def create_report(*, reporter, target_type, target, reason, details=""):
    kwargs = {
        "reporter": reporter,
        "target_type": target_type,
        "reason": reason,
        "details": details.strip(),
    }

    if target_type == Report.TargetType.PUBLICATION:
        kwargs["publication"] = target
    elif target_type == Report.TargetType.COMMENT:
        kwargs["comment"] = target
    elif target_type == Report.TargetType.USER:
        kwargs["target_user"] = target
    else:
        raise ValueError("Unsupported report target type.")

    try:
        return Report.objects.create(**kwargs)
    except IntegrityError as exc:
        raise ValueError("You already have an active report for this target.") from exc


@transaction.atomic
def update_report_status(*, report, moderator, status, resolution_note=""):
    report = Report.objects.select_for_update().get(pk=report.pk)

    if status not in Report.Status.values:
        raise ValueError("Invalid report status.")

    report.status = status
    report.moderator = moderator
    report.resolution_note = resolution_note.strip()
    report.resolved_at = (
        timezone.now()
        if status in {Report.Status.RESOLVED, Report.Status.DISMISSED}
        else None
    )
    report.save(
        update_fields=[
            "status",
            "moderator",
            "resolution_note",
            "resolved_at",
            "updated_at",
        ]
    )
    return report


def _validate_optional_report(report, *, target_type, target_pk):
    if report is None:
        return

    if report.target_type != target_type:
        raise ValueError("Report target type does not match moderation target.")

    report_target_pk = {
        Report.TargetType.PUBLICATION: report.publication_id,
        Report.TargetType.COMMENT: report.comment_id,
    }.get(target_type)

    if report_target_pk != target_pk:
        raise ValueError("Report does not refer to this moderation target.")


@transaction.atomic
def set_publication_hidden(*, publication, moderator, hidden, reason="", report=None):
    publication = Publication.objects.select_for_update().get(pk=publication.pk)
    _validate_optional_report(
        report,
        target_type=Report.TargetType.PUBLICATION,
        target_pk=publication.pk,
    )

    desired = (
        Publication.Visibility.HIDDEN
        if hidden
        else Publication.Visibility.PUBLISHED
    )
    action = (
        ModerationAction.Action.HIDE
        if hidden
        else ModerationAction.Action.UNHIDE
    )

    if publication.visibility == desired:
        return publication, False

    publication.visibility = desired
    publication.save(update_fields=["visibility", "updated_at"])

    ModerationAction.objects.create(
        actor=moderator,
        target_type=ModerationAction.TargetType.PUBLICATION,
        publication=publication,
        action=action,
        reason=reason.strip(),
        report=report,
    )
    return publication, True


@transaction.atomic
def set_comment_hidden(*, comment, moderator, hidden, reason="", report=None):
    comment = Comment.objects.select_for_update().get(pk=comment.pk)
    _validate_optional_report(
        report,
        target_type=Report.TargetType.COMMENT,
        target_pk=comment.pk,
    )

    desired = Comment.Visibility.HIDDEN if hidden else Comment.Visibility.PUBLISHED
    action = ModerationAction.Action.HIDE if hidden else ModerationAction.Action.UNHIDE

    if comment.visibility == desired:
        return comment, False

    comment.visibility = desired
    update_fields = ["visibility", "updated_at"]

    # A hidden accepted answer must not block accepting another visible answer.
    if hidden and comment.is_accepted:
        comment.is_accepted = False
        update_fields.append("is_accepted")

    comment.save(update_fields=update_fields)

    ModerationAction.objects.create(
        actor=moderator,
        target_type=ModerationAction.TargetType.COMMENT,
        comment=comment,
        action=action,
        reason=reason.strip(),
        report=report,
    )
    return comment, True
