from django.conf import settings
from django.db import migrations


def bootstrap(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    AvatarFrame = apps.get_model("identity", "AvatarFrame")
    Badge = apps.get_model("identity", "Badge")
    UserIdentityProfile = apps.get_model("identity", "UserIdentityProfile")
    UserFrame = apps.get_model("identity", "UserFrame")
    UserBadge = apps.get_model("identity", "UserBadge")

    default_frame = AvatarFrame.objects.filter(slug="iris-line").first()
    newcomer = Badge.objects.filter(slug="newcomer").first()
    for user in User.objects.all().iterator():
        profile, _ = UserIdentityProfile.objects.get_or_create(user_id=user.pk)
        if default_frame is not None:
            UserFrame.objects.get_or_create(
                user_id=user.pk,
                frame_id=default_frame.pk,
                defaults={"source": "migration:bootstrap"},
            )
            if profile.equipped_frame_id is None:
                profile.equipped_frame_id = default_frame.pk
                profile.save(update_fields=["equipped_frame"])
        if newcomer is not None:
            UserBadge.objects.get_or_create(
                user_id=user.pk,
                badge_id=newcomer.pk,
                defaults={"source": "migration:bootstrap"},
            )


def reverse_bootstrap(apps, schema_editor):
    # User-created customization should never be deleted on reverse.
    pass


class Migration(migrations.Migration):
    dependencies = [("identity", "0002_seed_catalog")]
    operations = [migrations.RunPython(bootstrap, reverse_bootstrap)]
