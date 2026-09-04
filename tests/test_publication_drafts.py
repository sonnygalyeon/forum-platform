import pytest
from rest_framework.test import APIClient

from apps.publications.models import Publication, PublicationDraft
from apps.publications.services import create_publication


@pytest.mark.django_db
def test_publication_draft_autosave_publish_and_owner_isolation(user_factory):
    owner = user_factory(nickname="draft_owner", email="draft-owner@example.test")
    other = user_factory(nickname="draft_other", email="draft-other@example.test")
    client = APIClient()
    client.force_authenticate(owner)

    created = client.post(
        "/api/v1/publication-drafts/",
        {"type": "article", "title": "", "content": [], "tags": []},
        format="json",
    )
    assert created.status_code == 201, created.data
    draft_id = created.data["id"]

    saved = client.patch(
        f"/api/v1/publication-drafts/{draft_id}/",
        {
            "title": "Drafted article",
            "content": [
                {"type": "paragraph", "text": "Autosaved body"},
                {
                    "type": "embed",
                    "url": "https://example.com/reference",
                    "title": "Reference",
                    "description": "Safe link card",
                },
            ],
            "tags": ["drafts", "Drafts", "product"],
        },
        format="json",
    )
    assert saved.status_code == 200, saved.data
    assert saved.data["tags"] == ["drafts", "product"]

    other_client = APIClient()
    other_client.force_authenticate(other)
    hidden = other_client.get(f"/api/v1/publication-drafts/{draft_id}/")
    assert hidden.status_code == 404

    published = client.post(f"/api/v1/publication-drafts/{draft_id}/publish/", format="json")
    assert published.status_code == 201, published.data
    assert published.data["title"] == "Drafted article"
    assert published.data["revision"] == 1
    assert not PublicationDraft.objects.filter(public_id=draft_id).exists()


@pytest.mark.django_db
def test_edit_draft_publishes_as_new_revision(user_factory):
    owner = user_factory(nickname="draft_editor", email="draft-editor@example.test")
    publication = create_publication(
        author=owner,
        kind=Publication.Type.TOPIC,
        title="Original title",
        content=[{"type": "paragraph", "text": "Original body"}],
        community=None,
        tag_names=["original"],
    )
    client = APIClient()
    client.force_authenticate(owner)

    draft = client.post(
        "/api/v1/publication-drafts/",
        {
            "type": "topic",
            "title": "Edited title",
            "content": [{"type": "paragraph", "text": "Edited body"}],
            "tags": ["edited"],
            "source_publication_id": str(publication.public_id),
        },
        format="json",
    )
    assert draft.status_code == 201, draft.data

    published = client.post(f"/api/v1/publication-drafts/{draft.data['id']}/publish/", format="json")
    assert published.status_code == 200, published.data
    assert published.data["id"] == str(publication.public_id)
    assert published.data["revision"] == 2
    publication.refresh_from_db()
    assert publication.title == "Edited title"
    assert publication.current_revision == 2


@pytest.mark.django_db
def test_draft_rejects_unsafe_embed_scheme(user_factory):
    owner = user_factory(nickname="embed_owner", email="embed-owner@example.test")
    client = APIClient()
    client.force_authenticate(owner)

    response = client.post(
        "/api/v1/publication-drafts/",
        {
            "type": "post",
            "content": [{"type": "embed", "url": "javascript:alert(1)", "title": "Nope"}],
            "tags": [],
        },
        format="json",
    )
    assert response.status_code == 400
