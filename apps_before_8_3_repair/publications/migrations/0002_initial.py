import django.db.models.deletion
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("communities", "0001_initial"),
        ("publications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="author",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="publications", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="publication",
            name="community",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="publications", to="communities.community"),
        ),
        migrations.AddField(
            model_name="publicationrevision",
            name="editor",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="publication_revisions", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="publicationrevision",
            name="publication",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="revisions", to="publications.publication"),
        ),
        migrations.AddConstraint(
            model_name="tag",
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower("slug"), name="publications_tag_slug_ci_unique"),
        ),
        migrations.AddField(
            model_name="publication",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="publications", to="publications.tag"),
        ),
        migrations.AddConstraint(
            model_name="publicationrevision",
            constraint=models.UniqueConstraint(fields=("publication", "revision_number"), name="publication_unique_revision"),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(fields=["visibility", "-created_at"], name="publication_visibil_2e70ec_idx"),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(fields=["kind", "-created_at"], name="publication_kind_6e88f6_idx"),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(fields=["author", "-created_at"], name="publication_author__cbde3b_idx"),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(fields=["community", "-created_at"], name="publication_communi_0c5796_idx"),
        ),
    ]
