from django.core.management.base import BaseCommand

from apps.stock_data.repositories import ScreenerStatsRepository
from apps.stock_data.services.screener_stats_service import ScreenerStatsService


class Command(BaseCommand):
    help = "Updates the StockScreenerStats table with latest metrics"

    def handle(self, *args, **options):
        prefix = "[SCREENER_STATS]"
        self.stdout.write(f"{prefix} Starting stats update...")
        try:
            repository = ScreenerStatsRepository()
            service = ScreenerStatsService(repository=repository)
            service.update_stats()
            self.stdout.write(self.style.SUCCESS(f"{prefix} Successfully updated screener stats"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"{prefix} Failed to update screener stats: {e}"))
