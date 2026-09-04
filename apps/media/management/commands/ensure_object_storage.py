from django.core.management.base import BaseCommand

from apps.media.storage import ensure_bucket


class Command(BaseCommand):
    help = "Ensure the configured S3/MinIO media bucket exists and optionally apply CORS."

    def handle(self, *args, **options):
        ensure_bucket()
        self.stdout.write(self.style.SUCCESS("Object storage is ready."))
