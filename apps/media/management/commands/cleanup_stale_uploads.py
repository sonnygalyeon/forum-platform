from datetime import timedelta

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.media.models import MediaAsset
from apps.media.storage import abort_multipart_upload


class Command(BaseCommand):
    help = "Abort stale multipart uploads tracked by Night Iris and mark them aborted."

    def add_arguments(self, parser):
        parser.add_argument("--older-than-hours", type=int, default=24)
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        hours = options["older_than_hours"]
        limit = options["limit"]
        if hours < 1:
            raise CommandError("--older-than-hours must be at least 1")
        if limit < 1 or limit > 5000:
            raise CommandError("--limit must be between 1 and 5000")

        cutoff = timezone.now() - timedelta(hours=hours)
        ids = list(
            MediaAsset.objects.filter(
                status=MediaAsset.Status.UPLOADING,
                created_at__lt=cutoff,
            )
            .order_by("created_at")
            .values_list("pk", flat=True)[:limit]
        )

        if options["dry_run"]:
            self.stdout.write(f"{len(ids)} stale uploads would be aborted.")
            return

        cleaned = 0
        failed = 0
        for asset_pk in ids:
            with transaction.atomic():
                asset = (
                    MediaAsset.objects.select_for_update()
                    .filter(pk=asset_pk, status=MediaAsset.Status.UPLOADING)
                    .first()
                )
                if asset is None:
                    continue
                try:
                    abort_multipart_upload(
                        object_key=asset.object_key,
                        upload_id=asset.upload_id,
                    )
                except ClientError as exc:
                    code = str(exc.response.get("Error", {}).get("Code", ""))
                    if code not in {"NoSuchUpload", "NoSuchKey", "404", "NotFound"}:
                        failed += 1
                        self.stderr.write(
                            f"Failed to abort {asset.public_id}: {code or exc.__class__.__name__}"
                        )
                        continue
                asset.status = MediaAsset.Status.ABORTED
                asset.upload_id = ""
                asset.completed_at = timezone.now()
                asset.save(update_fields=["status", "upload_id", "completed_at"])
                cleaned += 1

        self.stdout.write(
            self.style.SUCCESS(f"Aborted {cleaned} stale uploads; {failed} failed.")
        )
