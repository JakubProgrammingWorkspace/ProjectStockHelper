import pytest

from apps.stock_data.models.tickers_models import SecTicker
from apps.stock_data.services.fetch_tickers.process_tickers_service import ProcessTickersService
from apps.stock_data.tests.factories import SecTickerFactory


@pytest.fixture
def service():
    return ProcessTickersService()

@pytest.mark.django_db
def test_set_exclude_status_to_trusts_and_etf(service):
    SecTickerFactory(name="Apple Inc.", status=SecTicker.ACTIVE, updated=None)
    SecTickerFactory(name="Vanguard ETF", status=SecTicker.ACTIVE, updated=None)
    SecTickerFactory(name="Sample Trust", status=SecTicker.ACTIVE, updated=None)

    service._set_exclude_status_to_trusts_and_etf(SecTicker)

    assert SecTicker.objects.filter(status=SecTicker.ACTIVE).count() == 1
    assert SecTicker.objects.filter(status=SecTicker.EXCLUDED).count() == 2

@pytest.mark.django_db
def test_deduplicate_by_shortest_ticker(service):
    # Same CIK, different tickers
    cik = 12345
    SecTickerFactory(cik=cik, ticker="ABCD", name="Long", status=SecTicker.ACTIVE, updated=None)
    SecTickerFactory(cik=cik, ticker="ABC", name="Short", status=SecTicker.ACTIVE, updated=None)

    service._deduplicate_by_shortest_ticker(SecTicker)

    assert SecTicker.objects.get(ticker="ABC").status == SecTicker.ACTIVE
    assert SecTicker.objects.get(ticker="ABCD").status == SecTicker.DEDUPLICATED

@pytest.mark.django_db
def test_set_excluded_status_for_non_common_stock(service):
    SecTickerFactory(ticker="AAPL", status=SecTicker.ACTIVE, updated=None)
    SecTickerFactory(ticker="AAPL-W", status=SecTicker.ACTIVE, updated=None) # Contains '-'

    service._set_excluded_status_for_non_common_stock(SecTicker)

    assert SecTicker.objects.get(ticker="AAPL").status == SecTicker.ACTIVE
    assert SecTicker.objects.get(ticker="AAPL-W").status == SecTicker.EXCLUDED
