import logging
import os
import time

import requests
from django.core.cache import cache

from apps.stock_data.services.api_clients.exceptions import ApiClientError

LOG_PREFIX = "[SEC API Client]"
RATE_LIMIT_BACKOFF_SECONDS = 601
logger = logging.getLogger(__name__)


class SecApiClient:
    """
    Service class to manage API request limits for SEC API.

    This service handles rate limiting logic for SEC API requests
    by checking the 10 requests per second limit based on request logs.
    """

    @classmethod
    def from_env(cls, base_url_env_var: str = "SEC_API_BASE_URL"):
        """
        Create an instance of SecApiClient using environment variables.
        """
        return cls(
            base_url=os.environ.get(base_url_env_var),
            app_name=os.environ.get("APP_NAME"),
            sec_email=os.environ.get("SEC_EMAIL"),
            limit=int(os.environ.get("SEC_API_LIMIT", 10)),
        )

    def __init__(self, base_url: str, app_name: str, sec_email: str, limit: int = 10):
        if not base_url:
            raise ValueError("base_url must be provided")
        if not app_name:
            raise ValueError("app_name must be provided")
        if not sec_email:
            raise ValueError("sec_email must be provided")

        self.base_url = base_url.rstrip("/")
        self.app_name = app_name
        self.sec_email = sec_email
        self.limit = limit

        self.headers = {
            "User-Agent": f"{self.app_name} {self.sec_email}",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def make_request(self, endpoint: str, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        max_retries = 10
        retry_count = 0

        while True:
            now_sec = int(time.time())
            cache_key = f"sec_rate_limit_{now_sec}"

            cache.add(cache_key, 0, timeout=2)
            try:
                count = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=2)
                count = 1

            if count <= self.limit:
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                except requests.RequestException as e:
                    raise ApiClientError(f"Request failed for {url}: {e}") from e

                if response.status_code == 429:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise ApiClientError(f"Max retries ({max_retries}) exceeded for {url}")
                    logger.warning(
                        "%s SEC API: 429 Too Many Requests — waiting %ds (attempt %d/%d)",
                        LOG_PREFIX,
                        RATE_LIMIT_BACKOFF_SECONDS,
                        retry_count,
                        max_retries,
                    )
                    time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                    continue

                if not response.ok:
                    raise ApiClientError(
                        f"Request to {url} failed with status {response.status_code}: {response.text[:200]}"
                    )

                return response
            else:
                wait_time = max((now_sec + 1) - time.time() + 0.05, 0.01)

                logger.info("%s Limit reached, waiting %.2fs...", LOG_PREFIX, wait_time)
                time.sleep(wait_time)
