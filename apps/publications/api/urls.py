from django.urls import path

from .views import (
    PublicationDetailView,
    PublicationDraftDetailView,
    PublicationDraftListCreateView,
    PublicationDraftPublishView,
    PublicationListCreateView,
    PublicationRevisionDetailView,
    PublicationRevisionListView,
)

urlpatterns = [
    path("publications/", PublicationListCreateView.as_view(), name="publication-list-create"),
    path("publications/<uuid:publication_id>/", PublicationDetailView.as_view(), name="publication-detail"),
    path("publications/<uuid:publication_id>/revisions/", PublicationRevisionListView.as_view(), name="publication-revisions"),
    path("publications/<uuid:publication_id>/revisions/<int:revision_number>/", PublicationRevisionDetailView.as_view(), name="publication-revision-detail"),
    path("publication-drafts/", PublicationDraftListCreateView.as_view(), name="publication-draft-list-create"),
    path("publication-drafts/<uuid:draft_id>/", PublicationDraftDetailView.as_view(), name="publication-draft-detail"),
    path("publication-drafts/<uuid:draft_id>/publish/", PublicationDraftPublishView.as_view(), name="publication-draft-publish"),
]
