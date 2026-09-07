from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.communities.models import Community
from apps.discussions.models import Comment
from apps.notifications.models import Notification, NotificationEvent
from apps.notifications.tasks import cleanup_old_notifications
from apps.publications.models import Publication
from apps.users.models import User


class NotificationCenterTests(TestCase):
    def setUp(self):
        self.viewer = self._user("viewer")
        self.actor = self._user("actor")
        self.client = APIClient()
        self.client.force_authenticate(self.viewer)

    def _user(self, nickname):
        return User.objects.create_user(
            nickname=nickname,
            email=f"{nickname}@example.com",
            password="Test-password-2026!",
            first_name=nickname.title(),
            last_name="Example",
            country="RU",
            nationality="RU",
        )

    def _publication(self, *, community=None):
        return Publication.objects.create(
            author=self.actor,
            community=community,
            kind=Publication.Type.POST,
            title="Night Iris update",
            content=[{"type": "paragraph", "text": "Update body"}],
            content_text="Update body",
        )

    def _notification(self, kind, *, publication=None, comment=None):
        event = NotificationEvent.objects.create(
            kind=kind,
            actor=self.actor,
            target_user=self.viewer,
            publication=publication,
            comment=comment,
            status=NotificationEvent.Status.DONE,
            processed_at=timezone.now(),
        )
        return Notification.objects.create(
            event=event,
            recipient=self.viewer,
            actor=self.actor,
            kind=kind,
            publication=publication,
            comment=comment,
        )

    def test_list_exposes_category_priority_label_and_deep_link(self):
        publication = self._publication()
        comment = Comment.objects.create(
            publication=publication,
            author=self.actor,
            kind=Comment.Kind.COMMENT,
            content=[{"type": "paragraph", "text": "A concrete reply"}],
            content_text="A concrete reply",
        )
        notification = self._notification(
            NotificationEvent.Kind.PUBLICATION_RESPONSE,
            publication=publication,
            comment=comment,
        )

        response = self.client.get("/api/v1/notifications/")

        self.assertEqual(response.status_code, 200)
        item = response.data["results"][0]
        self.assertEqual(item["id"], str(notification.public_id))
        self.assertEqual(item["category"], "replies")
        self.assertEqual(item["priority"], "normal")
        self.assertEqual(item["label"], "Новый ответ на публикацию")
        self.assertEqual(
            item["target_url"],
            f"/publications/{publication.public_id}#comment-{comment.public_id}",
        )

    def test_category_filter_separates_community_and_social_notifications(self):
        community = Community.objects.create(
            slug="dev-lab",
            name="Dev Lab",
            description="Development",
            owner=self.viewer,
        )
        community_publication = self._publication(community=community)
        social_publication = self._publication()
        community_notification = self._notification(
            NotificationEvent.Kind.NEW_PUBLICATION,
            publication=community_publication,
        )
        social_notification = self._notification(
            NotificationEvent.Kind.NEW_PUBLICATION,
            publication=social_publication,
        )

        community_response = self.client.get("/api/v1/notifications/?category=communities")
        social_response = self.client.get("/api/v1/notifications/?category=social")

        self.assertEqual(
            [item["id"] for item in community_response.data["results"]],
            [str(community_notification.public_id)],
        )
        self.assertEqual(
            [item["id"] for item in social_response.data["results"]],
            [str(social_notification.public_id)],
        )

    def test_batch_read_marks_only_owned_requested_notifications(self):
        first = self._notification(NotificationEvent.Kind.NEW_FOLLOWER)
        second = self._notification(NotificationEvent.Kind.NEW_FOLLOWER)
        outsider = self._user("outsider")
        outsider_event = NotificationEvent.objects.create(
            kind=NotificationEvent.Kind.NEW_FOLLOWER,
            actor=self.actor,
            target_user=outsider,
            status=NotificationEvent.Status.DONE,
        )
        outsider_notification = Notification.objects.create(
            event=outsider_event,
            recipient=outsider,
            actor=self.actor,
            kind=NotificationEvent.Kind.NEW_FOLLOWER,
        )

        response = self.client.put(
            "/api/v1/notifications/read/",
            {"ids": [str(first.public_id), str(outsider_notification.public_id)]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated"], 1)
        first.refresh_from_db()
        second.refresh_from_db()
        outsider_notification.refresh_from_db()
        self.assertIsNotNone(first.read_at)
        self.assertIsNone(second.read_at)
        self.assertIsNone(outsider_notification.read_at)

    def test_category_read_all_does_not_touch_other_categories(self):
        publication = self._publication()
        reply = self._notification(
            NotificationEvent.Kind.PUBLICATION_RESPONSE,
            publication=publication,
        )
        social = self._notification(NotificationEvent.Kind.NEW_FOLLOWER)

        response = self.client.put("/api/v1/notifications/read-all/?category=replies")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated"], 1)
        reply.refresh_from_db()
        social.refresh_from_db()
        self.assertIsNotNone(reply.read_at)
        self.assertIsNone(social.read_at)

    def test_retention_removes_old_notifications_then_orphaned_done_events(self):
        notification = self._notification(NotificationEvent.Kind.NEW_FOLLOWER)
        event_id = notification.event_id
        old = timezone.now() - timedelta(days=200)
        Notification.objects.filter(pk=notification.pk).update(created_at=old)
        NotificationEvent.objects.filter(pk=event_id).update(created_at=old)

        cleanup_old_notifications()

        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())
        self.assertFalse(NotificationEvent.objects.filter(pk=event_id).exists())
