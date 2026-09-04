from django.urls import path

from apps.media.api.schema_views import UploadAbortSchemaView
from apps.media.api.views import (
    UploadCompleteView,
    UploadInitiateView,
    UploadPartsSignView,
)

urlpatterns = [
    path("uploads/initiate/", UploadInitiateView.as_view(), name="media-upload-initiate"),
    path("uploads/<uuid:asset_id>/parts/sign/", UploadPartsSignView.as_view(), name="media-upload-sign-parts"),
    path("uploads/<uuid:asset_id>/complete/", UploadCompleteView.as_view(), name="media-upload-complete"),
    path("uploads/<uuid:asset_id>/abort/", UploadAbortSchemaView.as_view(), name="media-upload-abort"),
]
