from django.core.management.base import BaseCommand

from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.fetch_sec_financial_data.fetch_sec_financial_data_service import (
    FetchSecFinancialDataService,
)


class Command(BaseCommand):
    help = "Fetch financial data from SEC API for active tickers"

    LOG_PREFIX = "[Fetch SEC Financial Data]"

    def handle(self, *args, **options):
        self.stdout.write(f"{self.LOG_PREFIX} Fetching financial data from SEC API...")

        sec_api_client = SecApiClient.from_env()
        service = FetchSecFinancialDataService(sec_api_client)
        processed_count = service.fetch_and_process_financial_data()

        self.stdout.write(self.style.SUCCESS(f"{self.LOG_PREFIX} Successfully processed {processed_count} tickers"))
