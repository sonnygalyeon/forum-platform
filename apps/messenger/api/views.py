import uuid

from django.core import signing
from django.core.cache import cache
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messenger.api.serializers import (
    ConversationSerializer,
    ConversationUpdateSerializer,
    DirectConversationCreateSerializer,
    GroupConversationCreateSerializer,
    GroupMemberSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    MessageUpdateSerializer,
    ReactionSerializer,
    ReadSerializer,
    PinnedMessageSerializer,
    WSTicketSerializer,
)
from apps.messenger.models import Conversation, Message
from apps.messenger.selectors import blocked_user_ids_for, conversation_for_user, conversations_for_user, messages_for_conversation
from apps.messenger.services import (
    add_group_member,
    clear_reaction,
    create_direct_conversation,
    create_group_conversation,
    create_message,
    delete_message,
    edit_message,
    mark_read,
    remove_group_member,
    set_reaction,
    update_conversation_settings,
    pin_message,
)
from apps.social.models import UserBlock
from apps.users.api.serializers import UserPublicSerializer
from apps.users.models import User


def _error(exc):
    code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionError) else status.HTTP_400_BAD_REQUEST
    return Response({"detail": str(exc)}, status=code)


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ConversationSerializer(many=True), summary="List messenger conversations")
    def get(self, request):
        qs = conversations_for_user(request.user)
        if request.query_params.get("archived") != "1":
            qs = qs.filter(memberships__user=request.user, memberships__is_archived=False)
        return Response(ConversationSerializer(qs[:100], many=True, context={"request": request}).data)


class DirectConversationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=DirectConversationCreateSerializer, responses={200: ConversationSerializer, 201: ConversationSerializer})
    def post(self, request):
        serializer = DirectConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        other = User.objects.filter(public_id=serializer.validated_data["user_id"], is_active=True).first()
        if not other:
            return Response({"detail": "User not found."}, status=404)
        try:
            conversation, created = create_direct_conversation(creator=request.user, other_user=other)
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        conversation = conversation_for_user(request.user, conversation.public_id)
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class GroupConversationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=GroupConversationCreateSerializer, responses={201: ConversationSerializer})
    def post(self, request):
        serializer = GroupConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["member_ids"]
        members = list(User.objects.filter(public_id__in=ids, is_active=True))
        if len({str(user.public_id) for user in members}) != len({str(value) for value in ids}):
            return Response({"detail": "One or more users were not found."}, status=400)
        try:
            conversation = create_group_conversation(
                creator=request.user,
                title=serializer.validated_data["title"],
                members=members,
            )
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        conversation = conversation_for_user(request.user, conversation.public_id)
        return Response(ConversationSerializer(conversation, context={"request": request}).data, status=201)


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, conversation_id):
        return conversation_for_user(request.user, conversation_id)

    @extend_schema(responses=ConversationSerializer)
    def get(self, request, conversation_id):
        conversation = self._get(request, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        return Response(ConversationSerializer(conversation, context={"request": request}).data)

    @extend_schema(request=ConversationUpdateSerializer, responses=ConversationSerializer)
    def patch(self, request, conversation_id):
        conversation = self._get(request, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        serializer = ConversationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            update_conversation_settings(conversation=conversation, user=request.user, **serializer.validated_data)
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        conversation = self._get(request, conversation_id)
        return Response(ConversationSerializer(conversation, context={"request": request}).data)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MessageSerializer(many=True))
    def get(self, request, conversation_id):
        conversation = conversation_for_user(request.user, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), 100)
        except ValueError:
            limit = 50
        qs = messages_for_conversation(conversation)
        query = request.query_params.get("q", "").strip()
        if query:
            qs = qs.filter(text__icontains=query, deleted_at__isnull=True)
        before = request.query_params.get("before")
        if before:
            try:
                before_message = Message.objects.get(public_id=before, conversation=conversation)
                qs = qs.filter(created_at__lt=before_message.created_at)
            except Message.DoesNotExist:
                return Response({"detail": "Invalid before cursor."}, status=400)
        rows = list(qs[: limit + 1])
        has_more = len(rows) > limit
        rows = rows[:limit]
        rows.reverse()
        data = MessageSerializer(rows, many=True, context={"request": request}).data
        return Response({"next_before": str(rows[0].public_id) if has_more and rows else None, "results": data})

    @extend_schema(request=MessageCreateSerializer, responses={200: MessageSerializer, 201: MessageSerializer})
    def post(self, request, conversation_id):
        conversation = conversation_for_user(request.user, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = None
        reply_id = serializer.validated_data.get("reply_to_id")
        if reply_id:
            reply = Message.objects.filter(public_id=reply_id, conversation=conversation).first()
            if not reply:
                return Response({"detail": "Reply target not found."}, status=400)
        try:
            message, created = create_message(
                conversation=conversation,
                sender=request.user,
                text=serializer.validated_data.get("text", ""),
                client_id=serializer.validated_data["client_id"],
                reply_to=reply,
                attachment_ids=serializer.validated_data.get("attachment_ids", []),
            )
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        message = messages_for_conversation(conversation).get(pk=message.pk)
        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, message_id):
        return Message.objects.select_related("conversation", "sender").filter(
            public_id=message_id,
            conversation__memberships__user=request.user,
        ).first()

    @extend_schema(request=MessageUpdateSerializer, responses=MessageSerializer)
    def patch(self, request, message_id):
        message = self._get(request, message_id)
        if not message:
            return Response({"detail": "Message not found."}, status=404)
        serializer = MessageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = edit_message(message=message, actor=request.user, text=serializer.validated_data["text"])
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        message = messages_for_conversation(message.conversation).get(pk=message.pk)
        return Response(MessageSerializer(message, context={"request": request}).data)

    @extend_schema(responses={204: None})
    def delete(self, request, message_id):
        message = self._get(request, message_id)
        if not message:
            return Response({"detail": "Message not found."}, status=404)
        try:
            delete_message(message=message, actor=request.user)
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        return Response(status=204)


class MessageReactionView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, message_id):
        return Message.objects.select_related("conversation").filter(
            public_id=message_id,
            conversation__memberships__user=request.user,
        ).first()

    @extend_schema(request=ReactionSerializer, responses={200: ReactionSerializer})
    def put(self, request, message_id):
        message = self._get(request, message_id)
        if not message:
            return Response({"detail": "Message not found."}, status=404)
        serializer = ReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            edge = set_reaction(message=message, user=request.user, emoji=serializer.validated_data["emoji"])
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        return Response({"emoji": edge.emoji})

    @extend_schema(request=ReactionSerializer, responses={204: None})
    def delete(self, request, message_id):
        message = self._get(request, message_id)
        if not message:
            return Response({"detail": "Message not found."}, status=404)
        payload = request.data if request.data else {"emoji": request.query_params.get("emoji", "")}
        serializer = ReactionSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        try:
            clear_reaction(
                message=message,
                user=request.user,
                emoji=serializer.validated_data["emoji"],
            )
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        return Response(status=204)


class ConversationPinnedMessageView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PinnedMessageSerializer, responses=ConversationSerializer)
    def put(self, request, conversation_id):
        conversation = conversation_for_user(request.user, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        serializer = PinnedMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = None
        message_id = serializer.validated_data.get("message_id")
        if message_id:
            message = Message.objects.filter(public_id=message_id, conversation=conversation).first()
            if not message:
                return Response({"detail": "Message not found."}, status=400)
        try:
            pin_message(conversation=conversation, actor=request.user, message=message)
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        conversation = conversation_for_user(request.user, conversation_id)
        return Response(ConversationSerializer(conversation, context={"request": request}).data)


class ConversationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ReadSerializer, responses={200: ConversationSerializer})
    def post(self, request, conversation_id):
        conversation = conversation_for_user(request.user, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        serializer = ReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = None
        if serializer.validated_data.get("message_id"):
            message = Message.objects.filter(public_id=serializer.validated_data["message_id"], conversation=conversation).first()
            if not message:
                return Response({"detail": "Message not found."}, status=400)
        mark_read(conversation=conversation, user=request.user, message=message)
        conversation = conversation_for_user(request.user, conversation_id)
        return Response(ConversationSerializer(conversation, context={"request": request}).data)


class MessengerUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        total = 0
        for conversation in conversations_for_user(request.user).filter(memberships__user=request.user, memberships__is_archived=False):
            membership = next((m for m in conversation.memberships.all() if m.user_id == request.user.pk), None)
            if not membership:
                continue
            qs = conversation.messages.exclude(sender=request.user)
            if membership.last_read_at:
                qs = qs.filter(created_at__gt=membership.last_read_at)
            total += qs.count()
        return Response({"unread_count": total})


class MessengerUserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserPublicSerializer(many=True))
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        qs = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
        if q:
            qs = qs.filter(Q(nickname__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
        blocked = blocked_user_ids_for(request.user)
        if blocked:
            qs = qs.exclude(pk__in=blocked)
        return Response(UserPublicSerializer(qs.select_related("avatar_asset")[:30], many=True).data)


class GroupMemberView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=GroupMemberSerializer, responses={201: ConversationSerializer})
    def post(self, request, conversation_id):
        conversation = conversation_for_user(request.user, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        serializer = GroupMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(public_id=serializer.validated_data["user_id"], is_active=True).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)
        try:
            add_group_member(conversation=conversation, actor=request.user, user=user)
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        conversation = conversation_for_user(request.user, conversation_id)
        return Response(ConversationSerializer(conversation, context={"request": request}).data, status=201)

    @extend_schema(responses={204: None})
    def delete(self, request, conversation_id, user_id=None):
        conversation = conversation_for_user(request.user, conversation_id)
        if not conversation:
            return Response({"detail": "Conversation not found."}, status=404)
        user = User.objects.filter(public_id=user_id).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)
        try:
            remove_group_member(conversation=conversation, actor=request.user, user=user)
        except (ValueError, PermissionError) as exc:
            return _error(exc)
        return Response(status=204)


class WSTicketView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=WSTicketSerializer)
    def post(self, request):
        nonce = str(uuid.uuid4())
        cache.set(f"messenger:ws-ticket:{nonce}", str(request.user.public_id), timeout=75)
        ticket = signing.dumps(
            {"user_id": str(request.user.public_id), "nonce": nonce},
            salt="night-iris-messenger-ws",
            compress=True,
        )
        return Response({"ticket": ticket, "expires_in": 60})
