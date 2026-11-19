
import pytest
import responses

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.api_clients.tiingo_api_client import TiingoApiClient
from apps.stock_data.services.fetch_historical_prices.tiingo_historical_prices_service import (
    TiingoHistoricalPricesService,
)
from apps.stock_data.tests.factories import TickerFactory


@pytest.fixture
def service():
    client = TiingoApiClient(base_url="https://api.tiingo.com", api_token="test-token")
    return TiingoHistoricalPricesService(api_client=client)

@pytest.mark.django_db
@responses.activate
def test_fetch_and_save_ticker_prices_success(service):
    ticker = "AAPL"
    responses.add(
        responses.GET,
        f"https://api.tiingo.com/tiingo/daily/{ticker}/prices",
        json=[
            {
                "date": "2023-01-01T00:00:00.000Z",
                "close": 150.0,
                "open": 145.0,
                "high": 155.0,
                "low": 140.0,
                "volume": 1000000,
            }
        ],
        status=200
    )

    count = service.fetch_and_save_ticker_prices(ticker, incremental=False)

    assert count == 1
    assert HistoricalStockPrice.objects.filter(ticker=ticker).count() == 1

@pytest.mark.django_db
@responses.activate
def test_fetch_and_persist_historical_prices_loop(service):
    TickerFactory(ticker="AAPL", status=Ticker.ACTIVE)
    TickerFactory(ticker="MSFT", status=Ticker.ACTIVE)

    responses.add(
        responses.GET,
        "https://api.tiingo.com/tiingo/daily/AAPL/prices",
        json=[{"date": "2023-01-01T00:00:00.000Z", "close": 150.0, "open": 145.0, "high": 155.0, "low": 140.0, "volume": 100}],
        status=200
    )
    responses.add(
        responses.GET,
        "https://api.tiingo.com/tiingo/daily/MSFT/prices",
        json=[{"date": "2023-01-01T00:00:00.000Z", "close": 250.0, "open": 245.0, "high": 255.0, "low": 240.0, "volume": 200}],
        status=200
    )

    total = service.fetch_and_persist_historical_prices(incremental=False)
    assert total == 2
    assert HistoricalStockPrice.objects.count() == 2
