import calendar
import logging
from datetime import date

from apps.stock_data.constants.sec_constants import FormType
from apps.stock_data.models.sec_models import SecFinancialData, SecProcessedFinancialData

LOG_PREFIX = "[Process SEC Financial Data Service]"
logger = logging.getLogger(__name__)


class ProcessSecFinancialDataService:
    """Service class to process SEC financial data and calculate TTM values."""

    def process_ticker(self, cik: int):
        """Process financial data for a single ticker."""
        # Fetch financial data for this ticker
        financial_data = (
            SecFinancialData.objects.filter(
                cik=cik,
                form_type=FormType.FORM_10_Q,
                tag_id__in=[SecFinancialData.TagId.NET_INCOME_LOSS, SecFinancialData.TagId.SALES_REVENUE_NET],
            )
            .order_by("end_date")
            .values("end_date", "value", "tag_id")
        )

        # Group data by tag_id
        tag_data = {}
        for record in financial_data:
            tag_id = record["tag_id"]
            if tag_id not in tag_data:
                tag_data[tag_id] = []
            tag_data[tag_id].append(record)

        # Process each tag's data
        processed_records = []

        # Process NET_INCOME_LOSS and SALES_REVENUE_NET
        for tag_id in [SecFinancialData.TagId.NET_INCOME_LOSS, SecFinancialData.TagId.SALES_REVENUE_NET]:
            if tag_id in tag_data:
                # Get the data for this tag
                data = tag_data[tag_id]

                # Convert dates to end of month and prepare records
                for record in data:
                    # Set the date to the end of the month
                    end_date = self.get_end_of_month(record["end_date"])

                    # Create processed record
                    processed_records.append(
                        {"cik": cik, "end_date": end_date, "value": record["value"], "tag_id": tag_id}
                    )

        # Calculate TTM values
        ttm_records = self.calculate_ttm_values(tag_data, cik)
        processed_records.extend(ttm_records)

        # Save all processed records
        if processed_records:
            self.save_processed_data(processed_records)

    def get_end_of_month(self, input_date):
        """Convert date to end of month."""
        year = input_date.year
        month = input_date.month
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)

    def calculate_ttm_values(self, tag_data, cik):
        """Calculate TTM values for sales revenue and net income."""
        ttm_records = []

        # Process TTM for SALES_REVENUE_NET
        if SecFinancialData.TagId.SALES_REVENUE_NET in tag_data:
            sales_data = sorted(tag_data[SecFinancialData.TagId.SALES_REVENUE_NET], key=lambda x: x["end_date"])
            ttm_records.extend(
                self.calculate_ttm_for_tag(sales_data, cik, SecProcessedFinancialData.TagId.SALES_REVENUE_NET_TTM)
            )

        # Process TTM for NET_INCOME_LOSS
        if SecFinancialData.TagId.NET_INCOME_LOSS in tag_data:
            income_data = sorted(tag_data[SecFinancialData.TagId.NET_INCOME_LOSS], key=lambda x: x["end_date"])
            ttm_records.extend(
                self.calculate_ttm_for_tag(income_data, cik, SecProcessedFinancialData.TagId.NET_INCOME_LOSS_TTM)
            )

        return ttm_records

    def calculate_ttm_for_tag(self, data, cik, ttm_tag_id):
        """Calculate TTM values for a specific tag."""
        ttm_records = []
        missing_quarters = set()

        # For each date, find the previous 3 quarters + current quarter
        for i, _record in enumerate(data):
            # Get the 4 most recent quarters (including current)
            quarters = []
            for j in range(4):
                if i - j >= 0:
                    quarters.append(data[i - j])
                else:
                    break

            # Only calculate TTM if we have 4 quarters and they are properly spaced
            if len(quarters) == 4:
                # Check if quarters are approximately 3 months apart
                valid_quarters = True
                for k in range(1, len(quarters)):
                    # Calculate the difference in months between consecutive quarters
                    days_diff = abs((quarters[k - 1]["end_date"] - quarters[k]["end_date"]).days)

                    # Allow for some variance (±20 days) to account for end-of-month date adjustments
                    if abs(days_diff - 90) > 20:
                        valid_quarters = False
                        missing_quarters.add(self.subtract_months(quarters[k - 1]["end_date"], 3))
                        break

                if valid_quarters:
                    # Sum the values for the 4 quarters
                    ttm_value = sum(q["value"] for q in quarters)

                    # Use the date of the most recent quarter for the TTM record
                    end_date = self.get_end_of_month(quarters[0]["end_date"])

                    ttm_records.append({"cik": cik, "end_date": end_date, "value": ttm_value, "tag_id": ttm_tag_id})

        if missing_quarters and data:
            logger.info(
                "%s For cik: %s tag id: %s there are missing months: %s",
                LOG_PREFIX,
                cik,
                data[0]["tag_id"],
                missing_quarters,
            )

        return ttm_records

    def save_processed_data(self, records):
        """Save processed financial data to SecProcessedFinancialData."""
        # Create list of SecProcessedFinancialData objects
        processed_objects = []
        for record in records:
            processed_objects.append(
                SecProcessedFinancialData(
                    cik=record["cik"], end_date=record["end_date"], value=record["value"], tag_id=record["tag_id"]
                )
            )

        # Bulk create the records
        SecProcessedFinancialData.objects.bulk_create(processed_objects, ignore_conflicts=True)

    def subtract_months(self, date_obj, months):
        year = date_obj.year
        month = date_obj.month - months
        day = date_obj.day

        # Adjust year and month if month is zero or negative
        while month <= 0:
            month += 12
            year -= 1

        # Get the last day of the target month (taking leap years into account)
        last_day_of_month = calendar.monthrange(year, month)[1]

        # Adjust day to not exceed last day of target month
        day = min(day, last_day_of_month)

        return f"{year}, {month}, {day}"
