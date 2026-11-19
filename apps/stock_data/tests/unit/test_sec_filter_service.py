import pytest

from apps.stock_data.constants.sec_constants import FiscalPeriod, FormType
from apps.stock_data.services.fetch_sec_financial_data.sec_filter_service import ProcessSecFinanceRecords


@pytest.fixture
def processor():
    return ProcessSecFinanceRecords()

def test_filter_records_valid_10k(processor):
    item = {
        "form": FormType.FORM_10_K,
        "start": "2023-01-01",
        "end": "2023-12-31"
    }
    assert processor.filter_records(item) is True

def test_filter_records_invalid_10k_too_short(processor):
    item = {
        "form": FormType.FORM_10_K,
        "start": "2023-01-01",
        "end": "2023-06-30"  # ~180 days
    }
    assert processor.filter_records(item) is False

def test_filter_records_valid_10q(processor):
    item = {
        "form": FormType.FORM_10_Q,
        "start": "2023-01-01",
        "end": "2023-03-31"
    }
    assert processor.filter_records(item) is True

def test_filter_records_invalid_10q_too_long(processor):
    item = {
        "form": FormType.FORM_10_Q,
        "start": "2023-01-01",
        "end": "2023-06-30" # ~180 days
    }
    assert processor.filter_records(item) is False

def test_filter_records_invalid_form(processor):
    item = {
        "form": "8-K",
        "start": "2023-01-01",
        "end": "2023-03-31"
    }
    assert processor.filter_records(item) is False

def test_add_missing_data_fy(processor):
    item = {
        "form": FormType.FORM_10_K,
        "start": "2023-01-01",
        "end": "2023-12-31"
    }
    processor.add_missing_data(item)
    assert item["fy"] == "2023"
    assert item["fp"] == FiscalPeriod.FY

def test_add_missing_data_10q(processor):
    item = {
        "form": FormType.FORM_10_Q,
        "start": "2023-01-01",
        "end": "2023-03-31"
    }
    processor.add_missing_data(item)
    assert item["fy"] == "2023"
    assert item["fp"] == FiscalPeriod.Q1

def test_filter_by_date(processor):
    from datetime import date

    from apps.stock_data.models.sec_models import SecFinancialData
    records = [
        SecFinancialData(start_date=date(2023, 1, 1), end_date=date(2023, 3, 31)),
        SecFinancialData(start_date=date(2023, 1, 1), end_date=date(2023, 3, 31)), # Duplicate
        SecFinancialData(start_date=date(2023, 4, 1), end_date=date(2023, 6, 30)),
    ]
    filtered = processor.filter_by_date(records)
    assert len(filtered) == 2
    assert filtered[0].start_date == date(2023, 1, 1)
    assert filtered[1].start_date == date(2023, 4, 1)

def test_calculate_missing_q4_values(processor):
    from datetime import date

    from apps.stock_data.models.sec_models import SecFinancialData
    # Q1, Q2, Q3, FY
    records = [
        SecFinancialData(cik=123, start_date=date(2023, 1, 1), end_date=date(2023, 3, 31), value=100, fiscal_year=2023),
        SecFinancialData(cik=123, start_date=date(2023, 4, 1), end_date=date(2023, 6, 30), value=110, fiscal_year=2023),
        SecFinancialData(cik=123, start_date=date(2023, 7, 1), end_date=date(2023, 9, 30), value=120, fiscal_year=2023),
        SecFinancialData(cik=123, start_date=date(2023, 1, 1), end_date=date(2023, 12, 31), value=450, fiscal_year=2023),
    ]
    # Injected fields by add_missing_data or assumed in calculate_missing_q4_values
    # Wait, the method uses record.end_date which might be a string in the API item but it's a date in the model
    # The method uses parse_date(str(q3_record.end_date)) which is a bit weird if it's already a date

    new_records = processor.calculate_missing_q4_values(records)
    assert len(new_records) == 1
    q4 = new_records[0]
    assert q4.value == 450 - 100 - 110 - 120 # 120
    assert q4.fiscal_period == FiscalPeriod.Q4
    assert q4.form_type == FormType.FORM_10_Q
