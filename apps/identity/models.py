import uuid

from django.conf import settings
from django.db import models


class AvatarFrame(models.Model):
    class Tier(models.TextChoices):
        BASE = "base", "Base"
        RARE = "rare", "Rare"
        EPIC = "epic", "Epic"
        LEGENDARY = "legendary", "Legendary"
        STAFF = "staff", "Staff"

    class UnlockType(models.TextChoices):
        FREE = "free", "Free"
        REPUTATION = "reputation", "Reputation"
        BADGE = "badge", "Badge"
        STAFF = "staff", "Staff"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    tier = models.CharField(max_length=16, choices=Tier.choices, default=Tier.BASE)
    style_token = models.CharField(max_length=32)
    unlock_type = models.CharField(max_length=16, choices=UnlockType.choices, default=UnlockType.FREE)
    unlock_value = models.PositiveIntegerField(default=0)
    required_badge_slug = models.SlugField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "sort_order"], name="identity_frame_active_idx"),
        ]

    def __str__(self):
        return self.name


class Badge(models.Model):
    class Tier(models.TextChoices):
        BASE = "base", "Base"
        RARE = "rare", "Rare"
        EPIC = "epic", "Epic"
        LEGENDARY = "legendary", "Legendary"
        STAFF = "staff", "Staff"

    class RuleType(models.TextChoices):
        ALWAYS = "always", "Always"
        REPUTATION = "reputation", "Reputation"
        PUBLICATIONS = "publications", "Publications"
        ANSWERS = "answers", "Answers"
        ACCEPTED = "accepted", "Accepted answers"
        FOLLOWERS = "followers", "Followers"
        COMMUNITIES = "communities", "Owned communities"
        STAFF = "staff", "Staff"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    tier = models.CharField(max_length=16, choices=Tier.choices, default=Tier.BASE)
    icon_key = models.CharField(max_length=32, default="spark")
    rule_type = models.CharField(max_length=20, choices=RuleType.choices, default=RuleType.ALWAYS)
    threshold = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "sort_order"], name="identity_badge_active_idx"),
        ]

    def __str__(self):
        return self.name


class UserIdentityProfile(models.Model):
    class Accent(models.TextChoices):
        EMERALD = "emerald", "Emerald"
        JADE = "jade", "Jade"
        ICE = "ice", "Ice"
        VIOLET = "violet", "Violet"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity_profile",
    )
    equipped_frame = models.ForeignKey(
        AvatarFrame,
        on_delete=models.SET_NULL,
        related_name="equipped_profiles",
        null=True,
        blank=True,
    )
    accent = models.CharField(max_length=16, choices=Accent.choices, default=Accent.EMERALD)
    headline = models.CharField(max_length=90, blank=True)
    reputation = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Identity: {self.user.nickname}"


class UserFrame(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity_frames",
    )
    frame = models.ForeignKey(
        AvatarFrame,
        on_delete=models.CASCADE,
        related_name="owners",
    )
    source = models.CharField(max_length=120, blank=True)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "frame"], name="identity_unique_user_frame"),
        ]
        indexes = [
            models.Index(fields=["user", "-unlocked_at"], name="identity_user_frame_idx"),
        ]


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity_badges",
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="owners",
    )
    pinned = models.BooleanField(default=False)
    pin_order = models.PositiveSmallIntegerField(default=0)
    source = models.CharField(max_length=120, blank=True)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="identity_unique_user_badge"),
        ]
        indexes = [
            models.Index(fields=["user", "pinned", "pin_order"], name="identity_user_badge_idx"),
        ]
