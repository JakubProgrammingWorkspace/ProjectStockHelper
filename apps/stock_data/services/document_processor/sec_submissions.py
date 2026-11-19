import logging
from dataclasses import dataclass
from datetime import datetime

from dateutil.relativedelta import relativedelta

from apps.stock_data.constants.sec_constants import FormType
from apps.stock_data.dto.sec_submission_dto import SecSubmissionDTO
from apps.stock_data.models.tickers_models import SecTicker
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient

SEC_API_ENDPOINT_TEMPLATE = "/submissions/CIK{cik}.json"

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    """Value object representing a date range for SEC submission filtering."""

    start_date: datetime | None
    end_date: datetime | None

    @classmethod
    def from_days(cls, days_from: int | None = None, days_to: int | None = None):

        today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        start_date = today_midnight - relativedelta(days=days_from) if days_from is not None else None
        end_date = today_midnight - relativedelta(days=days_to) if days_to is not None else None

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be later than end_date")

        return cls(start_date, end_date)

    @classmethod
    def from_date_strings(cls, start_date_str: str | None = None, end_date_str: str | None = None):
        """
        Create a DateRange from date strings in 'YYYY-MM-DD' format.

        Args:
            start_date_str: Start date as string in 'YYYY-MM-DD' format
            end_date_str: End date as string in 'YYYY-MM-DD' format

        Returns:
            DateRange instance

        Raises:
            ValueError: If date strings are invalid or start_date is after end_date
        """
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Invalid start_date format: {start_date_str}. Expected 'YYYY-MM-DD'") from e

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Invalid end_date format: {end_date_str}. Expected 'YYYY-MM-DD'") from e

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be later than end_date")

        return cls(start_date, end_date)


class SecSubmissions:
    """
    Service to find and load SEC submissions of a specific type.
    """

    VALID_FORMS = {
        FormType.FORM_8_K,
        FormType.FORM_10_Q,
        FormType.FORM_10_K,
        FormType.FORM_20_F,
        FormType.FORM_6_K,
    }

    def __init__(
        self,
        sec_api_client: SecApiClient,
        form_type: str,
        max_results: int = 0,
        items: list[str] | None = None,
        date_range: DateRange | None = None,
    ):
        if form_type not in self.VALID_FORMS:
            raise ValueError(f"Invalid form_type: {form_type}. Must be one of {self.VALID_FORMS}")

        self.sec_api_client = sec_api_client
        self.form_type = form_type
        self.max_results = max_results
        self.items = items if items is not None else []
        self.date_range = date_range

    def matches(self, form_name, results_count, row_items, raw_date):

        # 1. Check form type and results limit conditions
        if form_name != self.form_type:
            return False

        if self.max_results and results_count >= self.max_results:
            return False

        # 2. Check items condition
        if self.items:
            items_list = row_items.split(",")
            if not any(sub in items_list for sub in self.items):
                return False

        # 3. Check date condition
        if self.date_range:
            try:
                if not raw_date:
                    return False

                submission_date = datetime.strptime(raw_date, "%Y-%m-%d")

                # Check if submission date is within the specified range
                if self.date_range.start_date and submission_date < self.date_range.start_date:
                    return False

                if self.date_range.end_date and submission_date > self.date_range.end_date:
                    return False

            except (ValueError, TypeError):
                return False

        return True

    def find_submissions(self, ticker: SecTicker) -> list[SecSubmissionDTO]:
        cik = ticker.formatted_cik
        endpoint = SEC_API_ENDPOINT_TEMPLATE.format(cik=cik)

        try:
            response = self.sec_api_client.make_request(endpoint)
            submissions = response.json()
        except ApiClientError as e:
            logger.error("%s Transport error fetching submissions for CIK %s: %s", "SEC Submissions", cik, e)
            return []
        except ValueError as e:
            logger.error("%s Failed to parse submissions JSON for CIK %s: %s", "SEC Submissions", cik, e)
            return []

        filings = submissions["filings"]["recent"]
        results = []

        keys = (
            "form",
            "items",
            "filingDate",
            "accessionNumber",
            "acceptanceDateTime",
            "primaryDocument",
        )
        rows = zip(*(filings[k] for k in keys), strict=True)

        for form, items, filing_date, accession_number, acceptance_date_time, primary_document in rows:
            if self.matches(form, len(results), items, filing_date):
                dto = SecSubmissionDTO(
                    ticker=ticker.ticker,
                    cik=cik,
                    form_type=self.form_type,
                    accession_number=accession_number,
                    filing_date=filing_date,
                    acceptance_date_time=acceptance_date_time,
                    primary_document=primary_document,
                )

                results.append(dto)

        return results
