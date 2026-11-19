import logging
from urllib.parse import parse_qs, urlparse

from django.db import transaction
from django.utils import timezone

from apps.stock_data.models.tickers_models import MassiveTicker
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.massive_api_client import MassiveApiClient

LOG_PREFIX = "[Fetch Massive Tickers]"
logger = logging.getLogger(__name__)


class FetchMassiveTickersService:
    """
    Service class for fetching and saving stock tickers from Massive API.
    """

    ENDPOINT_TICKERS = "v3/reference/tickers"

    EXCHANGES_MAPPER = {
        "BATS": "CBOE",
        "XASE": "NYSE American (AMEX)",
        "XNYS": "NYSE",
        "XNAS": "NASDAQ",
    }
    ACCEPTED_EXCHANGES = frozenset({"XNYS", "XNAS"})

    def __init__(self, api_client: MassiveApiClient):
        self.api_client = api_client

    def fetch_and_update_tickers(self) -> int:
        """
        Orchestrate fetching all tickers and saving them to the database.

        Returns:
            int: Number of tickers saved.
        """
        logger.info("%s Starting to fetch all tickers from Massive...", LOG_PREFIX)
        ticker_objects = self._fetch_all_tickers()

        if not ticker_objects:
            logger.warning("%s No tickers fetched — skipping database update", LOG_PREFIX)
            return 0

        count = self._save(ticker_objects)
        logger.info("%s Saved %d tickers to database", LOG_PREFIX, count)
        return count

    def _fetch_all_tickers(self) -> list[MassiveTicker]:
        endpoint = self.ENDPOINT_TICKERS
        params = {
            "type": "CS",
            "market": "stocks",
            "active": "true",
            "order": "asc",
            "limit": 1000,
            "sort": "ticker",
        }
        ticker_objects = []

        while endpoint:
            data = self._fetch_page(endpoint, params)
            if data is None:
                break

            results = data.get("results", [])
            if not results:
                logger.debug("%s No more results in page", LOG_PREFIX)
                break

            ticker_objects.extend(self._parse_results(results))

            next_url = data.get("next_url")
            if next_url:
                endpoint, params = self._parse_next_url(next_url)
            else:
                endpoint = None

        return ticker_objects

    def _fetch_page(self, endpoint: str, params: dict) -> dict | None:
        try:
            response = self.api_client.make_request(endpoint, params=params)
            return response.json()
        except ApiClientError as e:
            logger.error("%s Transport error fetching endpoint %s: %s", LOG_PREFIX, endpoint, e)
            return None
        except ValueError as e:
            logger.error("%s Failed to parse JSON for endpoint %s: %s", LOG_PREFIX, endpoint, e)
            return None

    def _parse_results(self, results: list) -> list[MassiveTicker]:
        objects = []
        today = timezone.now().date()
        for item in results:
            if item.get("primary_exchange") not in self.ACCEPTED_EXCHANGES:
                continue
            objects.append(
                MassiveTicker(
                    ticker=item["ticker"],
                    name=item["name"],
                    cik=int(item["cik"]) if item.get("cik") else None,
                    exchange=self.EXCHANGES_MAPPER.get(item["primary_exchange"]),
                    status=MassiveTicker.ACTIVE,
                    created=today,
                )
            )
        return objects

    def _parse_next_url(self, next_url: str) -> tuple[str, dict]:
        """Extract endpoint path and query params from a full Massive next_url."""
        parsed = urlparse(next_url)
        endpoint = parsed.path.lstrip("/")
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        params.pop("apiKey", None)  # api_client injects the key automatically
        return endpoint, params

    def _save(self, ticker_objects: list[MassiveTicker]) -> int:
        try:
            with transaction.atomic():
                MassiveTicker.objects.all().update(status=MassiveTicker.INACTIVE)
                created = MassiveTicker.objects.bulk_create(
                    ticker_objects,
                    update_conflicts=True,
                    unique_fields=["ticker"],
                    update_fields=["cik", "name", "exchange", "status", "created"],
                )
            return len(created)
        except Exception as e:
            logger.error("%s Failed to save Massive tickers: %s", LOG_PREFIX, e)
            raise
