from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.communities.models import Community
from apps.publications.models import Publication, Tag
from apps.social.feed import (
    following_feed_queryset,
    personalized_feed_queryset,
    viewer_interest_tag_ids,
)
from apps.social.models import (
    CommunitySubscription,
    PublicationBookmark,
    UserBlock,
    UserFollow,
    UserMute,
)
from apps.users.models import User


class FeedTests(TestCase):
    def setUp(self):
        self.viewer = self._user("viewer")
        self.alice = self._user("alice")
        self.bob = self._user("bob")
        self.carol = self._user("carol")
        self.community = Community.objects.create(
            slug="backend",
            name="Backend",
            description="Backend discussions",
            owner=self.carol,
        )

    def _user(self, nickname):
        return User.objects.create_user(
            nickname=nickname,
            email=f"{nickname}@example.com",
            password="test-pass-12345",
            first_name=nickname.title(),
            last_name="Example",
            country="DE",
            nationality="DE",
        )

    def _publication(self, author, title, *, community=None, tags=(), days_old=0):
        publication = Publication.objects.create(
            author=author,
            community=community,
            kind=Publication.Type.POST,
            title=title,
            content=[{"type": "paragraph", "text": title}],
            content_text=title,
        )
        if tags:
            tag_objects = []
            for name in tags:
                tag, _ = Tag.objects.get_or_create(
                    slug=name.lower(),
                    defaults={"name": name},
                )
                tag_objects.append(tag)
            publication.tags.set(tag_objects)
        if days_old:
            Publication.objects.filter(pk=publication.pk).update(
                created_at=timezone.now() - timedelta(days=days_old)
            )
            publication.refresh_from_db()
        return publication

    def test_following_feed_combines_followed_authors_and_subscribed_communities(self):
        UserFollow.objects.create(follower=self.viewer, following=self.alice)
        CommunitySubscription.objects.create(user=self.viewer, community=self.community)

        followed = self._publication(self.alice, "from alice")
        community = self._publication(self.bob, "from community", community=self.community)
        unrelated = self._publication(self.carol, "unrelated")

        ids = list(following_feed_queryset(self.viewer).values_list("pk", flat=True))

        self.assertIn(followed.pk, ids)
        self.assertIn(community.pk, ids)
        self.assertNotIn(unrelated.pk, ids)

    def test_personalized_feed_prioritizes_explicit_follow(self):
        UserFollow.objects.create(follower=self.viewer, following=self.alice)
        followed = self._publication(self.alice, "older followed", days_old=5)
        fresh = self._publication(self.bob, "fresh unrelated")

        ranked = list(personalized_feed_queryset(self.viewer))
        by_id = {publication.pk: publication for publication in ranked}

        self.assertEqual(ranked[0].pk, followed.pk)
        self.assertTrue(by_id[followed.pk].feed_followed_author)
        self.assertGreater(by_id[followed.pk].feed_score, by_id[fresh.pk].feed_score)

    def test_interest_tags_are_derived_from_bookmarks_and_affect_ranking(self):
        seed = self._publication(self.alice, "python seed", tags=("Python",), days_old=10)
        PublicationBookmark.objects.create(user=self.viewer, publication=seed)

        python_candidate = self._publication(self.bob, "python candidate", tags=("Python",))
        rust_candidate = self._publication(self.carol, "rust candidate", tags=("Rust",))

        interest_ids = viewer_interest_tag_ids(self.viewer)
        ranked = list(
            personalized_feed_queryset(
                self.viewer,
                interest_tag_ids=interest_ids,
            )
        )

        positions = {publication.pk: index for index, publication in enumerate(ranked)}
        self.assertLess(positions[python_candidate.pk], positions[rust_candidate.pk])
        ranked_python = next(item for item in ranked if item.pk == python_candidate.pk)
        self.assertEqual(ranked_python.feed_interest_matches, 1)

    def test_personalized_feed_excludes_muted_and_blocked_authors_in_both_directions(self):
        muted = self._publication(self.alice, "muted")
        blocked_by_viewer = self._publication(self.bob, "blocked by viewer")
        blocked_viewer = self._publication(self.carol, "blocked viewer")
        visible_author = self._user("dave")
        visible = self._publication(visible_author, "visible")

        UserMute.objects.create(muter=self.viewer, muted=self.alice)
        UserBlock.objects.create(blocker=self.viewer, blocked=self.bob)
        UserBlock.objects.create(blocker=self.carol, blocked=self.viewer)

        ids = set(personalized_feed_queryset(self.viewer).values_list("pk", flat=True))

        self.assertNotIn(muted.pk, ids)
        self.assertNotIn(blocked_by_viewer.pk, ids)
        self.assertNotIn(blocked_viewer.pk, ids)
        self.assertIn(visible.pk, ids)

    def test_for_you_endpoint_returns_explanations_and_requires_authentication(self):
        self._publication(self.alice, "fresh discovery")
        client = APIClient()

        anonymous = client.get("/api/v1/feed/for-you/")
        self.assertEqual(anonymous.status_code, 401)

        client.force_authenticate(self.viewer)
        response = client.get("/api/v1/feed/for-you/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("feed_score", response.data["results"][0])
        self.assertTrue(response.data["results"][0]["recommendation_reasons"])
