import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from django.db import transaction
from channels.db import database_sync_to_async

from apps.discussions.models import Comment
from apps.publications.models import Publication
from apps.social.consumer import PublicationEngagementConsumer
from apps.social.models import PublicationBookmark, PublicationReaction
from apps.social.realtime import publication_engagement_group
from apps.users.models import User


class EngagementRealtimeSignalTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            nickname="rt_author",
            email="rt-author@example.com",
            password="Test-password-2026!",
            first_name="RT",
            last_name="Author",
            country="RU",
            nationality="RU",
        )
        self.viewer = User.objects.create_user(
            nickname="rt_viewer",
            email="rt-viewer@example.com",
            password="Test-password-2026!",
            first_name="RT",
            last_name="Viewer",
            country="RU",
            nationality="RU",
        )
        self.publication = Publication.objects.create(
            author=self.author,
            kind=Publication.Type.POST,
            title="Realtime",
            content=[{"type": "paragraph", "text": "Realtime"}],
            content_text="Realtime",
        )
        self.layer = get_channel_layer()
        self.channel = async_to_sync(self.layer.new_channel)("engagement-test.")
        async_to_sync(self.layer.group_add)(
            publication_engagement_group(self.publication.public_id),
            self.channel,
        )

    def receive(self):
        return async_to_sync(self.layer.receive)(self.channel)

    def test_reaction_commit_broadcasts_publication_change(self):
        with self.captureOnCommitCallbacks(execute=True):
            PublicationReaction.objects.create(
                user=self.viewer,
                publication=self.publication,
                kind=PublicationReaction.Kind.HEART,
            )

        event = self.receive()
        self.assertEqual(event["type"], "engagement.changed")
        self.assertEqual(event["publication_id"], str(self.publication.public_id))
        self.assertEqual(event["reason"], "reaction")

    def test_bookmark_commit_broadcasts_publication_change(self):
        with self.captureOnCommitCallbacks(execute=True):
            PublicationBookmark.objects.create(
                user=self.viewer,
                publication=self.publication,
            )

        event = self.receive()
        self.assertEqual(event["reason"], "bookmark")

    def test_comment_commit_broadcasts_publication_change(self):
        with self.captureOnCommitCallbacks(execute=True):
            Comment.objects.create(
                publication=self.publication,
                author=self.viewer,
                kind=Comment.Kind.COMMENT,
                content=[{"type": "paragraph", "text": "Realtime reply"}],
                content_text="Realtime reply",
            )

        event = self.receive()
        self.assertEqual(event["reason"], "comment")


@database_sync_to_async
def _make_realtime_fixture():
    author = User.objects.create_user(
        nickname="socket_author",
        email="socket-author@example.com",
        password="Test-password-2026!",
        first_name="Socket",
        last_name="Author",
        country="RU",
        nationality="RU",
    )
    viewer = User.objects.create_user(
        nickname="socket_viewer",
        email="socket-viewer@example.com",
        password="Test-password-2026!",
        first_name="Socket",
        last_name="Viewer",
        country="RU",
        nationality="RU",
    )
    publication = Publication.objects.create(
        author=author,
        kind=Publication.Type.POST,
        title="Socket publication",
        content=[{"type": "paragraph", "text": "Socket"}],
        content_text="Socket",
    )
    return viewer, publication


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.websocket
async def test_engagement_consumer_ready_and_changed_event():
    viewer, publication = await _make_realtime_fixture()
    communicator = WebsocketCommunicator(
        PublicationEngagementConsumer.as_asgi(),
        f"/ws/engagement/?publication={publication.public_id}",
    )
    communicator.scope["user"] = viewer

    connected, _ = await communicator.connect()
    assert connected
    ready = await communicator.receive_json_from()
    assert ready == {
        "type": "engagement.ready",
        "publication_id": str(publication.public_id),
    }

    layer = get_channel_layer()
    await layer.group_send(
        publication_engagement_group(publication.public_id),
        {
            "type": "engagement.changed",
            "publication_id": str(publication.public_id),
            "reason": "reaction",
        },
    )
    changed = await communicator.receive_json_from()
    assert changed == {
        "type": "engagement.changed",
        "publication_id": str(publication.public_id),
        "reason": "reaction",
    }
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.websocket
async def test_engagement_consumer_rejects_anonymous_user():
    _viewer, publication = await _make_realtime_fixture()
    communicator = WebsocketCommunicator(
        PublicationEngagementConsumer.as_asgi(),
        f"/ws/engagement/?publication={publication.public_id}",
    )

    connected, code = await communicator.connect()
    assert not connected
    assert code == 4401
