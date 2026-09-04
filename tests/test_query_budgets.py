import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.messenger.models import Conversation, ConversationMember, Message
from apps.publications.models import Publication
from apps.publications.services import create_publication


def _queries_for(client, path):
    with CaptureQueriesContext(connection) as captured:
        response = client.get(path)
    return response, captured


@pytest.mark.django_db
@pytest.mark.query_budget
def test_publication_list_query_budget(user_factory):
    author = user_factory(nickname="query_author", email="query-author@example.test")
    for index in range(8):
        create_publication(
            author=author,
            kind=Publication.Type.ARTICLE,
            title=f"Query budget {index}",
            content=[{"type": "paragraph", "text": f"Payload {index}"}],
            community=None,
            tag_names=["query-budget", f"tag-{index % 2}"],
        )

    client = APIClient()
    response, captured = _queries_for(client, "/api/v1/publications/")
    assert response.status_code == 200
    assert len(response.data["results"]) >= 8
    assert len(captured) <= 18, [query["sql"] for query in captured]


@pytest.mark.django_db
@pytest.mark.query_budget
def test_publication_search_query_budget(user_factory):
    author = user_factory(nickname="search_author", email="search-author@example.test")
    for index in range(12):
        create_publication(
            author=author,
            kind=Publication.Type.ARTICLE,
            title=f"PostgreSQL tuning {index}",
            content=[{"type": "paragraph", "text": "Night Iris performance payload"}],
            community=None,
            tag_names=["performance"],
        )

    client = APIClient()
    response, captured = _queries_for(client, "/api/v1/search/?q=performance&scope=publications")
    assert response.status_code == 200
    assert len(captured) <= 20, [query["sql"] for query in captured]


@pytest.mark.django_db
@pytest.mark.query_budget
def test_messenger_conversation_list_query_budget(user_factory):
    user = user_factory(nickname="inbox_owner", email="inbox-owner@example.test")
    peer = user_factory(nickname="inbox_peer", email="inbox-peer@example.test")
    for index in range(12):
        conversation = Conversation.objects.create(
            kind=Conversation.Kind.GROUP,
            title=f"Inbox {index}",
            created_by=user,
        )
        ConversationMember.objects.create(
            conversation=conversation,
            user=user,
            role=ConversationMember.Role.OWNER,
        )
        ConversationMember.objects.create(
            conversation=conversation,
            user=peer,
        )

    client = APIClient()
    client.force_authenticate(user)
    response, captured = _queries_for(client, "/api/v1/messenger/conversations/")
    assert response.status_code == 200
    assert len(response.data) == 12
    assert len(captured) <= 18, [query["sql"] for query in captured]


@pytest.mark.django_db
@pytest.mark.query_budget
def test_messenger_message_page_query_budget(user_factory):
    user = user_factory(nickname="history_owner", email="history-owner@example.test")
    peer = user_factory(nickname="history_peer", email="history-peer@example.test")
    conversation = Conversation.objects.create(
        kind=Conversation.Kind.GROUP,
        title="History",
        created_by=user,
    )
    ConversationMember.objects.create(
        conversation=conversation,
        user=user,
        role=ConversationMember.Role.OWNER,
    )
    ConversationMember.objects.create(conversation=conversation, user=peer)
    Message.objects.bulk_create(
        [
            Message(
                conversation=conversation,
                sender=user if index % 2 == 0 else peer,
                client_id=uuid.uuid4(),
                text=f"message {index}",
            )
            for index in range(40)
        ]
    )

    client = APIClient()
    client.force_authenticate(user)
    response, captured = _queries_for(
        client,
        f"/api/v1/messenger/conversations/{conversation.public_id}/messages/?limit=20",
    )
    assert response.status_code == 200
    assert len(response.data["results"]) == 20
    assert len(captured) <= 24, [query["sql"] for query in captured]
