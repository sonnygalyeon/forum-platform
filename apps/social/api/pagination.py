import base64

from rest_framework.exceptions import NotFound
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param


class PersonalizedFeedCursorPagination(CursorPagination):
    page_size = 20
    ordering = ("-feed_score", "-created_at", "-id")


class QualityFeedCursorPagination(PageNumberPagination):
    """Opaque page cursor for an in-memory deterministic reranked candidate list.

    Response shape remains cursor-compatible: next, previous, results.
    """

    page_size = 20
    page_query_param = "cursor"
    page_size_query_param = "page_size"
    max_page_size = 50

    def _encode_page(self, page_number):
        token = f"p:{page_number}".encode("utf-8")
        return base64.urlsafe_b64encode(token).decode("ascii").rstrip("=")

    def _decode_page(self, token):
        try:
            padded = token + "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            prefix, raw_page = decoded.split(":", 1)
            if prefix != "p":
                raise ValueError
            page_number = int(raw_page)
            if page_number < 1:
                raise ValueError
            return page_number
        except (ValueError, UnicodeDecodeError, base64.binascii.Error) as exc:
            raise NotFound("Invalid feed cursor.") from exc

    def get_page_number(self, request, paginator):
        token = request.query_params.get(self.page_query_param)
        if not token:
            return 1
        return self._decode_page(token)

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = self.request.build_absolute_uri()
        return replace_query_param(
            url,
            self.page_query_param,
            self._encode_page(self.page.next_page_number()),
        )

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        previous = self.page.previous_page_number()
        if previous == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(
            url,
            self.page_query_param,
            self._encode_page(previous),
        )

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["results"],
            "properties": {
                "next": {
                    "type": ["string", "null"],
                    "format": "uri",
                },
                "previous": {
                    "type": ["string", "null"],
                    "format": "uri",
                },
                "results": schema,
            },
        }

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": self.page_query_param,
                "required": False,
                "in": "query",
                "description": "Opaque feed cursor.",
                "schema": {"type": "string"},
            },
            {
                "name": self.page_size_query_param,
                "required": False,
                "in": "query",
                "description": "Number of feed items per page (max 50).",
                "schema": {"type": "integer", "minimum": 1, "maximum": self.max_page_size},
            },
        ]


class SocialGraphPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
