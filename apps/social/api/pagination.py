from rest_framework.pagination import CursorPagination, PageNumberPagination


class PersonalizedFeedCursorPagination(CursorPagination):
    page_size = 20
    ordering = ("-feed_score", "-created_at", "-id")


class SocialGraphPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
