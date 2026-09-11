from django.test import TestCase
from rest_framework.test import APIClient

from apps.communities.models import Community
from apps.publications.models import Publication, Tag
from apps.social.models import CommunitySubscription, UserBlock, UserFollow, UserMute
from apps.users.models import User


class SocialGraphApiTests(TestCase):
    def setUp(self):
        self.viewer = self._user("viewer")
        self.target = self._user("target")
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

    def _publication(self, author, *, tag=None):
        publication = Publication.objects.create(
            author=author,
            kind=Publication.Type.POST,
            title=f"Post by {author.nickname}",
            content=[{"type": "paragraph", "text": "Graph test"}],
            content_text="Graph test",
        )
        if tag is not None:
            publication.tags.add(tag)
        return publication

    def test_relationship_summary_exposes_mutual_context(self):
        common = self._user("common")
        UserFollow.objects.create(follower=self.viewer, following=self.target)
        UserFollow.objects.create(follower=self.target, following=self.viewer)
        UserFollow.objects.create(follower=self.viewer, following=common)
        UserFollow.objects.create(follower=self.target, following=common)

        community = Community.objects.create(
            slug="graph-lab",
            name="Graph Lab",
            description="Shared community",
            owner=self.viewer,
        )
        CommunitySubscription.objects.create(user=self.viewer, community=community)
        CommunitySubscription.objects.create(user=self.target, community=community)

        tag = Tag.objects.create(name="Python", slug="python-graph-test")
        self._publication(self.viewer, tag=tag)
        self._publication(self.target, tag=tag)

        response = self.client.get(
            f"/api/v1/social/users/{self.target.public_id}/summary/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_following"])
        self.assertTrue(response.data["follows_you"])
        self.assertTrue(response.data["is_mutual"])
        self.assertTrue(response.data["can_follow"])
        self.assertEqual(response.data["mutual_count"], 1)
        self.assertEqual(response.data["shared_community_count"], 1)
        self.assertEqual(response.data["shared_tag_count"], 1)

    def test_recommendations_are_explainable_and_filter_follow_block_mute(self):
        common = self._user("common")
        related = self._user("related")
        already_followed = self._user("followed")
        blocked = self._user("blocked")
        muted = self._user("muted")

        UserFollow.objects.create(follower=self.viewer, following=common)
        UserFollow.objects.create(follower=related, following=common)
        UserFollow.objects.create(follower=related, following=self.viewer)
        UserFollow.objects.create(follower=self.viewer, following=already_followed)
        UserBlock.objects.create(blocker=self.viewer, blocked=blocked)
        UserMute.objects.create(muter=self.viewer, muted=muted)

        response = self.client.get("/api/v1/social/recommendations/")

        self.assertEqual(response.status_code, 200)
        by_id = {item["user"]["id"]: item for item in response.data["results"]}
        self.assertIn(str(related.public_id), by_id)
        self.assertNotIn(str(already_followed.public_id), by_id)
        self.assertNotIn(str(blocked.public_id), by_id)
        self.assertNotIn(str(muted.public_id), by_id)

        item = by_id[str(related.public_id)]
        self.assertGreaterEqual(item["recommendation_score"], 42)
        codes = {reason["code"] for reason in item["recommendation_reasons"]}
        self.assertIn("mutual_connections", codes)
        self.assertIn("follows_you", codes)

    def test_graph_followers_hide_users_blocked_relative_to_viewer(self):
        visible = self._user("visible")
        hidden = self._user("hidden")
        UserFollow.objects.create(follower=visible, following=self.target)
        UserFollow.objects.create(follower=hidden, following=self.target)
        UserBlock.objects.create(blocker=hidden, blocked=self.viewer)

        response = self.client.get(
            f"/api/v1/social/users/{self.target.public_id}/followers/"
        )

        self.assertEqual(response.status_code, 200)
        ids = {item["user"]["id"] for item in response.data["results"]}
        self.assertIn(str(visible.public_id), ids)
        self.assertNotIn(str(hidden.public_id), ids)

    def test_mutuals_returns_accounts_both_users_follow(self):
        common = self._user("common")
        only_viewer = self._user("onlyviewer")
        UserFollow.objects.create(follower=self.viewer, following=common)
        UserFollow.objects.create(follower=self.target, following=common)
        UserFollow.objects.create(follower=self.viewer, following=only_viewer)

        response = self.client.get(
            f"/api/v1/social/users/{self.target.public_id}/mutuals/"
        )

        self.assertEqual(response.status_code, 200)
        ids = {item["user"]["id"] for item in response.data["results"]}
        self.assertEqual(ids, {str(common.public_id)})

    def test_block_between_viewer_and_target_hides_graph_lists(self):
        UserBlock.objects.create(blocker=self.target, blocked=self.viewer)

        response = self.client.get(
            f"/api/v1/social/users/{self.target.public_id}/followers/"
        )

        self.assertEqual(response.status_code, 404)

    def test_legacy_followers_contract_remains_unchanged(self):
        follower = self._user("legacy")
        UserFollow.objects.create(follower=follower, following=self.target)

        response = self.client.get(
            f"/api/v1/users/{self.target.public_id}/followers/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data["results"][0].keys()),
            {"user", "followed_at"},
        )
