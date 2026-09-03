import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from apps.messenger.consumer import MessengerConsumer


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
