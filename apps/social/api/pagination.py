from rest_framework.pagination import CursorPagination


class PersonalizedFeedCursorPagination(CursorPagination):
    page_size = 20
    ordering = ("-feed_score", "-created_at", "-id")
