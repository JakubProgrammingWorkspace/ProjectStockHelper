import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.models.tickers_models import Ticker

logger = logging.getLogger(__name__)

DEFAULT_LOOKBACK_YEARS = 10


class BaseHistoricalPricesService(ABC):
    """
    Abstract base class for fetching and persisting historical stock prices.

    Subclasses implement provider-specific ticker selection, API fetching,
    and response parsing. The shared orchestration loop, date-range
    calculation, incremental-fetch logic, and bulk-save live here.
    """

    LOG_PREFIX = "[Historical Prices]"

    def _get_tickers_to_process(self) -> list[str]:
        """
        Return an ordered list of active ticker symbols to fetch data for.

        Returns:
            List of ticker symbol strings.
        """
        return list(
            Ticker.objects.filter(
                status=Ticker.ACTIVE,
            )
            .order_by("ticker")
            .values_list("ticker", flat=True)
        )

    @abstractmethod
    def _fetch_raw_price_data(self, ticker_symbol: str, start_date: date, end_date: date) -> list | None:
        """
        Fetch raw price data from the external provider for a single ticker.

        The caller has already narrowed ``start_date`` based on existing
        database records; implementations should use the dates as-is.

        Args:
            ticker_symbol: Symbol to fetch.
            start_date: Inclusive start of the date window (already adjusted
                        for incremental fetching).
            end_date: Inclusive end of the date window.

        Returns:
            Provider-specific raw data (list of dicts, DataFrame rows, etc.).
            Return an empty list when no data is available.
        """

    @abstractmethod
    def _parse_and_build_model_instances(self, raw_data: list, ticker_symbol: str) -> list[HistoricalStockPrice]:
        """
        Convert raw provider data into HistoricalStockPrice model instances.

        Args:
            raw_data: Raw data returned by ``_fetch_raw_price_data``.
            ticker_symbol: The ticker these records belong to.

        Returns:
            List of unsaved HistoricalStockPrice instances.
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_date_range(lookback_years: int = DEFAULT_LOOKBACK_YEARS) -> tuple[date, date]:
        """Return (start_date, end_date) covering the last ``lookback_years`` years up to yesterday."""
        today = date.today()
        # If Monday (0), target is Friday (-3). If Sunday (6), target is Friday (-2).
        if today.weekday() == 0:
            end_date = today - timedelta(days=3)
        elif today.weekday() == 6:
            end_date = today - timedelta(days=2)
        else:
            end_date = today - timedelta(days=1)
        try:
            start_date = end_date.replace(year=end_date.year - lookback_years)
        except ValueError:
            # Handle Feb 29 edge case when the target year is not a leap year
            start_date = end_date.replace(year=end_date.year - lookback_years, day=end_date.day - 1)
        return start_date, end_date

    @staticmethod
    def _is_ticker_up_to_date(ticker_symbol: str, end_date: date) -> bool:
        """Check if the latest record for ticker already covers the end_date."""
        latest_record = (
            HistoricalStockPrice.objects.filter(ticker=ticker_symbol)
            .order_by("-date")
            .values_list("date", flat=True)
            .first()
        )
        return latest_record is not None and latest_record >= end_date

    @staticmethod
    def _get_incremental_start_date(ticker_symbol: str, default_start: date) -> date:
        """
        Calculate the start date for incremental fetch based on latest existing record.

        Returns:
            - ``latest_record.date + 1 day`` when partial data exists.
            - *default_start* when no data exists at all.
        """
        latest_record = (
            HistoricalStockPrice.objects.filter(ticker=ticker_symbol)
            .order_by("-date")
            .values_list("date", flat=True)
            .first()
        )

        if latest_record is None:
            return default_start

        incremental_start = latest_record + timedelta(days=1)
        return max(incremental_start, default_start)

    def _save_records_to_database(self, records: list[HistoricalStockPrice]) -> int:
        """
        Persist a batch of HistoricalStockPrice records using bulk upsert.

        Args:
            records: List of unsaved HistoricalStockPrice instances.

        Returns:
            Number of records written.
        """
        if not records:
            return 0

        HistoricalStockPrice.objects.bulk_create(
            records,
            update_conflicts=True,
            unique_fields=["ticker", "date"],
            update_fields=[
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "volume",
            ],
        )
        return len(records)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fetch_and_save_ticker_prices(
        self,
        ticker_symbol: str,
        incremental: bool = False,
        lookback_years: int = DEFAULT_LOOKBACK_YEARS,
    ) -> int:
        """
        Fetch and save historical prices for a single ticker.

        Args:
            ticker_symbol: The ticker symbol string to refresh.
            incremental: If True, only fetches missing days since the latest
                         stored record. If False (default), fetches the full
                         ``lookback_years`` window and overrides existing data.
            lookback_years: Size of the history window in years (default 10).

        Returns:
            Number of records saved.
        """
        start_date, end_date = self._default_date_range(lookback_years)

        if incremental:
            if self._is_ticker_up_to_date(ticker_symbol, end_date):
                logger.info(
                    "%s Ticker %s is already up-to-date (data for yesterday exists). Skipping.",
                    self.LOG_PREFIX,
                    ticker_symbol,
                )
                return 0
            start_date = self._get_incremental_start_date(ticker_symbol, start_date)

        raw_data = self._fetch_raw_price_data(ticker_symbol, start_date, end_date)
        if not raw_data:
            return 0

        records = self._parse_and_build_model_instances(raw_data, ticker_symbol)
        return self._save_records_to_database(records)

    def fetch_and_persist_historical_prices(self, incremental: bool = False) -> int:
        """
        Orchestrate the full fetch-parse-save flow for all applicable tickers.

        Args:
            incremental: If True, uses incremental fetching per ticker.
                         If False (default), performs a full override.

        Returns:
            Total number of records saved across all tickers.
        """
        tickers = self._get_tickers_to_process()

        logger.info(
            "%s Starting fetch for %d tickers (Mode: %s)",
            self.LOG_PREFIX,
            len(tickers),
            "Incremental" if incremental else "Override",
        )

        total_saved = 0

        for ticker_symbol in tickers:
            try:
                saved_count = self.fetch_and_save_ticker_prices(
                    ticker_symbol,
                    incremental=incremental,
                )
                total_saved += saved_count

                if saved_count:
                    logger.info(
                        "%s Saved %d records for %s",
                        self.LOG_PREFIX,
                        saved_count,
                        ticker_symbol,
                    )
            except Exception:
                logger.exception(
                    "%s Error processing %s",
                    self.LOG_PREFIX,
                    ticker_symbol,
                )

        logger.info(
            "%s Completed — total records saved: %d",
            self.LOG_PREFIX,
            total_saved,
        )
        return total_saved
