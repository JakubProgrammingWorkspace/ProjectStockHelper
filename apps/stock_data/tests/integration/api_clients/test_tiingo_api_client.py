import pytest
import responses

from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.tiingo_api_client import TiingoApiClient


@pytest.fixture
def tiingo_client():
    return TiingoApiClient(
        base_url="https://api.tiingo.com",
        api_token="test-token",
        hourly_limit=10,
        daily_limit=100
    )

@responses.activate
def test_tiingo_api_client_success(tiingo_client):
    responses.add(
        responses.GET,
        "https://api.tiingo.com/tiingo/daily/AAPL/prices",
        json=[{"close": 150.0, "date": "2023-01-01"}],
        status=200
    )

    response = tiingo_client.make_request("tiingo/daily/AAPL/prices")
    assert response.status_code == 200
    assert response.json()[0]["close"] == 150.0
    assert response.request.headers["Authorization"] == "Token test-token"

@responses.activate
def test_tiingo_api_client_429_retry(tiingo_client, mocker):
    mocker.patch("time.sleep")

    responses.add(responses.GET, "https://api.tiingo.com/test", status=429)
    responses.add(responses.GET, "https://api.tiingo.com/test", status=200, json={"ok": True})

    response = tiingo_client.make_request("test")
    assert response.status_code == 200
    assert len(responses.calls) == 2

@responses.activate
def test_tiingo_api_client_failure(tiingo_client):
    responses.add(responses.GET, "https://api.tiingo.com/test", status=403)

    with pytest.raises(ApiClientError) as excinfo:
        tiingo_client.make_request("test")
    assert "status 403" in str(excinfo.value)
