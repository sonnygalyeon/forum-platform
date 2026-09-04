from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.messenger.api.serializers import (
    ConversationSerializer,
    GroupMemberSerializer,
    WSTicketSerializer,
)
from apps.messenger.api.views import GroupMemberView, WSTicketView


@extend_schema_view(
    post=extend_schema(
        operation_id="messenger_group_member_add",
        request=GroupMemberSerializer,
        responses={201: ConversationSerializer},
    ),
)
class GroupMemberCollectionView(GroupMemberView):
    http_method_names = ["post", "options"]


@extend_schema_view(
    delete=extend_schema(
        operation_id="messenger_group_member_remove",
        request=None,
        responses={204: None},
    ),
)
class GroupMemberDetailView(GroupMemberView):
    http_method_names = ["delete", "options"]


@extend_schema_view(
    post=extend_schema(
        operation_id="messenger_ws_ticket_create",
        request=None,
        responses=WSTicketSerializer,
    ),
)
class WSTicketSchemaView(WSTicketView):
    pass
