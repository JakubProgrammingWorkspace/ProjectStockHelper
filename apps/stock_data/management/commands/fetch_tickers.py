from django.core.management.base import BaseCommand

from apps.stock_data.services.api_clients.massive_api_client import MassiveApiClient
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.fetch_tickers.fetch_massive_tickers_service import FetchMassiveTickersService
from apps.stock_data.services.fetch_tickers.fetch_sec_tickers_service import FetchSecTickersService
from apps.stock_data.services.fetch_tickers.process_tickers_service import ProcessTickersService


class Command(BaseCommand):
    help = "Fetch or process stock tickers from various sources"

    LOG_PREFIX = "[Fetch Tickers]"

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            type=str,
            choices=["sec_tickers", "massive_tickers", "process_tickers"],
            help="The source or process to execute",
        )

    def handle(self, *args, **options):
        source = options["source"]
        self.stdout.write(f"{self.LOG_PREFIX} Starting {source}...")

        try:
            if source == "sec_tickers":
                api_client = SecApiClient.from_env("SEC_WWW_BASE_URL")
                count = FetchSecTickersService(api_client=api_client).fetch_and_update_tickers()
                self.stdout.write(self.style.SUCCESS(f"{self.LOG_PREFIX} Successfully processed {count} SEC tickers"))


            elif source == "massive_tickers":
                api_client = MassiveApiClient.from_env()
                count = FetchMassiveTickersService(api_client=api_client).fetch_and_update_tickers()
                msg = f"{self.LOG_PREFIX} Successfully processed {count} massive tickers"
                self.stdout.write(self.style.SUCCESS(msg))

            elif source == "process_tickers":
                ProcessTickersService().process_all_tickers()
                self.stdout.write(self.style.SUCCESS(f"{self.LOG_PREFIX} Ticker processing completed successfully"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"{self.LOG_PREFIX} Command failed: {e}"))
            raise SystemExit(1) from e
