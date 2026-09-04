from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Report PostgreSQL table/index activity for Night Iris hot-path tuning."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        limit = max(1, min(options["limit"], 100))
        if connection.vendor != "postgresql":
            self.stdout.write("database_performance_report is PostgreSQL-only")
            return

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT relname,
                       seq_scan,
                       idx_scan,
                       n_live_tup,
                       pg_total_relation_size(relid) AS total_bytes
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT %s
                """,
                [limit],
            )
            table_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT relname,
                       indexrelname,
                       idx_scan,
                       pg_relation_size(indexrelid) AS index_bytes
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC, pg_relation_size(indexrelid) DESC
                LIMIT %s
                """,
                [limit],
            )
            index_rows = cursor.fetchall()

        self.stdout.write("TABLES")
        self.stdout.write("name\tseq_scan\tidx_scan\tlive_rows\ttotal_bytes")
        for row in table_rows:
            self.stdout.write("\t".join(str(value) for value in row))

        self.stdout.write("\nINDEXES")
        self.stdout.write("table\tindex\tidx_scan\tindex_bytes")
        for row in index_rows:
            self.stdout.write("\t".join(str(value) for value in row))
