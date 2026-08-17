from rest_framework.throttling import UserRateThrottle


class AuthRateThrottle(UserRateThrottle):
    scope = "auth"


class UploadRateThrottle(UserRateThrottle):
    scope = "uploads"
