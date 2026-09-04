import pytest
from rest_framework.test import APIClient

from apps.communities.models import CommunityStaff
from apps.communities.services import create_community


@pytest.mark.django_db
def test_owner_can_assign_staff_and_roles_expose_permissions(user_factory):
    owner = user_factory(nickname="community_owner", email="community-owner@example.test")
    moderator = user_factory(nickname="community_mod", email="community-mod@example.test")
    editor = user_factory(nickname="community_editor", email="community-editor@example.test")
    community = create_community(owner=owner, slug="product-ux", name="Product UX", description="")

    owner_client = APIClient()
    owner_client.force_authenticate(owner)
    staff_path = f"/api/v1/communities/{community.public_id}/staff/"
    add_mod = owner_client.post(staff_path, {"user_id": str(moderator.public_id), "role": "moderator"}, format="json")
    add_editor = owner_client.post(staff_path, {"user_id": str(editor.public_id), "role": "editor"}, format="json")
    assert add_mod.status_code == 201, add_mod.data
    assert add_editor.status_code == 201, add_editor.data
    assert CommunityStaff.objects.filter(community=community).count() == 2

    moderator_client = APIClient()
    moderator_client.force_authenticate(moderator)
    moderator_detail = moderator_client.get(f"/api/v1/communities/{community.public_id}/")
    assert moderator_detail.status_code == 200
    assert moderator_detail.data["my_role"] == "moderator"
    assert moderator_detail.data["can_moderate"] is True
    assert moderator_detail.data["can_edit"] is False

    editor_client = APIClient()
    editor_client.force_authenticate(editor)
    editor_detail = editor_client.get(f"/api/v1/communities/{community.public_id}/")
    assert editor_detail.data["my_role"] == "editor"
    assert editor_detail.data["can_edit"] is True
    updated = editor_client.patch(f"/api/v1/communities/{community.public_id}/", {"description": "Edited by staff"}, format="json")
    assert updated.status_code == 200
    assert updated.data["description"] == "Edited by staff"


@pytest.mark.django_db
def test_only_owner_can_manage_community_staff(user_factory):
    owner = user_factory(nickname="staff_owner", email="staff-owner@example.test")
    outsider = user_factory(nickname="staff_outsider", email="staff-outsider@example.test")
    target = user_factory(nickname="staff_target", email="staff-target@example.test")
    community = create_community(owner=owner, slug="staff-guard", name="Staff Guard", description="")

    client = APIClient()
    client.force_authenticate(outsider)
    response = client.post(
        f"/api/v1/communities/{community.public_id}/staff/",
        {"user_id": str(target.public_id), "role": "moderator"},
        format="json",
    )
    assert response.status_code == 403
    assert not CommunityStaff.objects.filter(community=community, user=target).exists()
