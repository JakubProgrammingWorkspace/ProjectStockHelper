import pytest


@pytest.fixture
def api_response_200():
    return {"status": "success", "data": {}}

@pytest.fixture
def mock_sec_tickers_response():
    return {
        "elms": [
            {"ticker": "AAPL", "title": "Apple Inc.", "cik": 320193},
            {"ticker": "MSFT", "title": "Microsoft Corp", "cik": 789019},
        ]
    }
