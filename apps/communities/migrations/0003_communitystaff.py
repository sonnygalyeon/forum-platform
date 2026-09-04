from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("communities", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunityStaff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("moderator", "Moderator"), ("editor", "Editor")], max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="community_staff_grants", to=settings.AUTH_USER_MODEL)),
                ("community", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="staff_edges", to="communities.community")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="community_staff_edges", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["role", "created_at", "id"],
                "indexes": [
                    models.Index(fields=["community", "role", "-created_at"], name="community_staff_role_idx"),
                    models.Index(fields=["user", "role"], name="community_staff_user_idx"),
                ],
                "constraints": [models.UniqueConstraint(fields=("community", "user"), name="community_unique_staff_user")],
            },
        ),
    ]
