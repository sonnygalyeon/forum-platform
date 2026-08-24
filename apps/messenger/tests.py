from django.test import TestCase, override_settings

from apps.messenger.models import ConversationMember, MessageReaction
from apps.messenger.presence import is_online, set_offline, set_online
from apps.messenger.services import (
    clear_reaction,
    create_direct_conversation,
    create_message,
    pin_message,
    set_reaction,
    update_conversation_settings,
)
from apps.users.models import User


TEST_CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}
TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS, CACHES=TEST_CACHES)
class MessengerPolishTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            nickname="messenger_alice",
            email="messenger-alice@example.com",
            password="test-pass-12345",
            country="DE",
            nationality="DE",
        )
        self.bob = User.objects.create_user(
            nickname="messenger_bob",
            email="messenger-bob@example.com",
            password="test-pass-12345",
            country="DE",
            nationality="DE",
        )
        self.conversation, _ = create_direct_conversation(
            creator=self.alice,
            other_user=self.bob,
        )
        self.message, _ = create_message(
            conversation=self.conversation,
            sender=self.alice,
            text="hello",
            client_id="4b0f3986-d03a-4f29-92de-39f97caa36a1",
        )

    def test_reactions_toggle_independently_by_emoji(self):
        set_reaction(message=self.message, user=self.bob, emoji="👍")
        set_reaction(message=self.message, user=self.bob, emoji="🔥")
        self.assertEqual(MessageReaction.objects.filter(message=self.message, user=self.bob).count(), 2)

        clear_reaction(message=self.message, user=self.bob, emoji="👍")
        self.assertFalse(MessageReaction.objects.filter(message=self.message, user=self.bob, emoji="👍").exists())
        self.assertTrue(MessageReaction.objects.filter(message=self.message, user=self.bob, emoji="🔥").exists())

    def test_appearance_is_private_to_membership(self):
        update_conversation_settings(
            conversation=self.conversation,
            user=self.alice,
            chat_theme="violet",
            wallpaper="aurora",
            wallpaper_dim=33,
            wallpaper_blur=True,
            message_scale="large",
        )
        alice_membership = ConversationMember.objects.get(conversation=self.conversation, user=self.alice)
        bob_membership = ConversationMember.objects.get(conversation=self.conversation, user=self.bob)
        self.assertEqual(alice_membership.chat_theme, "violet")
        self.assertEqual(alice_membership.wallpaper, "aurora")
        self.assertEqual(alice_membership.wallpaper_dim, 33)
        self.assertTrue(alice_membership.wallpaper_blur)
        self.assertEqual(alice_membership.message_scale, "large")
        self.assertEqual(bob_membership.chat_theme, "iris")

    def test_direct_chat_member_can_pin_and_unpin(self):
        pin_message(conversation=self.conversation, actor=self.bob, message=self.message)
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.pinned_message_id, self.message.pk)

        pin_message(conversation=self.conversation, actor=self.alice, message=None)
        self.conversation.refresh_from_db()
        self.assertIsNone(self.conversation.pinned_message_id)

    def test_presence_stays_online_until_final_connection_closes(self):
        self.assertTrue(set_online(self.alice))
        self.assertFalse(set_online(self.alice))
        self.assertTrue(is_online(self.alice))

        self.assertFalse(set_offline(self.alice))
        self.assertTrue(is_online(self.alice))

        self.assertTrue(set_offline(self.alice))
        self.assertFalse(is_online(self.alice))
