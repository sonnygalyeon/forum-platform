from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.publications.models import Publication, Tag
from apps.social.feed_quality import quality_reranked_feed
from apps.social.models import FeedFeedback, UserFollow
from apps.users.models import User


class FeedQualityTests(TestCase):
    def setUp(self):
        self.viewer = self._user("viewer")
        self.alice = self._user("alice")
        self.bob = self._user("bob")
        self.carol = self._user("carol")
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

    def _publication(self, author, title, *, tags=(), days_old=0):
        publication = Publication.objects.create(
            author=author,
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

    def test_feedback_api_is_reversible(self):
        publication = self._publication(self.alice, "Hide me")
        endpoint = f"/api/v1/publications/{publication.public_id}/feed-feedback/"

        initial = self.client.get(endpoint)
        created = self.client.put(
            endpoint,
            {"reason": "not_interested"},
            format="json",
        )
        stored = self.client.get(endpoint)
        removed = self.client.delete(endpoint)

        self.assertEqual(initial.status_code, 200)
        self.assertIsNone(initial.data["reason"])
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.data["reason"], "not_interested")
        self.assertEqual(stored.data["reason"], "not_interested")
        self.assertEqual(removed.data["reason"], None)
        self.assertFalse(
            FeedFeedback.objects.filter(
                user=self.viewer,
                publication=publication,
            ).exists()
        )

    def test_feedback_rejects_own_publication(self):
        publication = self._publication(self.viewer, "Mine")

        response = self.client.put(
            f"/api/v1/publications/{publication.public_id}/feed-feedback/",
            {"reason": "already_seen"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(FeedFeedback.objects.exists())

    def test_feedback_suppresses_exact_item_from_for_you(self):
        hidden = self._publication(self.alice, "Hidden")
        visible = self._publication(self.bob, "Visible")
        FeedFeedback.objects.create(
            user=self.viewer,
            publication=hidden,
            reason=FeedFeedback.Reason.ALREADY_SEEN,
        )

        ranked = quality_reranked_feed(self.viewer)
        ids = {publication.pk for publication in ranked}

        self.assertNotIn(hidden.pk, ids)
        self.assertIn(visible.pk, ids)

    def test_not_interested_penalizes_matching_tags_only(self):
        seed = self._publication(self.alice, "Python seed", tags=("Python",))
        FeedFeedback.objects.create(
            user=self.viewer,
            publication=seed,
            reason=FeedFeedback.Reason.NOT_INTERESTED,
        )
        matching = self._publication(self.bob, "Python again", tags=("Python",))
        unrelated = self._publication(self.carol, "Rust", tags=("Rust",))

        ranked = quality_reranked_feed(self.viewer)
        by_id = {publication.pk: publication for publication in ranked}

        self.assertGreater(by_id[matching.pk].feed_negative_feedback_penalty, 0)
        self.assertEqual(by_id[unrelated.pk].feed_negative_feedback_penalty, 0)

    def test_too_repetitive_penalizes_same_author(self):
        seed = self._publication(self.alice, "Alice seed")
        FeedFeedback.objects.create(
            user=self.viewer,
            publication=seed,
            reason=FeedFeedback.Reason.TOO_REPETITIVE,
        )
        repeated = self._publication(self.alice, "Alice again")
        other = self._publication(self.bob, "Bob")

        ranked = quality_reranked_feed(self.viewer)
        by_id = {publication.pk: publication for publication in ranked}

        self.assertGreater(by_id[repeated.pk].feed_negative_feedback_penalty, 0)
        self.assertEqual(by_id[other.pk].feed_negative_feedback_penalty, 0)

    def test_diversity_reranker_breaks_same_author_run(self):
        self._publication(self.alice, "Alice 1")
        self._publication(self.alice, "Alice 2")
        self._publication(self.alice, "Alice 3")
        self._publication(self.bob, "Bob 1")

        ranked = quality_reranked_feed(self.viewer)

        self.assertGreaterEqual(len(ranked), 4)
        self.assertEqual(
            len({ranked[0].author_id, ranked[1].author_id}),
            2,
        )
        alice_rows = [item for item in ranked if item.author_id == self.alice.pk]
        self.assertTrue(
            any(item.feed_diversity_penalty > 0 for item in alice_rows[1:])
        )

    def test_stale_content_gets_quality_penalty(self):
        old = self._publication(self.alice, "Old", days_old=45)
        fresh = self._publication(self.bob, "Fresh")

        ranked = quality_reranked_feed(self.viewer)
        by_id = {publication.pk: publication for publication in ranked}

        self.assertEqual(by_id[old.pk].feed_stale_penalty, 12)
        self.assertEqual(by_id[fresh.pk].feed_stale_penalty, 0)
        self.assertLess(
            by_id[old.pk].feed_score,
            by_id[old.pk].feed_base_score,
        )

    def test_explicit_relationship_is_not_marked_as_exploration(self):
        UserFollow.objects.create(follower=self.viewer, following=self.alice)
        explicit = self._publication(self.alice, "Followed")
        discovery = self._publication(self.bob, "Discovery")

        ranked = quality_reranked_feed(self.viewer)
        by_id = {publication.pk: publication for publication in ranked}

        self.assertFalse(by_id[explicit.pk].feed_is_exploration)
        self.assertTrue(by_id[discovery.pk].feed_is_exploration)

    def test_for_you_contract_exposes_quality_fields_without_count(self):
        self._publication(self.alice, "One")

        response = self.client.get("/api/v1/feed/for-you/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("count", response.data)
        self.assertEqual(set(response.data.keys()), {"next", "previous", "results"})
        item = response.data["results"][0]
        self.assertIn("feed_score", item)
        self.assertIn("feed_base_score", item)
        self.assertIn("reaction_total", item)
        self.assertIn("is_exploration", item)
        self.assertIn("quality_adjustments", item)
        self.assertTrue(item["recommendation_reasons"])

    def test_quality_feed_cursor_pages_without_duplicates(self):
        for index in range(5):
            author = self._user(f"author{index}")
            self._publication(author, f"Post {index}")

        first = self.client.get("/api/v1/feed/for-you/?page_size=2")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data["results"]), 2)
        self.assertIsNotNone(first.data["next"])

        parsed = urlparse(first.data["next"])
        query = parse_qs(parsed.query)
        cursor = query["cursor"][0]
        second = self.client.get(
            "/api/v1/feed/for-you/",
            {"page_size": 2, "cursor": cursor},
        )

        self.assertEqual(second.status_code, 200)
        first_ids = {item["id"] for item in first.data["results"]}
        second_ids = {item["id"] for item in second.data["results"]}
        self.assertFalse(first_ids & second_ids)
        self.assertIsNotNone(second.data["previous"])

    def test_invalid_quality_feed_cursor_returns_404(self):
        self._publication(self.alice, "One")

        response = self.client.get(
            "/api/v1/feed/for-you/",
            {"cursor": "definitely-not-a-feed-cursor"},
        )

        self.assertEqual(response.status_code, 404)
