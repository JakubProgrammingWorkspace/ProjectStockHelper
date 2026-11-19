from datetime import date

import pytest

from apps.stock_data.services.price_bundler import PriceBundler


@pytest.fixture
def daily_prices():
    return [
        {"date": date(2023, 1, 2), "open_price": 100, "high_price": 105, "low_price": 95, "close_price": 102, "volume": 1000},  # Monday
        {"date": date(2023, 1, 3), "open_price": 102, "high_price": 108, "low_price": 101, "close_price": 105, "volume": 1100}, # Tuesday
        {"date": date(2023, 1, 4), "open_price": 105, "high_price": 106, "low_price": 103, "close_price": 104, "volume": 900},  # Wednesday
        {"date": date(2023, 1, 5), "open_price": 104, "high_price": 110, "low_price": 102, "close_price": 108, "volume": 1200}, # Thursday
        {"date": date(2023, 1, 6), "open_price": 108, "high_price": 112, "low_price": 107, "close_price": 110, "volume": 1300}, # Friday
        {"date": date(2023, 1, 9), "open_price": 110, "high_price": 115, "low_price": 109, "close_price": 114, "volume": 1400}, # Next Monday
    ]

def test_bundle_1d(daily_prices):
    result = PriceBundler.bundle("1D", daily_prices)
    assert result == daily_prices

def test_bundle_1w(daily_prices):
    result = PriceBundler.bundle("1W", daily_prices)
    assert len(result) == 2

    # First week (Jan 2 - Jan 6)
    week1 = result[0]
    assert week1["date"] == date(2023, 1, 2)
    assert week1["open_price"] == 100
    assert week1["high_price"] == 112
    assert week1["low_price"] == 95
    assert week1["close_price"] == 110
    assert week1["volume"] == 1000 + 1100 + 900 + 1200 + 1300

    # Second week (Jan 9)
    week2 = result[1]
    assert week2["date"] == date(2023, 1, 9)
    assert week2["open_price"] == 110
    assert week2["high_price"] == 115
    assert week2["low_price"] == 109
    assert week2["close_price"] == 114
    assert week2["volume"] == 1400

def test_bundle_1m(daily_prices):
    # Add a price from a different month
    prices_with_next_month = daily_prices + [
        {"date": date(2023, 2, 1), "open_price": 114, "high_price": 120, "low_price": 113, "close_price": 118, "volume": 1500}
    ]
    result = PriceBundler.bundle("1M", prices_with_next_month)
    assert len(result) == 2

    # Jan bundle
    jan = result[0]
    assert jan["date"] == date(2023, 1, 2)
    assert jan["open_price"] == 100
    assert jan["high_price"] == 115
    assert jan["low_price"] == 95
    assert jan["close_price"] == 114

    # Feb bundle
    feb = result[1]
    assert feb["date"] == date(2023, 2, 1)

def test_bundle_empty():
    assert PriceBundler.bundle("1W", []) == []

def test_bundle_single_day():
    single_day = [{"date": date(2023, 1, 2), "open_price": 100, "high_price": 105, "low_price": 95, "close_price": 102, "volume": 1000}]
    # Weekly bundle should work even for single day
    result = PriceBundler.bundle("1W", single_day)
    assert len(result) == 1
    assert result[0] == single_day[0]

def test_bundle_custom_days(daily_prices):
    result = PriceBundler.bundle("3D", daily_prices)
    # Group 1: Jan 2, 3, 4
    # Group 2: Jan 5, 6 (next date Jan 9 is 4 days later, so it starts a new group)
    # Group 3: Jan 9
    assert len(result) == 3
    assert result[0]["date"] == date(2023, 1, 2)
    assert result[1]["date"] == date(2023, 1, 5)
    assert result[2]["date"] == date(2023, 1, 9)

def test_bundle_invalid_interval(daily_prices):
    # Should return original data for invalid interval
    result = PriceBundler.bundle("BOGUS", daily_prices)
    assert result == daily_prices
