from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0003_publicationbookmark"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationReaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("heart", "Heart"), ("insightful", "Insightful"), ("useful", "Useful"), ("curious", "Curious")], max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reaction_edges", to="publications.publication")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="publication_reactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["publication", "kind"], name="social_react_pub_kind_idx"),
                    models.Index(fields=["user", "-updated_at"], name="social_react_user_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("user", "publication"), name="social_unique_publication_reaction"),
                ],
            },
        ),
    ]
