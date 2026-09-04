import pytest
from rest_framework.test import APIClient

from apps.publications.models import Publication
from apps.publications.services import create_publication
from apps.social.models import UserFollow


@pytest.mark.django_db
def test_discovery_prioritizes_followed_authors_for_authenticated_user(user_factory):
    viewer = user_factory(nickname="discover_viewer", email="discover-viewer@example.test")
    followed = user_factory(nickname="discover_followed", email="discover-followed@example.test")
    other = user_factory(nickname="discover_other", email="discover-other@example.test")

    other_publication = create_publication(
        author=other,
        kind=Publication.Type.ARTICLE,
        title="Generic recent article",
        content=[{"type": "paragraph", "text": "Generic discovery payload"}],
        community=None,
        tag_names=["generic"],
    )
    followed_publication = create_publication(
        author=followed,
        kind=Publication.Type.ARTICLE,
        title="Followed author article",
        content=[{"type": "paragraph", "text": "Personalized discovery payload"}],
        community=None,
        tag_names=["personalized"],
    )
    UserFollow.objects.create(follower=viewer, following=followed)

    client = APIClient()
    client.force_authenticate(viewer)
    response = client.get("/api/v1/discover/")
    assert response.status_code == 200, response.data
    assert response.data["personalized"] is True
    ids = [item["id"] for item in response.data["recommended_publications"]]
    assert str(followed_publication.public_id) in ids
    assert str(other_publication.public_id) in ids
    assert ids.index(str(followed_publication.public_id)) < ids.index(str(other_publication.public_id))


@pytest.mark.django_db
def test_discovery_has_cold_start_recommendations_for_anonymous_user(user_factory):
    author = user_factory(nickname="discover_cold", email="discover-cold@example.test")
    publication = create_publication(
        author=author,
        kind=Publication.Type.POST,
        title="",
        content=[{"type": "paragraph", "text": "Cold-start content"}],
        community=None,
        tag_names=["cold-start"],
    )
    response = APIClient().get("/api/v1/discover/")
    assert response.status_code == 200
    assert response.data["personalized"] is False
    assert str(publication.public_id) in [item["id"] for item in response.data["recommended_publications"]]
