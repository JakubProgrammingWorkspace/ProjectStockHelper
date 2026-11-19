from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.stock_data.services.api_clients.massive_api_client import MassiveApiClient
from apps.stock_data.services.fetch_bulk_massive_historical_prices_service import (
    FetchBulkMassiveHistoricalPricesService,
)


class Command(BaseCommand):
    """
    Management command to fetch and save massive amounts of historical stock prices.

    This command retrieves daily price data for all tickers in the Ticker model
    and stores it in the HistoricalStockPrice model. It only fetches data starting
    from the latest date already present in the database to avoid duplicates.
    """

    help = "Fetch bulk historical stock prices"

    LOG_PREFIX = "[Fetch Bulk Historical Prices]"

    def add_arguments(self, parser):
        parser.add_argument(
            "date",
            nargs="?",
            type=str,
            default=None,
            help="Date for which to fetch data (YYYY-MM-DD format). Defaults to yesterday.",
        )
        parser.add_argument(
            "--all_range",
            action="store_true",
            default=False,
            help="Fetch data for the last two years (excluding weekends)",
        )

    def handle(self, *args, **options):
        # Create service instance
        service = FetchBulkMassiveHistoricalPricesService(api_client=MassiveApiClient.from_env())

        # Check if all_range flag is set
        if options.get("all_range"):
            self.stdout.write(
                f"{self.LOG_PREFIX} Fetching bulk historical prices for all range. Check logs for details."
            )
            service.fetch_historical_data_for_range(all_range=True)
            self.stdout.write(
                self.style.SUCCESS(f"{self.LOG_PREFIX} Completed fetching bulk historical prices for all range.")
            )
        else:
            # Fetch data for a specific date or yesterday
            if options.get("date"):
                fetch_date = date.fromisoformat(options["date"])
            else:
                # Default to yesterday's date
                fetch_date = date.today() - timedelta(days=1)

            date_str = fetch_date.strftime("%Y-%m-%d")
            self.stdout.write(f"{self.LOG_PREFIX} Fetching bulk historical prices for {date_str}")

            try:
                saved_count = service.fetch_massive_historical_prices_for_date(fetch_date)
                self.stdout.write(
                    self.style.SUCCESS(f"{self.LOG_PREFIX} Successfully processed {saved_count} tickers for {date_str}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"{self.LOG_PREFIX} Error fetching data: {str(e)}"))
