import pytest
from rest_framework.test import APIClient

from apps.communities.models import CommunityStaff
from apps.communities.services import create_community
from apps.publications.models import Publication
from apps.publications.services import create_publication


@pytest.mark.django_db
def test_community_moderator_can_review_report_and_hide_scoped_publication(user_factory):
    owner = user_factory(nickname="trust_owner", email="trust-owner@example.test")
    moderator = user_factory(nickname="trust_mod", email="trust-mod@example.test")
    reporter = user_factory(nickname="trust_reporter", email="trust-reporter@example.test")
    community = create_community(owner=owner, slug="trust-scope", name="Trust Scope", description="")
    CommunityStaff.objects.create(community=community, user=moderator, role=CommunityStaff.Role.MODERATOR, added_by=owner)
    publication = create_publication(
        author=owner,
        kind=Publication.Type.POST,
        title="",
        content=[{"type": "paragraph", "text": "Reported community content"}],
        community=community,
        tag_names=[],
    )

    reporter_client = APIClient()
    reporter_client.force_authenticate(reporter)
    created = reporter_client.post(
        "/api/v1/reports/",
        {"target_type":"publication","target_id":str(publication.public_id),"reason":"spam","details":"Repeated promotion"},
        format="json",
    )
    assert created.status_code == 201, created.data
    report_id = created.data["id"]

    moderator_client = APIClient()
    moderator_client.force_authenticate(moderator)
    queue = moderator_client.get(f"/api/v1/communities/{community.public_id}/moderation/reports/")
    assert queue.status_code == 200
    assert [item["id"] for item in queue.data["results"]] == [report_id]

    reviewing = moderator_client.patch(
        f"/api/v1/communities/{community.public_id}/moderation/reports/{report_id}/",
        {"status":"reviewing","resolution_note":""},
        format="json",
    )
    assert reviewing.status_code == 200
    hidden = moderator_client.put(
        f"/api/v1/communities/{community.public_id}/moderation/publications/{publication.public_id}/hidden/",
        {"report_id":report_id,"reason":"Confirmed spam"},
        format="json",
    )
    assert hidden.status_code == 200, hidden.data
    publication.refresh_from_db()
    assert publication.visibility == Publication.Visibility.HIDDEN


@pytest.mark.django_db
def test_community_editor_cannot_use_moderation_queue(user_factory):
    owner = user_factory(nickname="trust_owner2", email="trust-owner2@example.test")
    editor = user_factory(nickname="trust_editor", email="trust-editor@example.test")
    community = create_community(owner=owner, slug="trust-editor-scope", name="Trust Editor Scope", description="")
    CommunityStaff.objects.create(community=community, user=editor, role=CommunityStaff.Role.EDITOR, added_by=owner)
    client = APIClient()
    client.force_authenticate(editor)
    response = client.get(f"/api/v1/communities/{community.public_id}/moderation/reports/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_community_moderator_cannot_moderate_foreign_community_target(user_factory):
    owner = user_factory(nickname="trust_owner3", email="trust-owner3@example.test")
    moderator = user_factory(nickname="trust_mod3", email="trust-mod3@example.test")
    foreign_owner = user_factory(nickname="trust_foreign", email="trust-foreign@example.test")
    community = create_community(owner=owner, slug="trust-local", name="Trust Local", description="")
    foreign = create_community(owner=foreign_owner, slug="trust-foreign", name="Trust Foreign", description="")
    CommunityStaff.objects.create(community=community, user=moderator, role=CommunityStaff.Role.MODERATOR, added_by=owner)
    publication = create_publication(
        author=foreign_owner,
        kind=Publication.Type.POST,
        title="",
        content=[{"type":"paragraph","text":"Foreign content"}],
        community=foreign,
        tag_names=[],
    )
    client = APIClient()
    client.force_authenticate(moderator)
    response = client.put(
        f"/api/v1/communities/{community.public_id}/moderation/publications/{publication.public_id}/hidden/",
        {"reason":"Should not cross scope"},
        format="json",
    )
    assert response.status_code == 404
    publication.refresh_from_db()
    assert publication.visibility == Publication.Visibility.PUBLISHED
