from datetime import timedelta

import pytest
from django.utils import timezone

from apps.communities.models import Community
from apps.publications.models import Publication, Tag
from apps.social.models import UserMute


@pytest.fixture
def search_catalog(user_factory):
    author = user_factory()
    publications = [Publication.objects.create(
        author=author, kind=Publication.Type.ARTICLE, title=f"searchneedle {i}",
        content=[{"type": "paragraph", "text": "Indexed body"}], content_text="Indexed body",
    ) for i in range(35)]
    Publication.objects.filter(author=author).update(created_at=timezone.now())
    return author, publications


@pytest.mark.django_db
def test_publication_pages_preserve_order_and_legacy_default(api_client, search_catalog):
    _, publications = search_catalog
    first = api_client.get("/api/v1/search/", {"scope": "publications", "q": "searchneedle"})
    assert first.status_code == 200
    assert len(first.data["publications"]) == 30
    assert first.data["pagination"] == {
        "page": 1, "page_size": 30, "total_pages": 2, "total_results": 35,
        "has_next": True, "has_previous": False,
    }
    second = api_client.get("/api/v1/search/", {"scope": "publications", "q": "searchneedle", "page": 2})
    assert second.status_code == 200
    combined = first.data["publications"] + second.data["publications"]
    assert [row["id"] for row in combined] == [str(item.public_id) for item in reversed(publications)]
    assert second.data["pagination"]["has_next"] is False
    assert first.data["users"] == first.data["communities"] == first.data["tags"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("scope", ["users", "communities", "tags"])
def test_other_scopes_have_complete_disjoint_pages(api_client, user_factory, scope):
    owner = user_factory(nickname="scope_owner")
    for i in range(5):
        if scope == "users":
            user_factory(nickname=f"scopeperson_{i}")
        elif scope == "communities":
            Community.objects.create(owner=owner, name="Scope common name", slug=f"scope-{i}")
        else:
            Tag.objects.create(name=f"scopetag {i}", slug=f"scopetag-{i}")
    query = {"users": "scopeperson", "communities": "Scope", "tags": "scopetag"}[scope]
    pages = [api_client.get("/api/v1/search/", {"q": query, "scope": scope, "page_size": 2, "page": page}) for page in (1, 2, 3)]
    assert all(response.status_code == 200 for response in pages)
    ids = [row["id"] for response in pages for row in response.data[scope]]
    assert len(ids) == len(set(ids)) == 5
    assert [len(response.data[scope]) for response in pages] == [2, 2, 1]
    assert pages[-1].data["pagination"]["has_next"] is False


@pytest.mark.django_db
def test_all_scope_remains_a_preview(api_client, search_catalog):
    response = api_client.get("/api/v1/search/", {"q": "searchneedle", "scope": "all", "page": 999, "page_size": 1})
    assert response.status_code == 200
    assert len(response.data["publications"]) == 6
    assert response.data["counts"]["publications"] == 35
    assert response.data["pagination"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("params", [
    {"page": "0"}, {"page": "-1"}, {"page": "abc"}, {"page": "1.5"},
    {"page_size": "0"}, {"page_size": "51"}, {"page_size": "abc"},
])
def test_invalid_page_parameters_return_400(api_client, params):
    assert api_client.get("/api/v1/search/", {"scope": "publications", **params}).status_code == 400


@pytest.mark.django_db
def test_empty_and_out_of_range_pages(api_client):
    first = api_client.get("/api/v1/search/", {"scope": "publications"})
    assert first.status_code == 200
    assert first.data["pagination"]["total_pages"] == 1
    assert first.data["pagination"]["total_results"] == 0
    assert api_client.get("/api/v1/search/", {"scope": "publications", "page": 2}).status_code == 404


@pytest.mark.django_db
def test_filters_and_viewer_visibility_apply_before_pagination(api_client, user_factory):
    viewer, visible, muted = user_factory(), user_factory(), user_factory()
    UserMute.objects.create(muter=viewer, muted=muted)
    tag = Tag.objects.create(name="tagfilter", slug="tagfilter")
    included = []
    for i in range(6):
        pub = Publication.objects.create(author=visible, kind=Publication.Type.ARTICLE, title=f"Filtered {i}")
        pub.tags.add(tag)
        included.append(pub)
    for kwargs in [
        {"author": muted}, {"visibility": Publication.Visibility.HIDDEN}, {"kind": Publication.Type.POST},
    ]:
        pub = Publication.objects.create(**{"author": visible, "kind": Publication.Type.ARTICLE, **kwargs})
        pub.tags.add(tag)
    old = Publication.objects.create(author=visible, kind=Publication.Type.ARTICLE)
    old.tags.add(tag)
    Publication.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=60))
    api_client.force_authenticate(viewer)
    params = {"scope": "publications", "tag": "tagfilter", "type": "article", "date": "week", "sort": "latest", "page_size": 4}
    first, second = [api_client.get("/api/v1/search/", {**params, "page": page}) for page in (1, 2)]
    assert first.status_code == second.status_code == 200
    assert first.data["counts"]["publications"] == 6
    ids = {row["id"] for response in (first, second) for row in response.data["publications"]}
    assert ids == {str(pub.public_id) for pub in included}
