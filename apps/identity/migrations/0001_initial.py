import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("users", "0002_profile_media"),
    ]

    operations = [
        migrations.CreateModel(
            name="AvatarFrame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("slug", models.SlugField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("description", models.CharField(blank=True, max_length=240)),
                ("tier", models.CharField(choices=[("base", "Base"), ("rare", "Rare"), ("epic", "Epic"), ("legendary", "Legendary"), ("staff", "Staff")], default="base", max_length=16)),
                ("style_token", models.CharField(max_length=32)),
                ("unlock_type", models.CharField(choices=[("free", "Free"), ("reputation", "Reputation"), ("badge", "Badge"), ("staff", "Staff")], default="free", max_length=16)),
                ("unlock_value", models.PositiveIntegerField(default=0)),
                ("required_badge_slug", models.SlugField(blank=True, max_length=64)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["sort_order", "name"],
                "indexes": [models.Index(fields=["is_active", "sort_order"], name="identity_frame_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="Badge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("slug", models.SlugField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("description", models.CharField(blank=True, max_length=240)),
                ("tier", models.CharField(choices=[("base", "Base"), ("rare", "Rare"), ("epic", "Epic"), ("legendary", "Legendary"), ("staff", "Staff")], default="base", max_length=16)),
                ("icon_key", models.CharField(default="spark", max_length=32)),
                ("rule_type", models.CharField(choices=[("always", "Always"), ("reputation", "Reputation"), ("publications", "Publications"), ("answers", "Answers"), ("accepted", "Accepted answers"), ("followers", "Followers"), ("communities", "Owned communities"), ("staff", "Staff")], default="always", max_length=20)),
                ("threshold", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["sort_order", "name"],
                "indexes": [models.Index(fields=["is_active", "sort_order"], name="identity_badge_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="UserIdentityProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("accent", models.CharField(choices=[("emerald", "Emerald"), ("jade", "Jade"), ("ice", "Ice"), ("violet", "Violet")], default="emerald", max_length=16)),
                ("headline", models.CharField(blank=True, max_length=90)),
                ("reputation", models.PositiveIntegerField(default=0)),
                ("level", models.PositiveSmallIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("equipped_frame", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="equipped_profiles", to="identity.avatarframe")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="identity_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UserFrame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(blank=True, max_length=120)),
                ("unlocked_at", models.DateTimeField(auto_now_add=True)),
                ("frame", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="owners", to="identity.avatarframe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="identity_frames", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [models.Index(fields=["user", "-unlocked_at"], name="identity_user_frame_idx")],
                "constraints": [models.UniqueConstraint(fields=("user", "frame"), name="identity_unique_user_frame")],
            },
        ),
        migrations.CreateModel(
            name="UserBadge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pinned", models.BooleanField(default=False)),
                ("pin_order", models.PositiveSmallIntegerField(default=0)),
                ("source", models.CharField(blank=True, max_length=120)),
                ("awarded_at", models.DateTimeField(auto_now_add=True)),
                ("badge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="owners", to="identity.badge")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="identity_badges", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [models.Index(fields=["user", "pinned", "pin_order"], name="identity_user_badge_idx")],
                "constraints": [models.UniqueConstraint(fields=("user", "badge"), name="identity_unique_user_badge")],
            },
        ),
    ]
