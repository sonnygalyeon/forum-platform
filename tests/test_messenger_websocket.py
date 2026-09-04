import uuid
from urllib.parse import quote

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.core import signing
from django.core.cache import cache

from apps.messenger.consumer import MessengerConsumer
from config.asgi import application


async def _ticket_for(user):
    nonce = uuid.uuid4().hex
    await sync_to_async(cache.set)(
        f"messenger:ws-ticket:{nonce}",
        str(user.public_id),
        timeout=75,
    )
    ticket = signing.dumps(
        {"user_id": str(user.public_id), "nonce": nonce},
        salt="night-iris-messenger-ws",
    )
    return quote(ticket, safe="")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.websocket
async def test_authenticated_messenger_socket_ready_and_ping(user_factory):
    user = await sync_to_async(user_factory)(
        nickname="socket_user",
        email="socket-user@example.test",
    )
    communicator = WebsocketCommunicator(MessengerConsumer.as_asgi(), "/ws/messenger/")
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    assert connected
    ready = await communicator.receive_json_from(timeout=2)
    assert ready["type"] == "messenger.ready"
    assert ready["user_id"] == str(user.public_id)

    await communicator.send_json_to({"type": "ping"})
    pong = await communicator.receive_json_from(timeout=2)
    assert pong == {"type": "pong"}
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.websocket
async def test_asgi_messenger_accepts_allowed_origin_with_ticket(user_factory):
    user = await sync_to_async(user_factory)(
        nickname="socket_origin_ok",
        email="socket-origin-ok@example.test",
    )
    ticket = await _ticket_for(user)
    communicator = WebsocketCommunicator(
        application,
        f"/ws/messenger/?ticket={ticket}",
        headers=[(b"origin", b"http://testserver")],
    )

    connected, _ = await communicator.connect()
    assert connected
    ready = await communicator.receive_json_from(timeout=2)
    assert ready["type"] == "messenger.ready"
    assert ready["user_id"] == str(user.public_id)
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.websocket
async def test_asgi_messenger_rejects_untrusted_origin(user_factory):
    user = await sync_to_async(user_factory)(
        nickname="socket_origin_bad",
        email="socket-origin-bad@example.test",
    )
    ticket = await _ticket_for(user)
    communicator = WebsocketCommunicator(
        application,
        f"/ws/messenger/?ticket={ticket}",
        headers=[(b"origin", b"https://evil.example")],
    )

    connected, _ = await communicator.connect()
    assert not connected
