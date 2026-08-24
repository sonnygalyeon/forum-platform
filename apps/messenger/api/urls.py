from django.urls import path

from apps.messenger.api.views import (
    ConversationDetailView,
    ConversationListView,
    ConversationMessagesView,
    ConversationReadView,
    ConversationPinnedMessageView,
    DirectConversationCreateView,
    GroupConversationCreateView,
    GroupMemberView,
    MessageDetailView,
    MessageReactionView,
    MessengerUnreadCountView,
    MessengerUserSearchView,
    WSTicketView,
)

urlpatterns = [
    path("messenger/conversations/", ConversationListView.as_view(), name="messenger-conversations"),
    path("messenger/conversations/direct/", DirectConversationCreateView.as_view(), name="messenger-direct-create"),
    path("messenger/conversations/groups/", GroupConversationCreateView.as_view(), name="messenger-group-create"),
    path("messenger/conversations/<uuid:conversation_id>/", ConversationDetailView.as_view(), name="messenger-conversation-detail"),
    path("messenger/conversations/<uuid:conversation_id>/messages/", ConversationMessagesView.as_view(), name="messenger-messages"),
    path("messenger/conversations/<uuid:conversation_id>/read/", ConversationReadView.as_view(), name="messenger-read"),
    path("messenger/conversations/<uuid:conversation_id>/pinned/", ConversationPinnedMessageView.as_view(), name="messenger-pinned"),
    path("messenger/conversations/<uuid:conversation_id>/members/", GroupMemberView.as_view(), name="messenger-members"),
    path("messenger/conversations/<uuid:conversation_id>/members/<uuid:user_id>/", GroupMemberView.as_view(), name="messenger-member-detail"),
    path("messenger/messages/<uuid:message_id>/", MessageDetailView.as_view(), name="messenger-message-detail"),
    path("messenger/messages/<uuid:message_id>/reaction/", MessageReactionView.as_view(), name="messenger-message-reaction"),
    path("messenger/unread-count/", MessengerUnreadCountView.as_view(), name="messenger-unread-count"),
    path("messenger/users/", MessengerUserSearchView.as_view(), name="messenger-user-search"),
    path("messenger/ws-ticket/", WSTicketView.as_view(), name="messenger-ws-ticket"),
]
