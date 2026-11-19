import pytest
import responses

from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient


@pytest.fixture
def sec_client():
    return SecApiClient(
        base_url="https://test.sec.gov",
        app_name="TestApp",
        sec_email="test@example.com",
        limit=10
    )

@responses.activate
def test_sec_api_client_success(sec_client):
    responses.add(
        responses.GET,
        "https://test.sec.gov/test-endpoint",
        json={"foo": "bar"},
        status=200
    )

    response = sec_client.make_request("test-endpoint")
    assert response.status_code == 200
    assert response.json() == {"foo": "bar"}
    assert "User-Agent" in response.request.headers
    assert response.request.headers["User-Agent"] == "TestApp test@example.com"

@responses.activate
def test_sec_api_client_429_retry(sec_client, mocker):
    # Mock time.sleep to avoid waiting 10 minutes in tests
    mocker.patch("time.sleep")

    responses.add(
        responses.GET,
        "https://test.sec.gov/test-endpoint",
        status=429
    )
    responses.add(
        responses.GET,
        "https://test.sec.gov/test-endpoint",
        json={"foo": "bar"},
        status=200
    )

    response = sec_client.make_request("test-endpoint")
    assert response.status_code == 200
    assert len(responses.calls) == 2

@responses.activate
def test_sec_api_client_failure(sec_client):
    responses.add(
        responses.GET,
        "https://test.sec.gov/test-endpoint",
        status=500
    )

    with pytest.raises(ApiClientError) as excinfo:
        sec_client.make_request("test-endpoint")
    assert "status 500" in str(excinfo.value)
