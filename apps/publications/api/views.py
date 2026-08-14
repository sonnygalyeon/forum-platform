from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from apps.publications.models import Publication, PublicationRevision
from apps.publications.permissions import IsPublicationAuthorOrReadOnly
from apps.publications.selectors import publication_queryset
from apps.publications.services import create_publication, update_publication
from .serializers import PublicationCreateSerializer, PublicationDetailSerializer, PublicationListSerializer, PublicationUpdateSerializer, RevisionDetailSerializer, RevisionListSerializer

class PublicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        queryset = publication_queryset()
        publication_type = self.request.query_params.get("type")
        community_id = self.request.query_params.get("community")
        author_id = self.request.query_params.get("author")
        tag = self.request.query_params.get("tag")
        if publication_type:
            queryset = queryset.filter(kind=publication_type)
        if community_id:
            queryset = queryset.filter(community__public_id=community_id)
        if author_id:
            queryset = queryset.filter(author__public_id=author_id)
        if tag:
            queryset = queryset.filter(tags__slug__iexact=tag)
        return queryset.distinct()
    def get_serializer_class(self):
        return PublicationCreateSerializer if self.request.method == "POST" else PublicationListSerializer
    def create(self, request, *args, **kwargs):
        serializer = PublicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        publication = create_publication(
            author=request.user, kind=data["type"], title=data["title"], content=data["content"],
            community=data["community"], tag_names=data["tags"],
        )
        publication = publication_queryset().get(pk=publication.pk)
        return Response(PublicationDetailSerializer(publication, context={"request": request}).data, status=status.HTTP_201_CREATED)

class PublicationDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsPublicationAuthorOrReadOnly]
    lookup_field = "public_id"
    lookup_url_kwarg = "publication_id"
    def get_queryset(self):
        return publication_queryset()
    def get_serializer_class(self):
        return PublicationUpdateSerializer if self.request.method == "PATCH" else PublicationDetailSerializer
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    def patch(self, request, *args, **kwargs):
        publication = self.get_object()
        serializer = PublicationUpdateSerializer(data=request.data, partial=True, context={"publication": publication})
        serializer.is_valid(raise_exception=True)
        changes = dict(serializer.validated_data)
        if "tags" in changes:
            changes["tag_names"] = changes.pop("tags")
        publication = update_publication(publication=publication, editor=request.user, changes=changes)
        publication = publication_queryset().get(pk=publication.pk)
        return Response(PublicationDetailSerializer(publication, context={"request": request}).data)

class PublicationRevisionListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RevisionListSerializer
    def get_queryset(self):
        publication = get_object_or_404(Publication, public_id=self.kwargs["publication_id"], visibility=Publication.Visibility.PUBLISHED)
        return PublicationRevision.objects.filter(publication=publication).select_related("editor").order_by("-revision_number")

class PublicationRevisionDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RevisionDetailSerializer
    lookup_field = "revision_number"
    lookup_url_kwarg = "revision_number"
    def get_queryset(self):
        publication = get_object_or_404(Publication, public_id=self.kwargs["publication_id"], visibility=Publication.Visibility.PUBLISHED)
        return PublicationRevision.objects.filter(publication=publication).select_related("editor")
