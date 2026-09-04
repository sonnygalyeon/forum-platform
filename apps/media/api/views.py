from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttling import UploadRateThrottle
from apps.media.api.serializers import MediaAssetSerializer, SignedPartsResponseSerializer, UploadCompleteSerializer, UploadInitiateSerializer, UploadPartNumbersSerializer
from apps.media.models import MediaAsset
from apps.media.storage import MAX_MULTIPART_PARTS, abort_multipart_upload, classify_kind, complete_multipart_upload, create_multipart_upload, delete_object, head_object, normalized_part_size, object_key_for, part_count_for_size, sign_upload_part
from apps.media.tasks import enqueue_media_scan


class UploadBaseView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UploadRateThrottle]

    def asset_for_user(self, request, asset_id):
        return get_object_or_404(MediaAsset, public_id=asset_id, owner=request.user)


class UploadInitiateView(UploadBaseView):
    @extend_schema(request=UploadInitiateSerializer, responses={201: MediaAssetSerializer})
    def post(self, request):
        serializer = UploadInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        part_count = part_count_for_size(data["size_bytes"])
        if part_count > MAX_MULTIPART_PARTS:
            return Response({"detail": "File requires too many multipart chunks."}, status=status.HTTP_400_BAD_REQUEST)
        asset = MediaAsset(owner=request.user, original_name=data["original_name"], declared_content_type=data["content_type"], kind=classify_kind(data["content_type"]), size_bytes=data["size_bytes"], part_size=normalized_part_size(), part_count=part_count, status=MediaAsset.Status.UPLOADING)
        asset.object_key = object_key_for(owner_public_id=request.user.public_id, asset_public_id=asset.public_id, original_name=asset.original_name)
        asset.upload_id = create_multipart_upload(object_key=asset.object_key, content_type=asset.declared_content_type)
        asset.save()
        return Response(MediaAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class UploadPartsSignView(UploadBaseView):
    @extend_schema(request=UploadPartNumbersSerializer, responses=SignedPartsResponseSerializer)
    def post(self, request, asset_id):
        asset = self.asset_for_user(request, asset_id)
        if asset.status != MediaAsset.Status.UPLOADING or not asset.upload_id:
            return Response({"detail": "Upload is no longer active."}, status=status.HTTP_409_CONFLICT)
        serializer = UploadPartNumbersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        part_numbers = serializer.validated_data["part_numbers"]
        if any(number > asset.part_count for number in part_numbers):
            return Response({"detail": "Part number is outside this upload."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"parts": [{"part_number": number, "url": sign_upload_part(object_key=asset.object_key, upload_id=asset.upload_id, part_number=number)} for number in part_numbers]})


class UploadCompleteView(UploadBaseView):
    @extend_schema(request=UploadCompleteSerializer, responses=MediaAssetSerializer)
    def post(self, request, asset_id):
        serializer = UploadCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parts = serializer.validated_data["parts"]
        with transaction.atomic():
            asset = get_object_or_404(MediaAsset.objects.select_for_update(), public_id=asset_id, owner=request.user)
            if asset.status in {MediaAsset.Status.READY, MediaAsset.Status.PENDING_SCAN}:
                return Response(MediaAssetSerializer(asset).data)
            if asset.status != MediaAsset.Status.UPLOADING or not asset.upload_id:
                return Response({"detail": "Upload is no longer active."}, status=status.HTTP_409_CONFLICT)
            expected_numbers = list(range(1, asset.part_count + 1))
            actual_numbers = [item["part_number"] for item in parts]
            if actual_numbers != expected_numbers:
                return Response({"detail": "Completed parts do not match the upload manifest."}, status=status.HTTP_400_BAD_REQUEST)
            complete_multipart_upload(object_key=asset.object_key, upload_id=asset.upload_id, parts=parts)
            actual_size = int(head_object(object_key=asset.object_key).get("ContentLength", -1))
            if actual_size != asset.size_bytes:
                delete_object(object_key=asset.object_key)
                asset.status = MediaAsset.Status.REJECTED
                asset.upload_id = ""
                asset.completed_at = timezone.now()
                asset.scan_detail = "size_mismatch"
                asset.save(update_fields=["status", "upload_id", "completed_at", "scan_detail"])
                return Response({"detail": "Uploaded object size does not match the declared size."}, status=status.HTTP_400_BAD_REQUEST)
            asset.status = MediaAsset.Status.PENDING_SCAN if settings.MEDIA_REQUIRE_SCAN else MediaAsset.Status.READY
            asset.upload_id = ""
            asset.completed_at = timezone.now()
            asset.save(update_fields=["status", "upload_id", "completed_at"])
            if asset.status == MediaAsset.Status.PENDING_SCAN:
                transaction.on_commit(lambda asset_id=asset.public_id: enqueue_media_scan(asset_id))
        return Response(MediaAssetSerializer(asset).data)


class UploadAbortView(UploadBaseView):
    @extend_schema(responses={204: None})
    def post(self, request, asset_id):
        with transaction.atomic():
            asset = get_object_or_404(MediaAsset.objects.select_for_update(), public_id=asset_id, owner=request.user)
            if asset.status == MediaAsset.Status.ABORTED:
                return Response(status=status.HTTP_204_NO_CONTENT)
            if asset.status != MediaAsset.Status.UPLOADING:
                return Response({"detail": "Only active uploads can be aborted."}, status=status.HTTP_409_CONFLICT)
            abort_multipart_upload(object_key=asset.object_key, upload_id=asset.upload_id)
            asset.status = MediaAsset.Status.ABORTED
            asset.upload_id = ""
            asset.completed_at = timezone.now()
            asset.save(update_fields=["status", "upload_id", "completed_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
