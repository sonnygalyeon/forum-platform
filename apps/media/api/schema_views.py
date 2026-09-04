from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.media.api.views import UploadAbortView


@extend_schema_view(
    post=extend_schema(
        operation_id="media_upload_abort",
        request=None,
        responses={204: None},
    ),
)
class UploadAbortSchemaView(UploadAbortView):
    pass
