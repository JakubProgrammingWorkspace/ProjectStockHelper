from datetime import date

import pytest

from apps.stock_data.models.sec_models import SecProcessedFinancialData
from apps.stock_data.services.fetch_sec_financial_data.process_sec_financial_data_service import (
    ProcessSecFinancialDataService,
)


@pytest.fixture
def service():
    return ProcessSecFinancialDataService()

def test_get_end_of_month(service):
    assert service.get_end_of_month(date(2023, 2, 10)) == date(2023, 2, 28)
    assert service.get_end_of_month(date(2024, 2, 10)) == date(2024, 2, 29) # Leap year
    assert service.get_end_of_month(date(2023, 12, 1)) == date(2023, 12, 31)

def test_calculate_ttm_for_tag_valid(service):
    cik = 123
    ttm_tag_id = SecProcessedFinancialData.TagId.NET_INCOME_LOSS_TTM
    data = [
        {"end_date": date(2022, 3, 31), "value": 100, "tag_id": 4},
        {"end_date": date(2022, 6, 30), "value": 110, "tag_id": 4},
        {"end_date": date(2022, 9, 30), "value": 120, "tag_id": 4},
        {"end_date": date(2022, 12, 31), "value": 130, "tag_id": 4},
    ]

    result = service.calculate_ttm_for_tag(data, cik, ttm_tag_id)
    assert len(result) == 1
    assert result[0]["value"] == 460 # 100+110+120+130
    assert result[0]["end_date"] == date(2022, 12, 31)
    assert result[0]["tag_id"] == ttm_tag_id

def test_calculate_ttm_for_tag_missing_quarter(service):
    cik = 123
    ttm_tag_id = SecProcessedFinancialData.TagId.NET_INCOME_LOSS_TTM
    data = [
        {"end_date": date(2022, 3, 31), "value": 100, "tag_id": 4},
        {"end_date": date(2022, 6, 30), "value": 110, "tag_id": 4},
        # Missing Q3
        {"end_date": date(2022, 12, 31), "value": 130, "tag_id": 4},
        {"end_date": date(2023, 3, 31), "value": 140, "tag_id": 4},
    ]

    result = service.calculate_ttm_for_tag(data, cik, ttm_tag_id)
    assert len(result) == 0

def test_calculate_ttm_for_tag_multiple_years(service):
    cik = 123
    ttm_tag_id = SecProcessedFinancialData.TagId.NET_INCOME_LOSS_TTM
    data = [
        {"end_date": date(2021, 3, 31), "value": 10, "tag_id": 4},
        {"end_date": date(2021, 6, 30), "value": 20, "tag_id": 4},
        {"end_date": date(2021, 9, 30), "value": 30, "tag_id": 4},
        {"end_date": date(2021, 12, 31), "value": 40, "tag_id": 4},
        {"end_date": date(2022, 3, 31), "value": 50, "tag_id": 4},
    ]

    result = service.calculate_ttm_for_tag(data, cik, ttm_tag_id)
    # TTM at 2021-12-31: 10+20+30+40 = 100
    # TTM at 2022-03-31: 20+30+40+50 = 140
    assert len(result) == 2
    assert result[0]["value"] == 100
    assert result[1]["value"] == 140
