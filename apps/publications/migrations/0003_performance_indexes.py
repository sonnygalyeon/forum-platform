from django.db import migrations, models


SEARCH_INDEX_SQL = """
CREATE INDEX publications_search_vector_gin_idx
ON publications_publication
USING GIN ((
    setweight(to_tsvector('simple'::regconfig, coalesce(title, '')), 'A') ||
    setweight(to_tsvector('simple'::regconfig, coalesce(content_text, '')), 'B')
));
"""


class Migration(migrations.Migration):
    dependencies = [
        ("publications", "0002_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(
                fields=["visibility", "-created_at", "-id"],
                name="pub_feed_cursor_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(
                fields=["community", "visibility", "-created_at", "-id"],
                name="pub_comm_feed_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(
                fields=["author", "visibility", "-created_at", "-id"],
                name="pub_author_feed_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(
                fields=["kind", "visibility", "-created_at", "-id"],
                name="pub_kind_feed_idx",
            ),
        ),
        migrations.RunSQL(
            sql=SEARCH_INDEX_SQL,
            reverse_sql="DROP INDEX IF EXISTS publications_search_vector_gin_idx;",
        ),
    ]
