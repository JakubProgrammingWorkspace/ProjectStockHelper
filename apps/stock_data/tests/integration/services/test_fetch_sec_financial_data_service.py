import pytest
import responses

from apps.stock_data.models.sec_models import SecFinancialData, SecProcessedFinancialData
from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.fetch_sec_financial_data.fetch_sec_financial_data_service import (
    FetchSecFinancialDataService,
)
from apps.stock_data.tests.factories import TickerFactory


@pytest.fixture
def service():
    client = SecApiClient(base_url="https://test.sec.gov", app_name="Test", sec_email="test@test.com")
    return FetchSecFinancialDataService(sec_api_client=client)

@pytest.mark.django_db
@responses.activate
def test_fetch_and_process_financial_data_success(service):
    ticker = TickerFactory(ticker="AAPL", cik=320193, status=Ticker.ACTIVE)

    # Mock SEC responses for each tag
    from apps.stock_data.constants.sec_constants import SEC_TAG_MAPPING

    for tag in SEC_TAG_MAPPING.keys():
        mock_data = {
            "units": {
                "USD": [
                    {
                        "start": "2023-01-01",
                        "end": "2023-03-31",
                        "val": 1000000,
                        "accn": "000-00-001",
                        "fy": 2023,
                        "fp": "Q1",
                        "form": "10-Q",
                        "filed": "2023-04-15"
                    }
                ]
            }
        }
        responses.add(
            responses.GET,
            f"https://test.sec.gov/api/xbrl/companyconcept/CIK{ticker.formatted_cik}/us-gaap/{tag}.json",
            json=mock_data,
            status=200
        )

    count = service.fetch_and_process_financial_data()
    assert count == 1
    assert SecFinancialData.objects.filter(cik=ticker.cik).count() > 0

    # Check if processed records (non-TTM) exist
    assert SecProcessedFinancialData.objects.filter(cik=ticker.cik).count() > 0
