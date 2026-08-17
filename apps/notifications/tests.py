from django.test import TestCase

from apps.notifications.models import Notification, NotificationEvent, NotificationPreference
from apps.notifications.services import dispatch_notification_event, mark_all_notifications_read
from apps.publications.models import Publication
from apps.social.models import CommunitySubscription, UserFollow, UserMute
from apps.users.models import User


class NotificationDispatchTests(TestCase):
    def make_user(self, nickname):
        return User.objects.create_user(
            nickname=nickname,
            email=f"{nickname.lower()}@example.com",
            password="Test-password-2026!",
            first_name=nickname,
            last_name="Test",
            country="RU",
            nationality="RU",
        )

    def make_publication(self, author, community=None):
        return Publication.objects.create(
            author=author,
            community=community,
            kind=Publication.Type.POST,
            title="Test publication",
            content=[{"type": "paragraph", "text": "hello"}],
            content_text="hello",
        )

    def test_new_publication_notifies_follower(self):
        author = self.make_user("Author")
        follower = self.make_user("Follower")
        UserFollow.objects.create(follower=follower, following=author)
        publication = self.make_publication(author)
        event = NotificationEvent.objects.create(
            kind=NotificationEvent.Kind.NEW_PUBLICATION,
            actor=author,
            publication=publication,
        )

        dispatch_notification_event(event)

        notification = Notification.objects.get(recipient=follower)
        self.assertEqual(notification.kind, NotificationEvent.Kind.NEW_PUBLICATION)
        self.assertEqual(notification.publication, publication)

    def test_muted_author_does_not_generate_passive_publication_notification(self):
        author = self.make_user("MutedAuthor")
        follower = self.make_user("QuietFollower")
        UserFollow.objects.create(follower=follower, following=author)
        UserMute.objects.create(muter=follower, muted=author)
        publication = self.make_publication(author)
        event = NotificationEvent.objects.create(
            kind=NotificationEvent.Kind.NEW_PUBLICATION,
            actor=author,
            publication=publication,
        )

        dispatch_notification_event(event)

        self.assertFalse(Notification.objects.filter(recipient=follower).exists())

    def test_preference_can_disable_followed_user_publications(self):
        author = self.make_user("Writer")
        follower = self.make_user("Reader")
        UserFollow.objects.create(follower=follower, following=author)
        NotificationPreference.objects.create(
            user=follower,
            followed_user_publications=False,
        )
        publication = self.make_publication(author)
        event = NotificationEvent.objects.create(
            kind=NotificationEvent.Kind.NEW_PUBLICATION,
            actor=author,
            publication=publication,
        )

        dispatch_notification_event(event)

        self.assertFalse(Notification.objects.filter(recipient=follower).exists())

    def test_mark_all_read_is_idempotent(self):
        author = self.make_user("Actor")
        recipient = self.make_user("Recipient")
        event = NotificationEvent.objects.create(
            kind=NotificationEvent.Kind.NEW_FOLLOWER,
            actor=author,
            target_user=recipient,
        )
        Notification.objects.create(
            event=event,
            recipient=recipient,
            actor=author,
            kind=event.kind,
        )

        self.assertEqual(mark_all_notifications_read(user=recipient), 1)
        self.assertEqual(mark_all_notifications_read(user=recipient), 0)
