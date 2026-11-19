"""
Service module for filtering SEC financial data records.
"""

import logging
from datetime import date, timedelta

from django.utils.dateparse import parse_date

from apps.stock_data.constants.sec_constants import FiscalPeriod, FormType
from apps.stock_data.models.sec_models import SecFinancialData

LOG_PREFIX = "[SEC Filter Service]"
logger = logging.getLogger(__name__)


class ProcessSecFinanceRecords:
    """Class to encapsulate SEC financial data processing logic."""

    # Constants for filtering logic
    MAX_DAYS_FOR_QUARTERLY_PERIOD = 110
    MIN_DAYS_FOR_YEARLY_PERIOD = 340

    # Constants for dictionary keys
    KEY_FORM = "form"
    KEY_START = "start"
    KEY_END = "end"
    FISCAL_YEAR = "fy"
    FISCAL_PERIOD = "fp"

    def add_missing_data(self, item):
        if not item.get(self.FISCAL_YEAR):
            item[self.FISCAL_YEAR] = item.get(self.KEY_START).split("-")[0]

        if not item.get(self.FISCAL_PERIOD):
            form = item.get(self.KEY_FORM)
            if form == FormType.FORM_10_K:
                item[self.FISCAL_PERIOD] = FiscalPeriod.FY

            if form == FormType.FORM_10_Q:
                item[self.FISCAL_PERIOD] = (
                    FiscalPeriod.Q1
                )  # we set it as Q1 but it doesent metter as we dont use this filed
        return item

    def filter_records(self, item):
        """
        Filter financial records based on form type and period length.
        Excludes 10-Q forms that refer to periods longer than three months.
        Args:
            item: Dictionary containing financial data from SEC API
        Returns:
            bool: True if record should be included, False if excluded
        """

        # Skip records with excluded form types
        form_type = item.get(self.KEY_FORM)
        if form_type not in {FormType.FORM_10_Q, FormType.FORM_10_K}:
            return False

        # Check for null start_date fields
        start_date_str = item.get(self.KEY_START)
        end_date_str = item.get(self.KEY_END)
        if not end_date_str or not start_date_str:
            logger.warning("%s Skipping record due to missing required fields: item=%s", LOG_PREFIX, item)

            return False

        # For 10-Q forms, exclude periods longer than 3 months as we want to exclude
        # cumulative records for 2 and 3 quarters cumulative
        if form_type == FormType.FORM_10_Q and end_date_str:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            # Calculate difference in days
            if start_date and end_date:
                date_diff = (end_date - start_date).days
                # If more than 110 days, exclude this record (3 months < 110 days)
                if date_diff > self.MAX_DAYS_FOR_QUARTERLY_PERIOD:
                    return False

        # For 10-K forms, exclude periods shorter than 340 days as we want to exclude
        # cumulative records for 2 and 3 months cumulative
        if form_type == FormType.FORM_10_K and end_date_str:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            # Calculate difference in days
            if start_date and end_date:
                date_diff = (end_date - start_date).days
                # If less than 340 days, exclude this record
                if date_diff < self.MIN_DAYS_FOR_YEARLY_PERIOD:
                    return False

        return True

    def filter_by_date(self, financial_records):
        """
        Filter financial records by unique combination of start_date and end_date.
        Args:
            financial_records: List of SecFinancialData objects
        Returns:
            List of filtered SecFinancialData objects with duplicates removed
        """

        seen_keys = set()
        filtered_records = []
        for record in financial_records:
            # Create a key from start_date and end_date
            record_key = (record.start_date, record.end_date)
            if record_key not in seen_keys:
                seen_keys.add(record_key)
                filtered_records.append(record)

        return filtered_records

    def _is_quarter_record(self, record):
        try:
            start_date = record.start_date if isinstance(record.start_date, date) else parse_date(str(record.start_date))
            end_date = record.end_date if isinstance(record.end_date, date) else parse_date(str(record.end_date))
            if not start_date or not end_date:
                return False
            # Check if the dates are approximately 3 months apart (within ±10 days)
            time_diff = (end_date - start_date).days
            if abs(time_diff - 90) <= 10:  # ~3 months = 90 days, within 10 days tolerance
                return True
        except (ValueError, TypeError, AttributeError):
            # If date parsing fails, skip this record
            pass

        return False

    def _return_if_next_quarter_record(self, record1, record2):
        try:
            end_date = record1.end_date if isinstance(record1.end_date, date) else parse_date(str(record1.end_date))
            start_date = record2.start_date if isinstance(record2.start_date, date) else parse_date(str(record2.start_date))
            if not start_date or not end_date:
                return None
            # Check if the dates are approximately 3 months apart (within ±10 days)
            time_diff = (start_date - end_date).days
            if time_diff == 1:  # next period
                return record2
        except (ValueError, TypeError, AttributeError):
            # If date parsing fails, skip this record
            pass

        return None

    def _return_if_fiscal_year_record(self, record1, record2):
        try:
            record1_end_date = record1.end_date if isinstance(record1.end_date, date) else parse_date(str(record1.end_date))
            record2_end_date = record2.end_date if isinstance(record2.end_date, date) else parse_date(str(record2.end_date))
            record2_start_date = record2.start_date if isinstance(record2.start_date, date) else parse_date(str(record2.start_date))

            if not record1_end_date or not record2_end_date or not record2_start_date:
                return None

            # Check if the dates are approximately 3 months apart (within ±10 days)
            r1_to_r2_diff = (record2_end_date - record1_end_date).days
            r2_diff = (record2_end_date - record2_start_date).days
            if (
                abs(r1_to_r2_diff - 90) <= 10 and abs(r2_diff - 365) <= 10
            ):  # ~3 months = 90 days, within 10 days tolerance, 1 year with 10 days tolerance
                return record2

        except (ValueError, TypeError, AttributeError):
            # If date parsing fails, skip this record
            pass

        return None

    def calculate_missing_q4_values(self, financial_records):
        """
        Calculate missing Q4 values from FY data.
        Groups records by end_date ranges to find complete quarters:
        Q1 → Q2 → Q3 → FY (each 3 months apart, within ±10 days)
        If any required quarter is missing in the sequence, starts over
        looking for next available Q1 record.
        """

        if len(financial_records) < 4:
            return []

        new_records = []
        i = 0
        while i < len(financial_records) - 3:
            # Find a record with fiscal_period equal to Q1
            if not self._is_quarter_record(financial_records[i]):
                i += 1
                continue

            # Assume q1
            q1_record = financial_records[i]
            # Look for Q2 (starts next day after Q1)
            q2_record = self._return_if_next_quarter_record(q1_record, financial_records[i + 1])
            if not q2_record:
                i += 1
                continue

            # Look for Q3 (starts next day after Q2)
            q3_record = self._return_if_next_quarter_record(q2_record, financial_records[i + 2])
            if not q3_record:
                i += 1
                continue

            # Look for FY (3 months after Q3, within ±10 days)
            fy_record = self._return_if_fiscal_year_record(q3_record, financial_records[i + 3])
            if not fy_record:
                i += 1
                continue

            # If we have all required records, calculate missing Q4
            try:
                fy_value = int(fy_record.value)
                q1_value = int(q1_record.value)
                q2_value = int(q2_record.value)
                q3_value = int(q3_record.value)

                # Calculate Q4 value
                calculated_q4_value = fy_value - q1_value - q2_value - q3_value

                # Create new Q4 record with properties from FY but with Q4 period and 10-Q form_type
                q4_record = SecFinancialData(
                    cik=fy_record.cik,
                    start_date=parse_date(str(q3_record.end_date))
                    + timedelta(days=1),  # Use last quarter's end date as start + 1 day
                    end_date=fy_record.end_date,  # Use FY end date as end
                    value=calculated_q4_value,
                    accession_number=fy_record.accession_number,
                    fiscal_year=fy_record.fiscal_year,
                    fiscal_period=FiscalPeriod.Q4,  # Set period to Q4
                    form_type=FormType.FORM_10_Q,  # Set form type to 10-Q for Q4 records
                    filed_date=fy_record.filed_date,  # Keep same filing date
                    tag_id=fy_record.tag_id,  # Keep same tag id
                )
                new_records.append(q4_record)

            except (ValueError, TypeError):
                # If calculation fails, skip this group
                pass

            # Move to the next record
            i += 1

        return new_records
