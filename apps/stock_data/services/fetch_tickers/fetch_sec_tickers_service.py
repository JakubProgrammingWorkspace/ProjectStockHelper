import logging

from django.db import transaction
from django.utils import timezone

from apps.stock_data.models.tickers_models import SecTicker
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient

LOG_PREFIX = "[Fetch Sec Tickers]"
logger = logging.getLogger(__name__)


class FetchSecTickersService:
    """
    Service for fetching SEC company tickers and updating SecTicker model.
    """

    SEC_TICKER_ENDPOINT = "/files/company_tickers_exchange.json"
    EXCLUDED_EXCHANGES = {"OTC", "CBOE"}

    def __init__(self, api_client: SecApiClient):
        self.api_client = api_client

    def fetch_and_update_tickers(self) -> int:
        """
        Orchestrate fetching and updating SEC tickers.

        Returns:
            int: Number of tickers processed.
        """
        logger.info("%s Fetching ticker data from SEC...", LOG_PREFIX)

        try:
            response = self.api_client.make_request(self.SEC_TICKER_ENDPOINT)
            data = response.json()
        except ApiClientError as e:
            logger.error("%s Transport error fetching SEC tickers: %s", LOG_PREFIX, e)
            return 0
        except ValueError as e:
            logger.error("%s Failed to parse SEC tickers response: %s", LOG_PREFIX, e)
            return 0

        rows = data.get("data", [])
        if not rows:
            logger.warning("%s No ticker data found in SEC response", LOG_PREFIX)
            return 0

        ticker_instances = self._map_to_models(rows)
        if ticker_instances:
            count = self._save_to_db(ticker_instances)
            logger.info("%s Processed %d SEC tickers", LOG_PREFIX, count)
            return count

        return 0

    def _map_to_models(self, rows: list) -> list[SecTicker]:
        """Map raw SEC rows to SecTicker model instances."""
        ticker_instances = []
        today = timezone.now().date()

        for row in rows:
            try:
                cik, name, ticker, exchange = row
            except ValueError:
                logger.debug("%s Skipping malformed row: %s", LOG_PREFIX, row)
                continue

            # Skip invalid exchanges
            if exchange is None or exchange.strip().upper() in self.EXCLUDED_EXCHANGES:
                continue

            instance = SecTicker(
                cik=cik,
                name=name,
                ticker=ticker.strip().upper(),
                exchange=exchange.strip().upper(),
                status=SecTicker.ACTIVE,
                created=today,
            )
            ticker_instances.append(instance)

        return ticker_instances

    def _save_to_db(self, instances: list[SecTicker]) -> int:
        """Bulk update SEC tickers in database."""
        try:
            with transaction.atomic():
                logger.info("%s Setting all SEC tickers to inactive status...", LOG_PREFIX)
                SecTicker.objects.all().update(status=SecTicker.INACTIVE)

                result = SecTicker.objects.bulk_create(
                    instances,
                    update_conflicts=True,
                    unique_fields=["ticker"],
                    update_fields=["cik", "name", "exchange", "status", "created"],
                )
            return len(result)
        except Exception as e:
            logger.error("%s Failed to save SEC tickers to database: %s", LOG_PREFIX, e)
            raise
