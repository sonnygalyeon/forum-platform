import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.publications.models import Publication
from apps.publications.services import create_publication


@pytest.mark.django_db
@pytest.mark.query_budget
def test_publication_list_query_budget(user_factory):
    author = user_factory(nickname="query_author", email="query-author@example.test")
    for index in range(8):
        create_publication(
            author=author,
            kind=Publication.Type.ARTICLE,
            title=f"Query budget {index}",
            content=[{"type": "paragraph", "text": f"Payload {index}"}],
            community=None,
            tag_names=["query-budget", f"tag-{index % 2}"],
        )

    client = APIClient()
    with CaptureQueriesContext(connection) as captured:
        response = client.get("/api/v1/publications/")
    assert response.status_code == 200
    assert len(response.data["results"]) >= 8
    # Deliberately loose regression guard: this should catch row-by-row N+1
    # behavior while allowing a few constant prefetch/annotation queries.
    assert len(captured) <= 18, [query["sql"] for query in captured]
