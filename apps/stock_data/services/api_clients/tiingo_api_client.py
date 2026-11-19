import logging
import os
import time
from datetime import timedelta

import requests
from django.core.cache import cache
from django.utils import timezone

from apps.stock_data.services.api_clients.exceptions import ApiClientError

LOG_PREFIX = "[Tiingo API]"
logger = logging.getLogger(__name__)


class TiingoApiClient:
    """
    API client for Tiingo. Handles transport and rate limiting only.

    Enforces hourly (50 req/h) and daily (1000 req/day) limits
    via RequestLog, blocking until a slot is available.
    """

    RATE_LIMIT_BUFFER_SECONDS = 5

    @classmethod
    def from_env(cls) -> "TiingoApiClient":
        """
        Create an instance of TiingoApiClient using environment variables.
        """
        return cls(
            base_url=os.environ["TIINGO_BASE_URL"],
            api_token=os.environ["TIINGO_API_TOKEN"],
            hourly_limit=int(os.environ.get("TIINGO_HOURLY_LIMIT", 50)),
            daily_limit=int(os.environ.get("TIINGO_DAILY_LIMIT", 1000)),
        )

    TOO_MANY_REQUESTS = 429

    def __init__(self, base_url: str, api_token: str, hourly_limit: int = 50, daily_limit: int = 1000):
        if not base_url:
            raise ValueError("base_url must be provided")
        if not api_token:
            raise ValueError("api_token must be provided")

        self.base_url = base_url
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {api_token}",
        }

    def make_request(self, endpoint: str, params=None) -> requests.Response:
        """
        Make a request to the Tiingo API with rate limiting.

        Args:
            endpoint: The API endpoint to call.
            params: Query parameters for the request.

        Returns:
            The response from the API.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        max_retries = 10
        retry_count = 0

        while True:
            now = timezone.now()
            start_of_hour = now.replace(minute=0, second=0, microsecond=0)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

            hourly_key = f"tiingo_api_hourly_{int(start_of_hour.timestamp())}"
            daily_key = f"tiingo_api_daily_{int(start_of_day.timestamp())}"

            cache.add(hourly_key, 0, timeout=3600)
            cache.add(daily_key, 0, timeout=86400)

            try:
                hourly_count = cache.incr(hourly_key)
            except ValueError:
                cache.set(hourly_key, 1, timeout=3600)
                hourly_count = 1

            try:
                daily_count = cache.incr(daily_key)
            except ValueError:
                cache.set(daily_key, 1, timeout=86400)
                daily_count = 1

            if hourly_count <= self.hourly_limit and daily_count <= self.daily_limit:
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                except requests.RequestException as e:
                    raise ApiClientError(f"Request failed for {url}: {e}") from e

                if response.status_code == self.TOO_MANY_REQUESTS:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise ApiClientError(f"Max retries ({max_retries}) exceeded for {url}")
                    logger.warning(
                        "%s 429 Too Many Requests — waiting 601s (attempt %d/%d)", LOG_PREFIX, retry_count, max_retries
                    )
                    time.sleep(601)
                    continue

                if not response.ok:
                    raise ApiClientError(
                        f"Request to {url} failed with status {response.status_code}: {response.text[:200]}"
                    )

                return response

            cache.decr(hourly_key)
            cache.decr(daily_key)

            wait_seconds = self._seconds_until_next_slot(now, start_of_hour, start_of_day, hourly_count, daily_count)
            logger.info("%s Rate limit reached, waiting %ds", LOG_PREFIX, wait_seconds)
            time.sleep(wait_seconds)

    def _seconds_until_next_slot(self, now, start_of_hour, start_of_day, hourly_count, daily_count):
        start_of_next_hour = start_of_hour + timedelta(hours=1)
        start_of_next_day = start_of_day + timedelta(days=1)

        seconds_until_hour_reset = 0
        seconds_until_day_reset = 0

        if hourly_count >= self.hourly_limit:
            seconds_until_hour_reset = (start_of_next_hour - now).total_seconds()

        if daily_count >= self.daily_limit:
            seconds_until_day_reset = (start_of_next_day - now).total_seconds()

        return int(round(max(seconds_until_hour_reset, seconds_until_day_reset))) + self.RATE_LIMIT_BUFFER_SECONDS
