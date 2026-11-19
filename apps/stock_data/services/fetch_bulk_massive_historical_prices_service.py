import logging
from datetime import date, timedelta
from decimal import Decimal

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.massive_api_client import MassiveApiClient

LOG_PREFIX = "[Fetch Bulk Massive Prices]"
logger = logging.getLogger(__name__)


class FetchBulkMassiveHistoricalPricesService:
    """
    Service class for fetching and saving historical stock prices from Massive API.
    """

    def __init__(self, api_client: MassiveApiClient):
        self.api_client = api_client

    def bulk_save(self, records_to_save):
        """
        Save records in bulk to the database.

        Args:
            records_to_save (list): List of HistoricalStockPrice objects to save

        Returns:
            int: Number of records saved
        """
        logger.info("%s Saving %d records in batch mode...", LOG_PREFIX, len(records_to_save))

        # Use bulk_create with ignore_conflicts=True for PostgreSQL
        try:
            HistoricalStockPrice.objects.bulk_create(records_to_save, ignore_conflicts=True)
            saved_count = len(records_to_save)
        except Exception as e:
            logger.error("%s Error during batch save: %s", LOG_PREFIX, str(e))
            saved_count = 0

        return saved_count

    def fetch_massive_historical_prices_for_date(self, fetch_date):
        """
        Fetch historical stock prices from the API for a specific date.

        Args:
            fetch_date (date): Date for which to fetch data

        Returns:
            int: Number of records saved
        """
        endpoint = f"v2/aggs/grouped/locale/us/market/stocks/{fetch_date}"

        # Add query parameters
        params = {"adjusted": "true", "include_otc": "false"}

        # Make the API request
        try:
            response = self.api_client.make_request(endpoint, params=params)
            data = response.json()
        except ApiClientError as e:
            logger.error("%s Transport error fetching data for %s: %s", LOG_PREFIX, fetch_date, e)
            return 0
        except ValueError as e:
            logger.error("%s Failed to parse JSON for %s: %s", LOG_PREFIX, fetch_date, e)
            return 0

        if data.get("status") != "OK":
            logger.error("%s API returned status: %s for %s", LOG_PREFIX, data.get("status"), fetch_date)
            return 0

        # Get existing tickers to validate against
        active_tickers = set(Ticker.objects.active().values_list("ticker", flat=True))

        # Process results
        saved_count = 0
        records_to_save = []

        for result in data.get("results", []):
            ticker_symbol = result.get("T")

            # Skip if ticker not in our database or is inactive
            if ticker_symbol not in active_tickers:
                continue

            # Extract price information
            try:
                open_price = Decimal(str(result.get("o", 0)))
                high_price = Decimal(str(result.get("h", 0)))
                low_price = Decimal(str(result.get("l", 0)))
                close_price = Decimal(str(result.get("c", 0)))
                volume = result.get("v", 0)

                # Create record for batch save
                records_to_save.append(
                    HistoricalStockPrice(
                        ticker=ticker_symbol,
                        date=fetch_date,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        volume=volume,
                    )
                )

                # Increment saved count for each successful record
                saved_count += 1

            except Exception as e:
                logger.error("%s Error processing ticker %s: %s", LOG_PREFIX, ticker_symbol, str(e))
                continue

        # Batch save if we have records
        if records_to_save:
            saved_count = self.bulk_save(records_to_save)

        return saved_count

    def fetch_historical_data_for_range(self, start_date=None, end_date=None, all_range=False):
        """
        Fetch historical stock prices from the API for a specific date range.
        If all_range is True, fetches data for approximately the last year (excluding weekends).
        """
        if all_range:
            end_date = date.today()
            start_date = end_date - timedelta(days=360)  # About 1 year

        if not start_date or not end_date:
            raise ValueError("start_date and end_date must be provided if all_range is False")

        current_date = start_date
        total_saved = 0

        while current_date <= end_date:
            # Skip weekends (Saturday = 5, Sunday = 6)
            if current_date.weekday() < 5:  # Monday to Friday
                try:
                    logger.info("%s Fetching historical data for %s", LOG_PREFIX, current_date)

                    saved_count = self.fetch_massive_historical_prices_for_date(current_date)

                    logger.info("%s Successfully processed %d tickers for %s", LOG_PREFIX, saved_count, current_date)

                    total_saved += saved_count
                except Exception as e:
                    logger.error("%s Error fetching data for %s: %s", LOG_PREFIX, current_date, str(e))

            current_date += timedelta(days=1)

        return total_saved
