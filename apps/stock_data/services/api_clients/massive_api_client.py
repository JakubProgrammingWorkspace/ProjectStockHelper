import logging
import os
import time

import requests
from django.core.cache import cache

from apps.stock_data.services.api_clients.exceptions import ApiClientError

LOG_PREFIX = "[Massive API]"
logger = logging.getLogger(__name__)


class MassiveApiClient:
    """
    API client for Massive API. Handles making requests and adding the API key.
    """

    @classmethod
    def from_env(cls):
        """
        Create an instance of MassiveApiClient using environment variables.
        """
        return cls(
            base_url=os.environ.get("MASSIVE_BASE_URL"),
            api_key=os.environ.get("MASSIVE_API_KEY"),
            api_limit=int(os.environ.get("MASSIVE_API_MINUTE_LIMIT", 5)),
        )

    def __init__(self, base_url: str, api_key: str, api_limit: int):
        if not base_url:
            raise ValueError("base_url must be provided")
        if not api_key:
            raise ValueError("api_key must be provided")

        self.base_url = base_url
        self.api_key = api_key
        self.api_limit = api_limit

    def make_request(self, endpoint: str, params=None):
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        if params is None:
            params = {}

        params["apiKey"] = self.api_key

        max_retries = 10
        retry_count = 0

        while True:
            now_sec = int(time.time())
            # Create a 60-second time window
            window = now_sec // 60
            cache_key = f"massive_rate_limit_{window}"

            # The cache will hold the count for at least the length of the window
            cache.add(cache_key, 0, timeout=62)
            try:
                count = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=62)
                count = 1

            if count <= self.api_limit:
                logger.debug("%s Making request to %s", LOG_PREFIX, url)
                try:
                    response = requests.get(url, params=params, timeout=10)
                except requests.RequestException as e:
                    raise ApiClientError(f"Request failed for {url}: {e}") from e

                if response.status_code == 429:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise ApiClientError(f"Max retries ({max_retries}) exceeded for {url}")
                    logger.warning(
                        "%s 429 Too Many Requests — waiting 60s (attempt %d/%d)", LOG_PREFIX, retry_count, max_retries
                    )
                    time.sleep(60)
                    continue

                if not response.ok:
                    raise ApiClientError(
                        f"Request to {url} failed with status {response.status_code}: {response.text[:200]}"
                    )

                return response
            else:
                # Wait until the start of the next window
                wait_time = max(((window + 1) * 60) - time.time() + 0.05, 0.01)
                logger.debug(
                    "%s Minute rate limit reached (%d/%d), waiting %.2fs", LOG_PREFIX, count, self.api_limit, wait_time
                )
                time.sleep(wait_time)
