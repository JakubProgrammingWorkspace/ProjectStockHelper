import logging

from django.db import transaction
from django.utils.dateparse import parse_date

from apps.stock_data.constants.sec_constants import SEC_TAG_MAPPING
from apps.stock_data.models.sec_models import SecFinancialData
from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.fetch_sec_financial_data.process_sec_financial_data_service import (
    ProcessSecFinancialDataService,
)
from apps.stock_data.services.fetch_sec_financial_data.sec_filter_service import ProcessSecFinanceRecords

LOG_PREFIX = "[Fetch SEC Financial Data Service]"
logger = logging.getLogger(__name__)

SEC_API_ENDPOINT_TEMPLATE = "/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"


class FetchSecFinancialDataService:
    """Service class to handle fetching and processing SEC financial data."""

    def __init__(self, sec_api_client: SecApiClient):
        self.sec_api_client = sec_api_client
        self.processor = ProcessSecFinanceRecords()
        self.processing_service = ProcessSecFinancialDataService()

    def _process_single_ticker(self, ticker: Ticker):
        """Process financial data for a single ticker."""
        try:
            # Fetch data for each tag
            tags_to_fetch = list(SEC_TAG_MAPPING.keys())
            for tag in tags_to_fetch:
                financial_records = []

                endpoint = SEC_API_ENDPOINT_TEMPLATE.format(cik=ticker.formatted_cik, tag=tag)

                try:
                    response = self.sec_api_client.make_request(endpoint)
                except ApiClientError as e:
                    logger.error(
                        "%s Transport error fetching %s for CIK %s: %s", LOG_PREFIX, tag, ticker.formatted_cik, e
                    )
                    continue

                # Parse JSON response
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error("%s Failed to parse %s JSON for CIK %s: %s", LOG_PREFIX, tag, ticker.formatted_cik, e)
                    continue

                # Extract financial data points
                if "units" in data and "USD" in data["units"]:
                    for item in data["units"]["USD"]:
                        # Apply filtering logic
                        if not self.processor.filter_records(item):
                            continue
                        item = self.processor.add_missing_data(item)

                        sec_financial_object = SecFinancialData(
                            cik=ticker.cik,
                            start_date=item.get("start"),
                            end_date=item.get("end"),
                            value=int(float(item.get("val"))),
                            accession_number=item.get("accn").split("-")[-1],
                            fiscal_year=item.get("fy"),
                            fiscal_period=item.get("fp"),
                            form_type=item.get("form"),
                            filed_date=item.get("filed"),
                            tag_id=SEC_TAG_MAPPING[tag],  # Use the tag ID instead of full tag name
                        )
                        financial_records.append(sec_financial_object)

                # Sort records by filed_date ascending before saving
                financial_records.sort(key=lambda x: parse_date(x.end_date) if x.end_date else None)

                # Filter records by unique combination of end_date and fiscal_period
                filtered_financial_records = self.processor.filter_by_date(financial_records)

                # Calculate missing Q4 values
                q4_records = self.processor.calculate_missing_q4_values(filtered_financial_records)

                # Add the new records to our list
                filtered_financial_records.extend(q4_records)

                # Save records to database
                if filtered_financial_records:
                    with transaction.atomic():
                        SecFinancialData.objects.bulk_create(filtered_financial_records, ignore_conflicts=True)

            # After fetching all tags, process the data for TTM values
            self.processing_service.process_ticker(ticker.cik)

        except Exception as e:
            logger.error("%s Error processing ticker %s (CIK: %s): %s", LOG_PREFIX, ticker.ticker, ticker.cik, str(e))

    def refresh_ticker_data(self, ticker: Ticker):
        """Refresh SEC financial data for a single ticker."""
        self._process_single_ticker(ticker)

    def fetch_and_process_financial_data(self):
        """Fetch financial data from SEC API for active tickers."""
        # Get all ACTIVE Tickers with non-null CIK
        active_tickers = Ticker.objects.active()

        processed_count = 0

        for ticker in active_tickers:
            self._process_single_ticker(ticker)
            processed_count += 1

        return processed_count
