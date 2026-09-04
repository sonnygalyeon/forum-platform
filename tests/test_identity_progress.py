import pytest
from rest_framework.test import APIClient

from apps.publications.models import Publication
from apps.publications.services import create_publication


@pytest.mark.django_db
def test_identity_progress_exposes_transparent_breakdown(user_factory):
    user = user_factory(nickname="progress_user", email="progress-user@example.test")
    for index in range(3):
        create_publication(
            author=user,
            kind=Publication.Type.POST,
            title="",
            content=[{"type": "paragraph", "text": f"Contribution {index}"}],
            community=None,
            tag_names=[],
        )

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/v1/identity/me/progress/")
    assert response.status_code == 200
    assert response.data["metrics"]["publications"] == 3
    assert response.data["point_breakdown"]["publications"] == 6
    assert response.data["reputation"] >= 6
    assert 0 <= response.data["progress_percent"] <= 100
    assert response.data["points_to_next_level"] >= 0


@pytest.mark.django_db
def test_public_identity_progress_is_available_without_private_profile_data(user_factory):
    user = user_factory(nickname="public_progress", email="public-progress@example.test")
    response = APIClient().get(f"/api/v1/users/{user.public_id}/identity/progress/")
    assert response.status_code == 200
    assert set(response.data["metrics"]) == {"publications", "answers", "accepted", "followers", "communities", "positive_score"}
