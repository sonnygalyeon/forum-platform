from django.urls import path
from .views import PublicationDetailView, PublicationListCreateView, PublicationRevisionDetailView, PublicationRevisionListView

urlpatterns = [
    path("publications/", PublicationListCreateView.as_view(), name="publication-list-create"),
    path("publications/<uuid:publication_id>/", PublicationDetailView.as_view(), name="publication-detail"),
    path("publications/<uuid:publication_id>/revisions/", PublicationRevisionListView.as_view(), name="publication-revisions"),
    path("publications/<uuid:publication_id>/revisions/<int:revision_number>/", PublicationRevisionDetailView.as_view(), name="publication-revision-detail"),
]
