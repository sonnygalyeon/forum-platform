import uuid

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class Community(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    slug = models.SlugField(max_length=80)
    name = models.CharField(max_length=120)
    description = models.TextField(max_length=5000, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_communities")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(Lower("slug"), name="communities_slug_case_insensitive_unique")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class CommunityStaff(models.Model):
    class Role(models.TextChoices):
        MODERATOR = "moderator", "Moderator"
        EDITOR = "editor", "Editor"

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="staff_edges")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_staff_edges")
    role = models.CharField(max_length=16, choices=Role.choices)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="community_staff_grants")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["community", "user"], name="community_unique_staff_user"),
        ]
        indexes = [
            models.Index(fields=["community", "role", "-created_at"], name="community_staff_role_idx"),
            models.Index(fields=["user", "role"], name="community_staff_user_idx"),
        ]
        ordering = ["role", "created_at", "id"]

    def __str__(self):
        return f"{self.community.slug}:{self.user_id}:{self.role}"
