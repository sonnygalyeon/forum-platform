from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
)


class IsPublicationAuthorOrReadOnly(
    BasePermission
):
    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and request.user.pk == obj.author_id
        )