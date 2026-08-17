from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discussions.models import Comment, CommentRevision
from apps.discussions.selectors import comment_queryset
from apps.discussions.services import (
    accept_answer,
    create_reply,
    create_root_comment,
    remove_comment_vote,
    set_comment_vote,
    unaccept_answer,
    update_comment,
)
from apps.publications.models import Publication
from apps.users.models import User

from .serializers import (
    CommentCreateSerializer,
    CommentRevisionSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    CommentVoteSerializer,
    UserAnswerSerializer,
)


class PublicationCommentListCreateView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def get_queryset(self):
        publication = get_object_or_404(
            Publication,
            public_id=self.kwargs["publication_id"],
            visibility=Publication.Visibility.PUBLISHED,
        )
        return comment_queryset(self.request.user).filter(
            publication=publication,
            parent__isnull=True,
            visibility=Comment.Visibility.PUBLISHED,
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            self.permission_denied(request)

        input_serializer = CommentCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        publication = get_object_or_404(
            Publication,
            public_id=self.kwargs["publication_id"],
        )

        try:
            comment = create_root_comment(
                publication=publication,
                author=request.user,
                content=input_serializer.validated_data["content"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        comment = comment_queryset(request.user).get(pk=comment.pk)
        return Response(
            CommentSerializer(
                comment,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class CommentRepliesView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def get_parent(self):
        return get_object_or_404(
            Comment,
            public_id=self.kwargs["comment_id"],
            visibility=Comment.Visibility.PUBLISHED,
            publication__visibility=Publication.Visibility.PUBLISHED,
        )

    def get_queryset(self):
        parent = self.get_parent()
        return comment_queryset(self.request.user).filter(
            parent=parent,
            visibility=Comment.Visibility.PUBLISHED,
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            self.permission_denied(request)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent = self.get_parent()

        try:
            comment = create_reply(
                parent=parent,
                author=request.user,
                content=serializer.validated_data["content"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        comment = comment_queryset(request.user).get(pk=comment.pk)
        return Response(
            CommentSerializer(
                comment,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class CommentDetailView(APIView):
    permission_classes = [AllowAny]

    def get_comment(self, user=None):
        return get_object_or_404(
            comment_queryset(user),
            public_id=self.kwargs["comment_id"],
            visibility=Comment.Visibility.PUBLISHED,
            publication__visibility=Publication.Visibility.PUBLISHED,
        )

    def get(self, request, comment_id):
        comment = self.get_comment(request.user)
        return Response(
            CommentSerializer(
                comment,
                context={"request": request},
            ).data
        )

    def patch(self, request, comment_id):
        if not request.user.is_authenticated:
            self.permission_denied(request)

        comment = self.get_comment(request.user)
        serializer = CommentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = update_comment(
                comment=comment,
                editor=request.user,
                content=serializer.validated_data["content"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        comment = comment_queryset(request.user).get(pk=comment.pk)
        return Response(
            CommentSerializer(
                comment,
                context={"request": request},
            ).data
        )


class CommentVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_comment(self):
        return get_object_or_404(
            Comment,
            public_id=self.kwargs["comment_id"],
        )

    def put(self, request, comment_id):
        serializer = CommentVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = self.get_comment()

        try:
            comment, value = set_comment_vote(
                comment=comment,
                user=request.user,
                value=serializer.validated_data["value"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            {
                "score": comment.score,
                "my_vote": value,
            }
        )

    def delete(self, request, comment_id):
        comment = self.get_comment()

        try:
            comment = remove_comment_vote(
                comment=comment,
                user=request.user,
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            {
                "score": comment.score,
                "my_vote": None,
            }
        )


class CommentRevisionListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CommentRevisionSerializer

    def get_queryset(self):
        comment = get_object_or_404(
            Comment,
            public_id=self.kwargs["comment_id"],
            visibility=Comment.Visibility.PUBLISHED,
            publication__visibility=Publication.Visibility.PUBLISHED,
        )
        return (
            CommentRevision.objects
            .filter(comment=comment)
            .select_related("editor")
        )


class UserCommentsView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def get_queryset(self):
        user = get_object_or_404(
            User,
            public_id=self.kwargs["user_id"],
            is_active=True,
        )
        return comment_queryset(self.request.user).filter(
            author=user,
            visibility=Comment.Visibility.PUBLISHED,
            publication__visibility=Publication.Visibility.PUBLISHED,
        )

class CommentAcceptedView(APIView):
    permission_classes = [IsAuthenticated]

    def get_answer(self):
        return get_object_or_404(
            Comment,
            public_id=self.kwargs["comment_id"],
        )

    def put(self, request, comment_id):
        answer = self.get_answer()

        try:
            answer = accept_answer(
                answer=answer,
                actor=request.user,
            )
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        answer = comment_queryset(request.user).get(pk=answer.pk)
        return Response(
            CommentSerializer(
                answer,
                context={"request": request},
            ).data
        )

    def delete(self, request, comment_id):
        answer = self.get_answer()

        try:
            answer = unaccept_answer(
                answer=answer,
                actor=request.user,
            )
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        answer = comment_queryset(request.user).get(pk=answer.pk)
        return Response(
            CommentSerializer(
                answer,
                context={"request": request},
            ).data
        )


class PublicationAcceptedAnswerView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, publication_id):
        publication = get_object_or_404(
            Publication,
            public_id=publication_id,
            kind=Publication.Type.TOPIC,
            visibility=Publication.Visibility.PUBLISHED,
        )

        answer = (
            comment_queryset(request.user)
            .filter(
                publication=publication,
                kind=Comment.Kind.ANSWER,
                parent__isnull=True,
                is_accepted=True,
                visibility=Comment.Visibility.PUBLISHED,
            )
            .first()
        )

        if answer is None:
            return Response({"accepted_answer": None})

        return Response(
            {
                "accepted_answer": CommentSerializer(
                    answer,
                    context={"request": request},
                ).data
            }
        )


class UserAnswersView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserAnswerSerializer

    def get_queryset(self):
        user = get_object_or_404(
            User,
            public_id=self.kwargs["user_id"],
            is_active=True,
        )

        return comment_queryset(self.request.user).filter(
            author=user,
            kind=Comment.Kind.ANSWER,
            parent__isnull=True,
            visibility=Comment.Visibility.PUBLISHED,
            publication__kind=Publication.Type.TOPIC,
            publication__visibility=Publication.Visibility.PUBLISHED,
        )

