from django.test import TestCase
from rest_framework.test import APIClient

from apps.communities.models import Community
from apps.discussions.models import Comment
from apps.publications.models import Publication, Tag
from apps.social.models import CommunitySubscription, UserBlock, UserFollow, UserMute
from apps.users.models import User


class CommunityActivityApiTests(TestCase):
    def setUp(self):
        self.viewer = self._user("viewer")
        self.owner = self._user("owner")
        self.community = Community.objects.create(
            slug="night-lab",
            name="Night Lab",
            description="Community activity tests",
            owner=self.owner,
        )
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

    def _publication(self, author, *, community=None, tag=None, title=None):
        publication = Publication.objects.create(
            author=author,
            community=community,
            kind=Publication.Type.POST,
            title=title or f"Post by {author.nickname}",
            content=[{"type": "paragraph", "text": "Community activity test"}],
            content_text="Community activity test",
        )
        if tag is not None:
            publication.tags.add(tag)
        return publication

    def _comment(self, author, publication, *, accepted=False):
        return Comment.objects.create(
            publication=publication,
            author=author,
            kind=Comment.Kind.ANSWER if accepted else Comment.Kind.COMMENT,
            content=[{"type": "paragraph", "text": "Useful reply"}],
            content_text="Useful reply",
            is_accepted=accepted,
        )

    def test_activity_summary_counts_real_community_events(self):
        author = self._user("author")
        publication = self._publication(author, community=self.community)
        self._comment(self.viewer, publication)
        CommunitySubscription.objects.create(user=self.viewer, community=self.community)

        response = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/activity/summary/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["publications_7d"], 1)
        self.assertEqual(response.data["comments_7d"], 1)
        self.assertEqual(response.data["new_subscribers_7d"], 1)
        self.assertEqual(response.data["active_contributors_7d"], 2)
        self.assertGreater(response.data["activity_score"], 0)

    def test_activity_summary_exposes_top_tags(self):
        tag = Tag.objects.create(name="Python", slug="community-python")
        publication = self._publication(
            self.owner,
            community=self.community,
            tag=tag,
        )
        self.assertIsNotNone(publication.pk)

        response = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/activity/summary/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["top_tags"][0]["name"], "Python")
        self.assertEqual(response.data["top_tags"][0]["publication_count"], 1)

    def test_timeline_contains_publications_and_comments(self):
        publication = self._publication(self.owner, community=self.community)
        comment = self._comment(self.viewer, publication)

        response = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/activity/"
        )

        self.assertEqual(response.status_code, 200)
        kinds = {item["type"] for item in response.data["results"]}
        ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(kinds, {"publication", "comment"})
        self.assertIn(str(publication.public_id), ids)
        self.assertIn(str(comment.public_id), ids)

    def test_contributors_rank_publication_and_accepted_answer_activity(self):
        author = self._user("contributor")
        publication = self._publication(author, community=self.community)
        topic = Publication.objects.create(
            author=self.owner,
            community=self.community,
            kind=Publication.Type.TOPIC,
            title="Question",
            content=[{"type": "paragraph", "text": "Question"}],
            content_text="Question",
        )
        self._comment(author, topic, accepted=True)

        response = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/contributors/"
        )

        self.assertEqual(response.status_code, 200)
        row = next(
            item
            for item in response.data["results"]
            if item["user"]["id"] == str(author.public_id)
        )
        self.assertEqual(row["publication_count"], 1)
        self.assertEqual(row["accepted_answer_count"], 1)
        self.assertGreaterEqual(row["activity_score"], 10)
        self.assertIsNotNone(publication.pk)

    def test_muted_and_blocked_people_are_hidden_from_identity_surfaces(self):
        muted = self._user("muted")
        blocked = self._user("blocked")
        visible = self._user("visible")
        self._publication(muted, community=self.community)
        self._publication(blocked, community=self.community)
        self._publication(visible, community=self.community)
        UserMute.objects.create(muter=self.viewer, muted=muted)
        UserBlock.objects.create(blocker=blocked, blocked=self.viewer)

        timeline = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/activity/"
        )
        contributors = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/contributors/"
        )

        timeline_actors = {
            item["actor"]["id"] for item in timeline.data["results"]
        }
        contributor_ids = {
            item["user"]["id"] for item in contributors.data["results"]
        }
        self.assertNotIn(str(muted.public_id), timeline_actors)
        self.assertNotIn(str(blocked.public_id), timeline_actors)
        self.assertNotIn(str(muted.public_id), contributor_ids)
        self.assertNotIn(str(blocked.public_id), contributor_ids)
        self.assertIn(str(visible.public_id), timeline_actors)
        self.assertIn(str(visible.public_id), contributor_ids)

    def test_recommendations_use_social_and_interest_signals(self):
        followed = self._user("followed")
        candidate_owner = self._user("candidate-owner")
        candidate = Community.objects.create(
            slug="python-lab",
            name="Python Lab",
            description="Python",
            owner=candidate_owner,
        )
        tag = Tag.objects.create(name="Python", slug="python-recommendation")
        self._publication(self.viewer, tag=tag)
        candidate_publication = self._publication(
            candidate_owner,
            community=candidate,
            tag=tag,
        )
        self._comment(followed, candidate_publication)
        UserFollow.objects.create(follower=self.viewer, following=followed)
        CommunitySubscription.objects.create(user=followed, community=candidate)

        response = self.client.get("/api/v1/community-recommendations/")

        self.assertEqual(response.status_code, 200)
        row = next(
            item
            for item in response.data["results"]
            if item["community"]["id"] == str(candidate.public_id)
        )
        self.assertGreaterEqual(row["followed_member_count"], 1)
        self.assertGreaterEqual(row["matching_tag_count"], 1)
        self.assertGreater(row["recommendation_score"], 0)
        reason_codes = {
            reason["code"] for reason in row["recommendation_reasons"]
        }
        self.assertIn("followed_people", reason_codes)
        self.assertIn("matching_interests", reason_codes)

    def test_recommendations_exclude_subscribed_and_hidden_owner_communities(self):
        subscribed_owner = self._user("subscribed-owner")
        blocked_owner = self._user("blocked-owner")
        muted_owner = self._user("muted-owner")
        visible_owner = self._user("visible-owner")
        subscribed = Community.objects.create(
            slug="already-here",
            name="Already Here",
            owner=subscribed_owner,
        )
        blocked = Community.objects.create(
            slug="blocked-community",
            name="Blocked Community",
            owner=blocked_owner,
        )
        muted = Community.objects.create(
            slug="muted-community",
            name="Muted Community",
            owner=muted_owner,
        )
        visible = Community.objects.create(
            slug="visible-community",
            name="Visible Community",
            owner=visible_owner,
        )
        CommunitySubscription.objects.create(user=self.viewer, community=subscribed)
        UserBlock.objects.create(blocker=self.viewer, blocked=blocked_owner)
        UserMute.objects.create(muter=self.viewer, muted=muted_owner)

        response = self.client.get("/api/v1/community-recommendations/")

        self.assertEqual(response.status_code, 200)
        ids = {
            item["community"]["id"] for item in response.data["results"]
        }
        self.assertNotIn(str(subscribed.public_id), ids)
        self.assertNotIn(str(blocked.public_id), ids)
        self.assertNotIn(str(muted.public_id), ids)
        self.assertIn(str(visible.public_id), ids)

    def test_legacy_community_detail_contract_has_no_activity_fields(self):
        response = self.client.get(
            f"/api/v1/communities/{self.community.public_id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("activity_score", response.data)
        self.assertNotIn("publications_7d", response.data)
        self.assertNotIn("active_contributors_7d", response.data)
