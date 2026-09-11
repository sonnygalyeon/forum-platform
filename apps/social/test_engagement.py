from django.test import TestCase
from rest_framework.test import APIClient

from apps.discussions.models import Comment
from apps.notifications.models import Notification, NotificationEvent, NotificationPreference
from apps.notifications.services import dispatch_notification_event
from apps.publications.models import Publication, Tag
from apps.social.feed import personalized_feed_queryset, viewer_interest_tag_ids
from apps.social.models import PublicationBookmark, PublicationReaction, UserBlock
from apps.users.models import User


class PublicationEngagementApiTests(TestCase):
    def setUp(self):
        self.author = self._user("author")
        self.viewer = self._user("viewer")
        self.publication = self._publication(self.author, "Main")
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

    def _publication(self, author, title, *, tag=None):
        publication = Publication.objects.create(
            author=author,
            kind=Publication.Type.POST,
            title=title,
            content=[{"type": "paragraph", "text": title}],
            content_text=title,
        )
        if tag is not None:
            publication.tags.add(tag)
        return publication

    def test_engagement_summary_is_public_and_empty_initially(self):
        anonymous = APIClient()
        response = anonymous.get(
            f"/api/v1/publications/{self.publication.public_id}/engagement/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reaction_total"], 0)
        self.assertEqual(response.data["bookmark_count"], 0)
        self.assertEqual(response.data["comment_count"], 0)
        self.assertIsNone(response.data["my_reaction"])
        self.assertFalse(response.data["can_react"])

    def test_one_reaction_per_user_can_change_kind_without_inflating_count(self):
        first = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "heart"},
            format="json",
        )
        second = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "insightful"},
            format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(PublicationReaction.objects.count(), 1)
        reaction = PublicationReaction.objects.get()
        self.assertEqual(reaction.kind, PublicationReaction.Kind.INSIGHTFUL)
        self.assertEqual(second.data["reaction_total"], 1)
        self.assertEqual(second.data["reactions"]["heart"], 0)
        self.assertEqual(second.data["reactions"]["insightful"], 1)
        self.assertEqual(second.data["my_reaction"], "insightful")

    def test_deleting_reaction_removes_signal(self):
        PublicationReaction.objects.create(
            user=self.viewer,
            publication=self.publication,
            kind=PublicationReaction.Kind.USEFUL,
        )

        response = self.client.delete(
            f"/api/v1/publications/{self.publication.public_id}/reaction/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PublicationReaction.objects.count(), 0)
        self.assertEqual(response.data["reaction_total"], 0)
        self.assertIsNone(response.data["my_reaction"])

    def test_author_cannot_react_to_own_publication(self):
        self.client.force_authenticate(self.author)
        response = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "heart"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PublicationReaction.objects.count(), 0)

    def test_block_in_either_direction_prevents_reaction(self):
        UserBlock.objects.create(blocker=self.author, blocked=self.viewer)

        response = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "curious"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PublicationReaction.objects.count(), 0)

    def test_summary_combines_reactions_bookmarks_and_comments(self):
        other = self._user("other")
        PublicationReaction.objects.create(
            user=self.viewer,
            publication=self.publication,
            kind=PublicationReaction.Kind.HEART,
        )
        PublicationReaction.objects.create(
            user=other,
            publication=self.publication,
            kind=PublicationReaction.Kind.USEFUL,
        )
        PublicationBookmark.objects.create(
            user=self.viewer,
            publication=self.publication,
        )
        Comment.objects.create(
            publication=self.publication,
            author=self.viewer,
            kind=Comment.Kind.COMMENT,
            content=[{"type": "paragraph", "text": "Useful"}],
            content_text="Useful",
        )

        response = self.client.get(
            f"/api/v1/publications/{self.publication.public_id}/engagement/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reaction_total"], 2)
        self.assertEqual(response.data["bookmark_count"], 1)
        self.assertEqual(response.data["comment_count"], 1)
        self.assertEqual(response.data["engagement_score"], 9)

    def test_reaction_creates_single_durable_notification_event_on_kind_change(self):
        first = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "heart"},
            format="json",
        )
        second = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "useful"},
            format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        events = NotificationEvent.objects.filter(
            kind=NotificationEvent.Kind.PUBLICATION_REACTION,
            actor=self.viewer,
            publication=self.publication,
        )
        self.assertEqual(events.count(), 1)

    def test_reaction_notification_is_center_only_for_legacy_compatibility(self):
        response = self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "heart"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        event = NotificationEvent.objects.get(
            kind=NotificationEvent.Kind.PUBLICATION_REACTION,
            actor=self.viewer,
            publication=self.publication,
        )
        dispatch_notification_event(event)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.author,
                kind=NotificationEvent.Kind.PUBLICATION_REACTION,
            ).count(),
            1,
        )

        author_client = APIClient()
        author_client.force_authenticate(self.author)
        legacy = author_client.get("/api/v1/notifications/")
        center = author_client.get("/api/v1/notifications/center/")
        legacy_count = author_client.get("/api/v1/notifications/unread-count/")
        center_count = author_client.get("/api/v1/notifications/center/unread-count/")

        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(center.status_code, 200)
        self.assertEqual(legacy.data["results"], [])
        self.assertEqual(center.data["results"][0]["kind"], "publication_reaction")
        self.assertEqual(legacy_count.data["unread_count"], 0)
        self.assertEqual(center_count.data["unread_count"], 1)

    def test_reaction_notification_preference_can_disable_delivery(self):
        NotificationPreference.objects.create(
            user=self.author,
            publication_reactions=False,
        )
        self.client.put(
            f"/api/v1/publications/{self.publication.public_id}/reaction/",
            {"kind": "heart"},
            format="json",
        )
        event = NotificationEvent.objects.get(
            kind=NotificationEvent.Kind.PUBLICATION_REACTION,
            actor=self.viewer,
            publication=self.publication,
        )

        created = dispatch_notification_event(event)

        self.assertEqual(created, 0)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.author,
                kind=NotificationEvent.Kind.PUBLICATION_REACTION,
            ).exists()
        )

    def test_reactions_affect_feed_score_but_remain_capped_signal(self):
        popular_author = self._user("popular")
        quiet_author = self._user("quiet")
        popular = self._publication(popular_author, "Popular")
        quiet = self._publication(quiet_author, "Quiet")

        for index in range(6):
            reactor = self._user(f"reactor{index}")
            PublicationReaction.objects.create(
                user=reactor,
                publication=popular,
                kind=PublicationReaction.Kind.HEART,
            )

        ranked = list(personalized_feed_queryset(self.viewer))
        by_id = {item.pk: item for item in ranked}

        self.assertGreater(
            by_id[popular.pk].feed_score,
            by_id[quiet.pk].feed_score,
        )
        self.assertEqual(by_id[popular.pk].feed_reaction_count, 6)

    def test_my_reaction_contributes_to_interest_tags(self):
        python = Tag.objects.create(name="Python", slug="engagement-python")
        seed = self._publication(self.author, "Seed", tag=python)
        PublicationReaction.objects.create(
            user=self.viewer,
            publication=seed,
            kind=PublicationReaction.Kind.INSIGHTFUL,
        )

        interest_ids = viewer_interest_tag_ids(self.viewer)

        self.assertIn(python.pk, interest_ids)
