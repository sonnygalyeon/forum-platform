from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("publications", "0003_performance_indexes"),
        ("social", "0002_userblock_usermute"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationBookmark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookmark_edges", to="publications.publication")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="publication_bookmarks", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "-created_at", "-id"], name="social_bookmark_user_idx"),
                    models.Index(fields=["publication", "-created_at"], name="social_bookmark_pub_idx"),
                ],
                "constraints": [models.UniqueConstraint(fields=("user", "publication"), name="social_unique_publication_bookmark")],
            },
        ),
    ]
