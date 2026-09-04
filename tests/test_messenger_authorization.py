import pytest

from apps.media.models import MediaAsset
from apps.messenger.models import Conversation, ConversationMember


def _group(owner, *members):
    conversation = Conversation.objects.create(
        kind=Conversation.Kind.GROUP,
        title="Security test group",
        created_by=owner,
    )
    ConversationMember.objects.create(
        conversation=conversation,
        user=owner,
        role=ConversationMember.Role.OWNER,
    )
    for user, role in members:
        ConversationMember.objects.create(
            conversation=conversation,
            user=user,
            role=role,
        )
    return conversation


@pytest.mark.django_db
def test_regular_member_cannot_add_group_members(api_client, user_factory):
    owner = user_factory(nickname="auth_owner", email="auth-owner@example.test")
    member = user_factory(nickname="auth_member", email="auth-member@example.test")
    candidate = user_factory(nickname="auth_candidate", email="auth-candidate@example.test")
    conversation = _group(owner, (member, ConversationMember.Role.MEMBER))

    api_client.force_authenticate(member)
    response = api_client.post(
        f"/api/v1/messenger/conversations/{conversation.public_id}/members/",
        {"user_id": str(candidate.public_id)},
        format="json",
    )

    assert response.status_code == 403
    assert not ConversationMember.objects.filter(conversation=conversation, user=candidate).exists()


@pytest.mark.django_db
def test_admin_cannot_promote_members(api_client, user_factory):
    owner = user_factory(nickname="role_owner", email="role-owner@example.test")
    admin = user_factory(nickname="role_admin", email="role-admin@example.test")
    member = user_factory(nickname="role_member", email="role-member@example.test")
    conversation = _group(
        owner,
        (admin, ConversationMember.Role.ADMIN),
        (member, ConversationMember.Role.MEMBER),
    )

    api_client.force_authenticate(admin)
    response = api_client.patch(
        f"/api/v1/messenger/conversations/{conversation.public_id}/members/{member.public_id}/role/",
        {"role": ConversationMember.Role.ADMIN},
        format="json",
    )

    assert response.status_code == 403
    edge = ConversationMember.objects.get(conversation=conversation, user=member)
    assert edge.role == ConversationMember.Role.MEMBER


@pytest.mark.django_db
def test_owner_can_promote_member(api_client, user_factory):
    owner = user_factory(nickname="promote_owner", email="promote-owner@example.test")
    member = user_factory(nickname="promote_member", email="promote-member@example.test")
    conversation = _group(owner, (member, ConversationMember.Role.MEMBER))

    api_client.force_authenticate(owner)
    response = api_client.patch(
        f"/api/v1/messenger/conversations/{conversation.public_id}/members/{member.public_id}/role/",
        {"role": ConversationMember.Role.ADMIN},
        format="json",
    )

    assert response.status_code == 200
    edge = ConversationMember.objects.get(conversation=conversation, user=member)
    assert edge.role == ConversationMember.Role.ADMIN


@pytest.mark.django_db
def test_regular_member_cannot_edit_group_metadata(api_client, user_factory):
    owner = user_factory(nickname="meta_owner", email="meta-owner@example.test")
    member = user_factory(nickname="meta_member", email="meta-member@example.test")
    conversation = _group(owner, (member, ConversationMember.Role.MEMBER))

    api_client.force_authenticate(member)
    response = api_client.patch(
        f"/api/v1/messenger/conversations/{conversation.public_id}/",
        {"title": "Unauthorized title"},
        format="json",
    )

    assert response.status_code == 403
    conversation.refresh_from_db()
    assert conversation.title == "Security test group"


@pytest.mark.django_db
def test_group_admin_cannot_use_another_users_asset_as_avatar(api_client, user_factory):
    owner = user_factory(nickname="avatar_owner", email="avatar-owner@example.test")
    admin = user_factory(nickname="avatar_admin", email="avatar-admin@example.test")
    asset_owner = user_factory(nickname="asset_owner", email="asset-owner@example.test")
    conversation = _group(owner, (admin, ConversationMember.Role.ADMIN))
    asset = MediaAsset.objects.create(
        owner=asset_owner,
        original_name="avatar.png",
        declared_content_type="image/png",
        kind=MediaAsset.Kind.IMAGE,
        size_bytes=128,
        object_key=f"uploads/{asset_owner.public_id}/foreign-avatar.png",
        upload_id="",
        part_size=5 * 1024 * 1024,
        part_count=1,
        status=MediaAsset.Status.READY,
    )

    api_client.force_authenticate(admin)
    response = api_client.patch(
        f"/api/v1/messenger/conversations/{conversation.public_id}/",
        {"avatar_asset_id": str(asset.public_id)},
        format="json",
    )

    assert response.status_code == 403
    conversation.refresh_from_db()
    assert conversation.avatar_asset_id is None
