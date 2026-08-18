from django.test import TestCase

from apps.social.models import UserBlock, UserFollow, UserMute
from apps.social.services import (
    block_user,
    follow_user,
    mute_user,
    users_have_block_between,
)
from apps.users.models import User


class UserRelationshipTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            nickname="Alice",
            email="alice@example.com",
            password="test-pass-12345",
            first_name="Alice",
            last_name="Example",
            country="DE",
            nationality="DE",
        )
        self.bob = User.objects.create_user(
            nickname="Bob",
            email="bob@example.com",
            password="test-pass-12345",
            first_name="Bob",
            last_name="Example",
            country="DE",
            nationality="DE",
        )

    def test_block_is_idempotent_and_removes_follows_both_directions(self):
        UserFollow.objects.create(follower=self.alice, following=self.bob)
        UserFollow.objects.create(follower=self.bob, following=self.alice)

        edge, created = block_user(blocker=self.alice, blocked=self.bob)
        self.assertTrue(created)
        self.assertEqual(edge.blocker, self.alice)
        self.assertFalse(UserFollow.objects.exists())

        _, created_again = block_user(blocker=self.alice, blocked=self.bob)
        self.assertFalse(created_again)
        self.assertEqual(UserBlock.objects.count(), 1)

    def test_block_prevents_follow_in_either_direction(self):
        block_user(blocker=self.alice, blocked=self.bob)
        self.assertTrue(users_have_block_between(self.alice, self.bob))

        with self.assertRaises(ValueError):
            follow_user(follower=self.alice, following=self.bob)

        with self.assertRaises(ValueError):
            follow_user(follower=self.bob, following=self.alice)

    def test_mute_does_not_prevent_follow(self):
        edge, created = mute_user(muter=self.alice, muted=self.bob)
        self.assertTrue(created)
        self.assertEqual(edge.muter, self.alice)
        self.assertTrue(UserMute.objects.filter(muter=self.alice, muted=self.bob).exists())

        _, follow_created = follow_user(follower=self.alice, following=self.bob)
        self.assertTrue(follow_created)

    def test_block_removes_same_direction_mute(self):
        mute_user(muter=self.alice, muted=self.bob)
        block_user(blocker=self.alice, blocked=self.bob)
        self.assertFalse(UserMute.objects.filter(muter=self.alice, muted=self.bob).exists())
