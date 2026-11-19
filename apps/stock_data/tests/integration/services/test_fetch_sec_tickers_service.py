import pytest
import responses

from apps.stock_data.models.tickers_models import SecTicker
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.fetch_tickers.fetch_sec_tickers_service import FetchSecTickersService


@pytest.fixture
def service():
    client = SecApiClient(base_url="https://test.sec.gov", app_name="Test", sec_email="test@test.com")
    return FetchSecTickersService(api_client=client)

@pytest.mark.django_db
@responses.activate
def test_fetch_and_update_tickers_success(service):
    # Mock SEC response
    mock_data = {
        "data": [
            [320193, "Apple Inc.", "AAPL", "Nasdaq"],
            [789019, "Microsoft Corp", "MSFT", "Nasdaq"],
            [123456, "Small Corp", "SML", "OTC"], # Should be skipped
        ],
        "fields": ["cik", "name", "ticker", "exchange"]
    }
    responses.add(
        responses.GET,
        "https://test.sec.gov/files/company_tickers_exchange.json",
        json=mock_data,
        status=200
    )

    # Pre-existing ticker that should become inactive
    SecTicker.objects.create(cik=999, name="Old", ticker="OLD", exchange="NYSE", status=SecTicker.ACTIVE)

    count = service.fetch_and_update_tickers()

    assert count == 2
    assert SecTicker.objects.filter(status=SecTicker.ACTIVE).count() == 2
    assert SecTicker.objects.get(ticker="AAPL").cik == 320193
    assert SecTicker.objects.get(ticker="OLD").status == SecTicker.INACTIVE
    assert not SecTicker.objects.filter(ticker="SML").exists()

@pytest.mark.django_db
@responses.activate
def test_fetch_and_update_tickers_api_error(service):
    responses.add(
        responses.GET,
        "https://test.sec.gov/files/company_tickers_exchange.json",
        status=500
    )

    count = service.fetch_and_update_tickers()
    assert count == 0
