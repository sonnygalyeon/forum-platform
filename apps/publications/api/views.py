from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.publications.models import Publication, PublicationDraft, PublicationRevision
from apps.publications.permissions import IsPublicationAuthorOrReadOnly
from apps.publications.selectors import publication_queryset
from apps.publications.services import create_publication, update_publication
from .serializers import (
    PublicationCreateSerializer,
    PublicationDetailSerializer,
    PublicationDraftSerializer,
    PublicationListSerializer,
    PublicationUpdateSerializer,
    RevisionDetailSerializer,
    RevisionListSerializer,
)


class PublicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        author_id = self.request.query_params.get("author")
        queryset = publication_queryset(
            self.request.user,
            hide_muted=not bool(author_id),
        )
        publication_type = self.request.query_params.get("type")
        community_id = self.request.query_params.get("community")
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
        try:
            publication = create_publication(
                author=request.user,
                kind=data["type"],
                title=data["title"],
                content=data["content"],
                community=data["community"],
                tag_names=data["tags"],
            )
        except ValueError as exc:
            from rest_framework import serializers as drf_serializers

            raise drf_serializers.ValidationError({"content": str(exc)}) from exc
        publication = publication_queryset(request.user).get(pk=publication.pk)
        return Response(
            PublicationDetailSerializer(publication, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PublicationDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsPublicationAuthorOrReadOnly]
    lookup_field = "public_id"
    lookup_url_kwarg = "publication_id"

    def get_queryset(self):
        return publication_queryset(self.request.user)

    def get_serializer_class(self):
        return PublicationUpdateSerializer if self.request.method == "PATCH" else PublicationDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        publication = self.get_object()
        serializer = PublicationUpdateSerializer(
            data=request.data,
            partial=True,
            context={"publication": publication},
        )
        serializer.is_valid(raise_exception=True)
        changes = dict(serializer.validated_data)
        if "tags" in changes:
            changes["tag_names"] = changes.pop("tags")
        try:
            publication = update_publication(
                publication=publication,
                editor=request.user,
                changes=changes,
            )
        except ValueError as exc:
            from rest_framework import serializers as drf_serializers

            raise drf_serializers.ValidationError({"content": str(exc)}) from exc
        publication = publication_queryset(request.user).get(pk=publication.pk)
        return Response(PublicationDetailSerializer(publication, context={"request": request}).data)


class PublicationRevisionListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RevisionListSerializer

    def get_queryset(self):
        publication = get_object_or_404(
            Publication,
            public_id=self.kwargs["publication_id"],
            visibility=Publication.Visibility.PUBLISHED,
        )
        return PublicationRevision.objects.filter(publication=publication).select_related("editor").order_by("-revision_number")


class PublicationRevisionDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RevisionDetailSerializer
    lookup_field = "revision_number"
    lookup_url_kwarg = "revision_number"

    def get_queryset(self):
        publication = get_object_or_404(
            Publication,
            public_id=self.kwargs["publication_id"],
            visibility=Publication.Visibility.PUBLISHED,
        )
        return PublicationRevision.objects.filter(publication=publication).select_related("editor")


class PublicationDraftListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationDraftSerializer

    def get_queryset(self):
        return (
            PublicationDraft.objects.filter(owner=self.request.user)
            .select_related("community", "source_publication")
            .order_by("-updated_at", "-id")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PublicationDraftDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationDraftSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "draft_id"

    def get_queryset(self):
        return PublicationDraft.objects.filter(owner=self.request.user).select_related("community", "source_publication")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class PublicationDraftPublishView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: PublicationDetailSerializer, 201: PublicationDetailSerializer},
        summary="Publish a saved publication draft",
    )
    @transaction.atomic
    def post(self, request, draft_id):
        # Lock only the draft row. Both related FKs are nullable, so joining them
        # here would make PostgreSQL reject FOR UPDATE on the nullable side of
        # the LEFT JOIN. Related objects are loaded lazily inside this transaction.
        draft = get_object_or_404(
            PublicationDraft.objects.select_for_update(),
            public_id=draft_id,
            owner=request.user,
        )

        source = draft.source_publication
        if source is not None and source.author_id != request.user.pk:
            return Response({"detail": "Only the publication author can publish this edit draft."}, status=403)

        payload = {
            "type": source.kind if source is not None else draft.kind,
            "title": draft.title,
            "content": draft.content,
            "community_id": str(source.community.public_id) if source is not None and source.community else (str(draft.community.public_id) if draft.community else None),
            "tags": draft.tags,
        }
        create_serializer = PublicationCreateSerializer(data=payload)
        create_serializer.is_valid(raise_exception=True)
        data = create_serializer.validated_data

        try:
            if source is not None:
                publication = update_publication(
                    publication=source,
                    editor=request.user,
                    changes={
                        "title": data["title"],
                        "content": data["content"],
                        "tag_names": data["tags"],
                    },
                )
                response_status = status.HTTP_200_OK
            else:
                publication = create_publication(
                    author=request.user,
                    kind=data["type"],
                    title=data["title"],
                    content=data["content"],
                    community=data["community"],
                    tag_names=data["tags"],
                )
                response_status = status.HTTP_201_CREATED
        except ValueError as exc:
            from rest_framework import serializers as drf_serializers

            raise drf_serializers.ValidationError({"content": str(exc)}) from exc

        draft.delete()
        publication = publication_queryset(request.user).get(pk=publication.pk)
        return Response(
            PublicationDetailSerializer(publication, context={"request": request}).data,
            status=response_status,
        )
