from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.communities.models import Community


class UserFollow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_edges",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_edges",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="social_unique_user_follow",
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("following")),
                name="social_user_cannot_follow_self",
            ),
        ]
        indexes = [
            models.Index(fields=["follower", "-created_at"]),
            models.Index(fields=["following", "-created_at"]),
        ]


class CommunitySubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_subscriptions",
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "community"],
                name="social_unique_community_subscription",
            )
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["community", "-created_at"]),
        ]


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_user_edges",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by_edges",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "blocked"],
                name="social_unique_user_block",
            ),
            models.CheckConstraint(
                condition=~Q(blocker=F("blocked")),
                name="social_user_cannot_block_self",
            ),
        ]
        indexes = [
            models.Index(
                fields=["blocker", "-created_at"],
                name="social_block_blocker_idx",
            ),
            models.Index(
                fields=["blocked", "-created_at"],
                name="social_block_blocked_idx",
            ),
        ]


class UserMute(models.Model):
    muter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="muted_user_edges",
    )
    muted = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="muted_by_edges",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["muter", "muted"],
                name="social_unique_user_mute",
            ),
            models.CheckConstraint(
                condition=~Q(muter=F("muted")),
                name="social_user_cannot_mute_self",
            ),
        ]
        indexes = [
            models.Index(
                fields=["muter", "-created_at"],
                name="social_mute_muter_idx",
            ),
            models.Index(
                fields=["muted", "-created_at"],
                name="social_mute_muted_idx",
            ),
        ]
