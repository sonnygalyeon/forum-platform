import pytest
from rest_framework.test import APIClient

from apps.publications.models import Publication
from apps.publications.services import create_publication
from apps.social.models import PublicationBookmark


@pytest.mark.django_db
def test_bookmark_is_idempotent_private_and_listed(user_factory):
    owner = user_factory(nickname="bookmark_author", email="bookmark-author@example.test")
    reader = user_factory(nickname="bookmark_reader", email="bookmark-reader@example.test")
    publication = create_publication(
        author=owner,
        kind=Publication.Type.ARTICLE,
        title="Saved reference",
        content=[{"type": "paragraph", "text": "Useful payload"}],
        community=None,
        tag_names=["saved"],
    )
    client = APIClient()
    client.force_authenticate(reader)
    path = f"/api/v1/publications/{publication.public_id}/bookmark/"

    assert client.get(path).data == {"bookmarked": False}
    assert client.put(path).status_code == 204
    assert client.put(path).status_code == 204
    assert PublicationBookmark.objects.filter(user=reader, publication=publication).count() == 1
    assert client.get(path).data == {"bookmarked": True}

    saved = client.get("/api/v1/users/me/bookmarks/")
    assert saved.status_code == 200
    assert saved.data["results"][0]["id"] == str(publication.public_id)

    assert client.delete(path).status_code == 204
    assert client.get(path).data == {"bookmarked": False}


@pytest.mark.django_db
def test_bookmarks_require_authentication(user_factory):
    owner = user_factory(nickname="private_saved_author", email="private-saved-author@example.test")
    publication = create_publication(
        author=owner,
        kind=Publication.Type.POST,
        title="",
        content=[{"type": "paragraph", "text": "Private saved state"}],
        community=None,
        tag_names=[],
    )
    client = APIClient()
    assert client.get("/api/v1/users/me/bookmarks/").status_code == 401
    assert client.get(f"/api/v1/publications/{publication.public_id}/bookmark/").status_code == 401
