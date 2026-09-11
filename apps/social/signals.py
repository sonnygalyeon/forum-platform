from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.discussions.models import Comment
from apps.social.models import PublicationBookmark, PublicationReaction
from apps.social.realtime import publish_publication_engagement_changed


@receiver([post_save, post_delete], sender=PublicationReaction)
def publication_reaction_changed(sender, instance, **kwargs):
    publish_publication_engagement_changed(
        publication_public_id=instance.publication.public_id,
        reason="reaction",
    )


@receiver([post_save, post_delete], sender=PublicationBookmark)
def publication_bookmark_changed(sender, instance, **kwargs):
    publish_publication_engagement_changed(
        publication_public_id=instance.publication.public_id,
        reason="bookmark",
    )


@receiver([post_save, post_delete], sender=Comment)
def publication_comment_changed(sender, instance, **kwargs):
    publish_publication_engagement_changed(
        publication_public_id=instance.publication.public_id,
        reason="comment",
    )
