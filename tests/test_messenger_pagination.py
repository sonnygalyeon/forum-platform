import uuid

import pytest
from django.utils import timezone

from apps.messenger.models import Message
from apps.messenger.services import create_direct_conversation


@pytest.mark.django_db
def test_message_cursor_keeps_equal_timestamp_messages(api_client, user_factory):
    alice, bob = user_factory(), user_factory()
    conversation, _ = create_direct_conversation(creator=alice, other_user=bob)
    messages = [Message.objects.create(conversation=conversation, sender=alice, text=str(i)) for i in range(5)]
    Message.objects.filter(conversation=conversation).update(created_at=timezone.now())
    api_client.force_authenticate(bob)
    url = f"/api/v1/messenger/conversations/{conversation.public_id}/messages/"
    pages = []
    cursor = None
    for _ in range(4):
        response = api_client.get(url, {"limit": 2, **({"before": cursor} if cursor else {})})
        assert response.status_code == 200
        pages.append([row["id"] for row in response.data["results"]])
        cursor = response.data["next_before"]
        if cursor is None:
            break
    ids = [str(message.public_id) for message in messages]
    assert pages == [ids[3:5], ids[1:3], ids[:1]]
    assert cursor is None


@pytest.mark.django_db
@pytest.mark.parametrize("cursor", ["not-a-uuid", str(uuid.uuid4())])
def test_bad_message_cursor_returns_400(api_client, user_factory, cursor):
    alice, bob = user_factory(), user_factory()
    conversation, _ = create_direct_conversation(creator=alice, other_user=bob)
    api_client.force_authenticate(alice)
    response = api_client.get(
        f"/api/v1/messenger/conversations/{conversation.public_id}/messages/", {"before": cursor}
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_message_cursor_is_scoped_to_conversation(api_client, user_factory):
    alice, bob, charlie = user_factory(), user_factory(), user_factory()
    conversation, _ = create_direct_conversation(creator=alice, other_user=bob)
    other, _ = create_direct_conversation(creator=alice, other_user=charlie)
    message = Message.objects.create(conversation=other, sender=charlie, text="private")
    api_client.force_authenticate(bob)
    response = api_client.get(
        f"/api/v1/messenger/conversations/{conversation.public_id}/messages/",
        {"before": str(message.public_id)},
    )
    assert response.status_code == 400
