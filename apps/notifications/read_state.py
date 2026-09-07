from django.db import transaction
from django.utils import timezone

from apps.notifications.cache import invalidate_unread_count
from apps.notifications.models import Notification
from apps.notifications.selectors import notification_queryset


@transaction.atomic
def mark_many_read(*, user, public_ids):
    ids = {str(value) for value in public_ids}
    if not ids:
        return 0
    updated = Notification.objects.filter(
        recipient=user,
        public_id__in=ids,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    if updated:
        invalidate_unread_count([user.pk])
    return updated


@transaction.atomic
def mark_category_read(*, user, category=None):
    updated = notification_queryset(user, category=category).filter(
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    if updated:
        invalidate_unread_count([user.pk])
    return updated
