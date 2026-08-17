import django.db.models.deletion
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("communities", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="community",
            name="owner",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_communities", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name="community",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("slug"),
                name="communities_slug_case_insensitive_unique",
            ),
        ),
    ]
