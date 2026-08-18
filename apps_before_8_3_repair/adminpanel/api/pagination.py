from rest_framework.pagination import LimitOffsetPagination


class AdminLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 30
    max_limit = 100
