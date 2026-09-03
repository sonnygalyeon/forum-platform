import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.integration
def test_article_comment_vote_and_revision_flow(user_factory):
    author = user_factory(nickname="workflow_author", email="workflow-author@example.test")
    commenter = user_factory(nickname="workflow_commenter", email="workflow-commenter@example.test")

    author_client = APIClient()
    author_client.force_authenticate(author)
    create = author_client.post(
        "/api/v1/publications/",
        {
            "type": "article",
            "title": "Integration article",
            "content": [{"type": "paragraph", "text": "Initial content"}],
            "tags": ["integration", "pytest"],
        },
        format="json",
    )
    assert create.status_code == 201, create.data
    publication_id = create.data["id"]

    edit = author_client.patch(
        f"/api/v1/publications/{publication_id}/",
        {
            "title": "Integration article edited",
            "content": [{"type": "paragraph", "text": "Second revision"}],
        },
        format="json",
    )
    assert edit.status_code == 200, edit.data
    assert edit.data["revision"] == 2

    commenter_client = APIClient()
    commenter_client.force_authenticate(commenter)
    comment = commenter_client.post(
        f"/api/v1/publications/{publication_id}/comments/",
        {"content": [{"type": "paragraph", "text": "Useful comment"}]},
        format="json",
    )
    assert comment.status_code == 201, comment.data

    vote = author_client.put(
        f"/api/v1/comments/{comment.data['id']}/vote/",
        {"value": 1},
        format="json",
    )
    assert vote.status_code == 200, vote.data
    assert vote.data == {"score": 1, "my_vote": 1}

    revisions = author_client.get(f"/api/v1/publications/{publication_id}/revisions/")
    assert revisions.status_code == 200
    assert len(revisions.data["results"]) == 2


@pytest.mark.django_db
def test_register_login_and_me_contract(api_client):
    payload = {
        "nickname": "contract_user",
        "email": "contract-user@example.test",
        "password": "StrongContractPass_2026!",
        "first_name": "Contract",
        "last_name": "User",
        "country": "DE",
        "nationality": "DE",
        "interface_language": "ru",
    }
    registered = api_client.post("/api/v1/auth/register/", payload, format="json")
    assert registered.status_code == 201, registered.data
    assert registered.data["user"]["nickname"] == payload["nickname"]
    assert registered.data["access"]
    assert registered.data["refresh"]

    login = api_client.post(
        "/api/v1/auth/login/",
        {"nickname": payload["nickname"], "password": payload["password"]},
        format="json",
    )
    assert login.status_code == 200, login.data
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = api_client.get("/api/v1/users/me/")
    assert me.status_code == 200
    assert me.data["email"] == payload["email"]
