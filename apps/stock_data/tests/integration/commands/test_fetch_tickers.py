from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.stock_data.models.tickers_models import SecTicker


@pytest.mark.django_db
def test_fetch_tickers_process_tickers_command():
    # Use real ProcessTickersService but with some data
    from apps.stock_data.tests.factories import SecTickerFactory
    SecTickerFactory(name="Sample Trust", status=SecTicker.ACTIVE, updated=None)

    out = StringIO()
    call_command("fetch_tickers", "process_tickers", stdout=out)

    assert "Ticker processing completed successfully" in out.getvalue()
    assert SecTicker.objects.filter(status=SecTicker.EXCLUDED).count() == 1

@pytest.mark.django_db
@patch("apps.stock_data.services.fetch_tickers.fetch_sec_tickers_service.FetchSecTickersService.fetch_and_update_tickers")
@patch("apps.stock_data.services.api_clients.sec_api_client.SecApiClient.from_env")
def test_fetch_tickers_sec_tickers_command(mock_from_env, mock_fetch_service):
    mock_fetch_service.return_value = 10

    out = StringIO()
    call_command("fetch_tickers", "sec_tickers", stdout=out)

    assert "Successfully processed 10 SEC tickers" in out.getvalue()
    mock_fetch_service.assert_called_once()
