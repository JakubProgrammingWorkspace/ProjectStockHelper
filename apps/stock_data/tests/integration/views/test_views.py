import pytest
from django.urls import reverse

from apps.stock_data.tests.factories import HistoricalStockPriceFactory, TickerFactory


@pytest.mark.django_db
def test_stock_data_view_success(client):
    TickerFactory(ticker="AAPL", status=1)
    HistoricalStockPriceFactory(ticker="AAPL", close_price=150.0)

    url = reverse('stock-data', kwargs={'ticker_symbol': 'AAPL'})
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert len(data["prices"]) == 1

@pytest.mark.django_db
def test_tickers_list_view(client):
    TickerFactory(ticker="AAPL", name="Apple", status=1)
    TickerFactory(ticker="MSFT", name="Microsoft", status=1)
    TickerFactory(ticker="DELETED", status=0) # Inactive

    url = reverse('tickers-list')
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert len(data["tickers"]) == 2
    assert data["tickers"][0]["ticker"] == "AAPL"

@pytest.mark.django_db
def test_stock_data_view_not_found(client):
    url = reverse('stock-data', kwargs={'ticker_symbol': 'UNKNOWN'})
    response = client.get(url)
    assert response.status_code == 404
