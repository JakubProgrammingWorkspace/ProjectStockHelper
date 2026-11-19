from django.core.management.base import BaseCommand

from apps.stock_data.services.api_clients.tiingo_api_client import TiingoApiClient
from apps.stock_data.services.fetch_historical_prices import (
    BaseHistoricalPricesService,
    TiingoHistoricalPricesService,
    YFinanceHistoricalPricesService,
)


class Command(BaseCommand):
    """
    Fetch historical stock prices from a selected data source.

    Usage examples::

        # Full sync (default): Process 10 years of data and override existing records
        manage.py fetch_historical_prices --source tiingo
        manage.py fetch_historical_prices --source yfinance

        # Quick sync (incremental): Only fetch missing data since the last stored record
        manage.py fetch_historical_prices --source tiingo --incremental
        manage.py fetch_historical_prices --source yfinance --incremental
    """

    help = "Fetch historical stock prices from a selected data source"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            choices=["tiingo", "yfinance"],
            required=True,
            help="Data source to fetch from: tiingo, or yfinance",
        )
        parser.add_argument(
            "--incremental",
            action="store_true",
            help="Only fetch missing data (incremental). Default is full override.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        incremental = options["incremental"]
        service = self._build_service(source)
        total_saved = service.fetch_and_persist_historical_prices(incremental=incremental)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully completed fetch from {source}. Total records saved: {total_saved}")
        )

    def _build_service(self, source: str) -> BaseHistoricalPricesService:
        """Instantiate the appropriate service for the requested source."""
        match source:
            case "tiingo":
                api_client = TiingoApiClient.from_env()
                return TiingoHistoricalPricesService(api_client=api_client)

            case "yfinance":
                return YFinanceHistoricalPricesService()

            case _:
                # This should be unreachable due to argparse choices
                raise ValueError(f"Unknown source: {source}")
