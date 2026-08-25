from django.test import TestCase, override_settings

from apps.messenger.models import (
    ConversationMember,
    MessageEdit,
    MessageHiddenForUser,
    MessageReaction,
    MessageReceipt,
    MessengerEventRecipient,
)
from apps.messenger.presence import is_online, set_offline, set_online
from apps.messenger.selectors import messages_for_conversation, messenger_events_for_user
from apps.messenger.services import (
    can_message_user,
    clear_reaction,
    create_direct_conversation,
    create_message,
    edit_message,
    forward_message,
    hide_message_for_user,
    mark_delivered,
    mark_read,
    pin_message,
    save_draft,
    set_reaction,
    update_conversation_settings,
    update_messenger_settings,
)
from apps.social.models import UserFollow
from apps.users.models import User

TEST_CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
TEST_CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS, CACHES=TEST_CACHES)
class MessengerCoreV2Tests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            nickname="messenger_alice", email="messenger-alice@example.com", password="test-pass-12345", country="DE", nationality="DE"
        )
        self.bob = User.objects.create_user(
            nickname="messenger_bob", email="messenger-bob@example.com", password="test-pass-12345", country="DE", nationality="DE"
        )
        self.charlie = User.objects.create_user(
            nickname="messenger_charlie", email="messenger-charlie@example.com", password="test-pass-12345", country="DE", nationality="DE"
        )
        self.conversation, _ = create_direct_conversation(creator=self.alice, other_user=self.bob)
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

    def test_appearance_and_pin_are_private_to_membership(self):
        update_conversation_settings(
            conversation=self.conversation, user=self.alice, chat_theme="violet", wallpaper="aurora",
            wallpaper_dim=33, wallpaper_blur=True, message_scale="large", is_pinned=True,
        )
        alice = ConversationMember.objects.get(conversation=self.conversation, user=self.alice)
        bob = ConversationMember.objects.get(conversation=self.conversation, user=self.bob)
        self.assertEqual(alice.chat_theme, "violet")
        self.assertTrue(alice.is_pinned)
        self.assertFalse(bob.is_pinned)

    def test_direct_chat_member_can_pin_and_unpin_message(self):
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

    def test_delivery_and_read_receipts_are_persistent(self):
        receipt = MessageReceipt.objects.get(message=self.message, user=self.bob)
        self.assertIsNone(receipt.delivered_at)
        mark_delivered(conversation=self.conversation, user=self.bob)
        receipt.refresh_from_db()
        self.assertIsNotNone(receipt.delivered_at)
        self.assertIsNone(receipt.read_at)
        mark_read(conversation=self.conversation, user=self.bob, message=self.message)
        receipt.refresh_from_db()
        self.assertIsNotNone(receipt.read_at)

    def test_edit_history_keeps_previous_text(self):
        edit_message(message=self.message, actor=self.alice, text="hello edited")
        row = MessageEdit.objects.get(message=self.message)
        self.assertEqual(row.previous_text, "hello")
        self.message.refresh_from_db()
        self.assertEqual(self.message.text, "hello edited")

    def test_delete_for_me_does_not_delete_for_other_member(self):
        hide_message_for_user(message=self.message, user=self.bob)
        self.assertTrue(MessageHiddenForUser.objects.filter(message=self.message, user=self.bob).exists())
        self.assertFalse(messages_for_conversation(self.conversation, user=self.bob).filter(pk=self.message.pk).exists())
        self.assertTrue(messages_for_conversation(self.conversation, user=self.alice).filter(pk=self.message.pk).exists())

    def test_server_draft_is_per_member(self):
        save_draft(conversation=self.conversation, user=self.alice, text="unfinished")
        alice = ConversationMember.objects.get(conversation=self.conversation, user=self.alice)
        bob = ConversationMember.objects.get(conversation=self.conversation, user=self.bob)
        self.assertEqual(alice.draft_text, "unfinished")
        self.assertEqual(bob.draft_text, "")

    def test_forward_keeps_source_reference_and_attachments_contract(self):
        target, _ = create_direct_conversation(creator=self.alice, other_user=self.charlie)
        forwarded, created = forward_message(
            message=self.message,
            actor=self.alice,
            target_conversation=target,
            client_id="5795780d-ad6c-4b59-92eb-651767edaa10",
        )
        self.assertTrue(created)
        self.assertEqual(forwarded.forwarded_from_id, self.message.pk)
        self.assertEqual(forwarded.text, self.message.text)

    def test_privacy_following_restricts_new_direct_chats(self):
        update_messenger_settings(user=self.charlie, who_can_message="following")
        self.assertFalse(can_message_user(actor=self.alice, target=self.charlie))
        UserFollow.objects.create(follower=self.charlie, following=self.alice)
        self.assertTrue(can_message_user(actor=self.alice, target=self.charlie))

    def test_existing_direct_chat_can_be_reopened_after_privacy_changes(self):
        update_messenger_settings(user=self.bob, who_can_message="nobody")
        reopened, created = create_direct_conversation(creator=self.alice, other_user=self.bob)
        self.assertFalse(created)
        self.assertEqual(reopened.pk, self.conversation.pk)

    def test_durable_event_log_can_resync_user(self):
        create_message(
            conversation=self.conversation,
            sender=self.bob,
            text="offline event",
            client_id="6fd84489-77a5-4f12-b2c9-3f18a252371e",
        )
        self.assertTrue(MessengerEventRecipient.objects.filter(user=self.alice).exists())
        edges = list(messenger_events_for_user(self.alice, after_id=0, limit=200))
        self.assertTrue(any(edge.event.event_type == "message.created" for edge in edges))
