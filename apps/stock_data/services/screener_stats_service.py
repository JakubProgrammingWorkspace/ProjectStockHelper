import logging

from apps.stock_data.models import StockScreenerStats
from apps.stock_data.repositories import ScreenerStatsRepository

LOG_PREFIX = "[Screener Stats]"
logger = logging.getLogger(__name__)


class ScreenerStatsService:
    """
    Service for calculating and updating stock screener statistics.
    Orchestrates between the repository (data access) and business logic.
    """

    def __init__(self, repository: ScreenerStatsRepository):
        self._repository = repository

    def update_stats(self) -> int:
        """
        Calculates stats for all tickers and persists to the StockScreenerStats table.
        Should be triggered daily via cron after price fetching is complete.

        Returns:
            int: Number of tickers updated.
        """
        raw_rows = self._repository.fetch_raw_ticker_stats()
        stats_instances = [self._build_stats_instance(row) for row in raw_rows]
        saved_count = self._repository.replace_all_stats(stats_instances)

        logger.info("%s Successfully updated stats for %d tickers", LOG_PREFIX, saved_count)
        return saved_count

    def _build_stats_instance(self, row: dict) -> StockScreenerStats:
        """
        Transforms a raw DB row dict into a StockScreenerStats model instance.
        """
        latest_close = float(row["latest_close"])
        stats = {
            "latest_close": latest_close,
            "high_52w": float(row["high_52w"]),
            "low_52w": float(row["low_52w"]),
        }

        if latest_close > 0:
            for d in range(1, 6):
                past = row.get(f"close_rn{1 + d}")
                if past and float(past) > 0:
                    pct = ((latest_close / float(past)) - 1.0) * 100
                    stats[f"chg_{d}d_pct"] = round(pct, 2)

        return StockScreenerStats(
            ticker=row["ticker"],
            company_name=row["company_name"],
            stats=stats,
        )
