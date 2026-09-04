from django.core.management.base import BaseCommand

from apps.media.tasks import recover_pending_media_scans


class Command(BaseCommand):
    help = "Re-enqueue quarantined media assets that are still pending malware scanning."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200)

    def handle(self, *args, **options):
        count = recover_pending_media_scans(limit=max(1, options["limit"]))
        self.stdout.write(self.style.SUCCESS(f"Queued {count} pending media scan(s)."))
