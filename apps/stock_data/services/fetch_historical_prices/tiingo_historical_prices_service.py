import logging
from datetime import date, datetime
from decimal import Decimal

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.tiingo_api_client import TiingoApiClient
from apps.stock_data.services.fetch_historical_prices.base_historical_prices_service import (
    BaseHistoricalPricesService,
)

logger = logging.getLogger(__name__)


class TiingoHistoricalPricesService(BaseHistoricalPricesService):
    """
    Fetch and persist historical stock prices from the Tiingo REST API.

    Saves all records to the shared ``HistoricalStockPrice`` model.
    """

    LOG_PREFIX = "[Tiingo Historical Prices]"

    ENDPOINT_TEMPLATE = "/tiingo/daily/{ticker}/prices"

    def __init__(self, api_client: TiingoApiClient) -> None:
        self.api_client = api_client

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def _fetch_raw_price_data(self, ticker_symbol: str, start_date: date, end_date: date) -> list | None:
        """
        Call the Tiingo daily prices endpoint for a single ticker.

        The base class has already narrowed the date window based on
        existing database records.
        """
        endpoint = self.ENDPOINT_TEMPLATE.format(ticker=ticker_symbol)
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
        }

        try:
            response = self.api_client.make_request(endpoint, params=params)
            data = response.json()
        except ApiClientError as e:
            logger.error("%s Transport error fetching data for %s: %s", self.LOG_PREFIX, ticker_symbol, e)
            return None
        except ValueError as e:
            logger.error("%s Failed to parse JSON for %s: %s", self.LOG_PREFIX, ticker_symbol, e)
            return None

        if not data:
            return None

        return data

    def _parse_and_build_model_instances(self, raw_data: list, ticker_symbol: str) -> list[HistoricalStockPrice]:
        """
        Parse Tiingo JSON rows into HistoricalStockPrice instances.

        Uses adjusted prices when available (adjClose, adjOpen, …).
        """
        records: list[HistoricalStockPrice] = []

        for row in raw_data:
            date_str = row.get("date")
            if not date_str:
                continue

            try:
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            except ValueError:
                logger.warning(
                    "%s Could not parse date %s for %s",
                    self.LOG_PREFIX,
                    date_str,
                    ticker_symbol,
                )
                continue

            close_price = self._get_price_with_fallback(row, "adjClose", "close")
            open_price = self._get_price_with_fallback(row, "adjOpen", "open")
            high_price = self._get_price_with_fallback(row, "adjHigh", "high")
            low_price = self._get_price_with_fallback(row, "adjLow", "low")

            if any(p is None for p in [close_price, open_price, high_price, low_price]):
                logger.warning(
                    "%s Missing price data for %s on %s",
                    self.LOG_PREFIX,
                    ticker_symbol,
                    date_str,
                )
                continue

            volume = self._get_price_with_fallback(row, "adjVolume", "volume")
            if volume is None:
                volume = 0

            records.append(
                HistoricalStockPrice(
                    date=date_obj,
                    open_price=Decimal(str(open_price)),
                    high_price=Decimal(str(high_price)),
                    low_price=Decimal(str(low_price)),
                    close_price=Decimal(str(close_price)),
                    volume=int(volume),
                    ticker=ticker_symbol,
                )
            )

        return records

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_price_with_fallback(self, row: dict, adj_key: str, raw_key: str):
        """Return the adjusted price if it exists, otherwise fall back to raw price."""
        val = row.get(adj_key)
        return val if val is not None else row.get(raw_key)
