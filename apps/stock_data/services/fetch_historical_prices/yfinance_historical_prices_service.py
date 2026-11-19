import logging
from datetime import date
from decimal import Decimal

import yfinance as yf

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.services.fetch_historical_prices.base_historical_prices_service import (
    BaseHistoricalPricesService,
)

logger = logging.getLogger(__name__)


class YFinanceHistoricalPricesService(BaseHistoricalPricesService):
    """
    Fetch and persist historical stock prices via the ``yfinance`` library.

    Saves all records to the shared ``HistoricalStockPrice`` model.
    """

    LOG_PREFIX = "[YFinance Historical Prices]"

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def _fetch_raw_price_data(self, ticker_symbol: str, start_date: date, end_date: date) -> list | None:
        """
        Download daily OHLCV data from Yahoo Finance for the specified range.
        """
        try:
            dataframe = yf.download(
                ticker_symbol,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )

            if dataframe.empty:
                return []

            # yfinance often returns MultiIndex columns (e.g., [('Close', 'AAPL'), ...])
            # even for a single ticker. Flatten it to just [('Close', ...)]
            if hasattr(dataframe.columns, "levels") and len(dataframe.columns.levels) > 1:
                dataframe.columns = dataframe.columns.get_level_values(0)

            # Convert to list of (Timestamp, Series) tuples for the parser
            return list(dataframe.iterrows())

        except Exception as download_error:
            logger.error(
                "%s YFinance download failed for %s (%s→%s): %s",
                self.LOG_PREFIX,
                ticker_symbol,
                start_date,
                end_date,
                download_error,
            )
            return None

    def _parse_and_build_model_instances(self, raw_data: list, ticker_symbol: str) -> list[HistoricalStockPrice]:
        """
        Convert ``(Timestamp, Series)`` tuples into HistoricalStockPrice
        instances.

        Accesses columns by name: Close, High, Low, Open, Volume.
        """
        records: list[HistoricalStockPrice] = []

        for timestamp, row in raw_data:
            try:
                if not all(self._is_valid_value(row[col]) for col in ["Close", "High", "Low", "Open"]):
                    continue

                # Volume is also checked, default to 0 if invalid
                volume_raw = self._get_scalar(row["Volume"])
                volume_str = str(volume_raw).lower()
                volume = int(float(volume_raw)) if volume_str not in ("nan", "none", "") else 0

                records.append(
                    HistoricalStockPrice(
                        ticker=ticker_symbol,
                        date=timestamp.date(),
                        close_price=Decimal(str(self._get_scalar(row["Close"]))),
                        high_price=Decimal(str(self._get_scalar(row["High"]))),
                        low_price=Decimal(str(self._get_scalar(row["Low"]))),
                        open_price=Decimal(str(self._get_scalar(row["Open"]))),
                        volume=volume,
                    )
                )
            except Exception as parse_error:
                logger.warning(
                    "%s Could not parse row for %s on %s: %s",
                    self.LOG_PREFIX,
                    ticker_symbol,
                    timestamp.date(),
                    parse_error,
                )

        return records

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_scalar(val):
        """Handle potential single-element Series (yfinance quirk)."""
        if hasattr(val, "iloc"):
            return val.iloc[0]
        return val

    def _is_valid_value(self, val) -> bool:
        """Check if a value is a valid numeric scalar (not NaN or None)."""
        scalar = self._get_scalar(val)
        s = str(scalar).lower()
        return s not in ("nan", "none", "")
