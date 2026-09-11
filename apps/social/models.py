from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.communities.models import Community
from apps.publications.models import Publication


class UserFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_edges")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_edges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="social_unique_user_follow"),
            models.CheckConstraint(condition=~Q(follower=F("following")), name="social_user_cannot_follow_self"),
        ]
        indexes = [
            models.Index(fields=["follower", "-created_at"]),
            models.Index(fields=["following", "-created_at"]),
        ]


class CommunitySubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_subscriptions")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "community"], name="social_unique_community_subscription")]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["community", "-created_at"]),
        ]


class UserBlock(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_user_edges")
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by_edges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="social_unique_user_block"),
            models.CheckConstraint(condition=~Q(blocker=F("blocked")), name="social_user_cannot_block_self"),
        ]
        indexes = [
            models.Index(fields=["blocker", "-created_at"], name="social_block_blocker_idx"),
            models.Index(fields=["blocked", "-created_at"], name="social_block_blocked_idx"),
        ]


class UserMute(models.Model):
    muter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="muted_user_edges")
    muted = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="muted_by_edges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["muter", "muted"], name="social_unique_user_mute"),
            models.CheckConstraint(condition=~Q(muter=F("muted")), name="social_user_cannot_mute_self"),
        ]
        indexes = [
            models.Index(fields=["muter", "-created_at"], name="social_mute_muter_idx"),
            models.Index(fields=["muted", "-created_at"], name="social_mute_muted_idx"),
        ]


class PublicationBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="publication_bookmarks")
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="bookmark_edges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "publication"], name="social_unique_publication_bookmark"),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at", "-id"], name="social_bookmark_user_idx"),
            models.Index(fields=["publication", "-created_at"], name="social_bookmark_pub_idx"),
        ]



class PublicationReaction(models.Model):
    class Kind(models.TextChoices):
        HEART = "heart", "Heart"
        INSIGHTFUL = "insightful", "Insightful"
        USEFUL = "useful", "Useful"
        CURIOUS = "curious", "Curious"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="publication_reactions",
    )
    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="reaction_edges",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "publication"],
                name="social_unique_publication_reaction",
            ),
        ]
        indexes = [
            models.Index(
                fields=["publication", "kind"],
                name="social_react_pub_kind_idx",
            ),
            models.Index(
                fields=["user", "-updated_at"],
                name="social_react_user_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user.nickname} -> {self.publication.public_id}: {self.kind}"
