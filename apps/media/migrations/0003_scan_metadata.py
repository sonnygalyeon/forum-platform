from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("media", "0002_publicationmedia")]

    operations = [
        migrations.AddField(
            model_name="mediaasset",
            name="scan_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="scan_detail",
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
