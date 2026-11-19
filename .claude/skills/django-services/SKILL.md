---
name: django-services
description: "Patterns and conventions for writing Django service classes, management commands, API clients, DTOs, and error handling in this codebase. Use this skill whenever writing or editing a service, command, API client, or DTO — even if the user just says 'add a service', 'create a command', 'call this API', or 'fetch and save data'. Also applies when handling errors from external requests or structuring data from API responses."
---


# Django Services

## Management Commands

Commands are thin wrappers — no business logic allowed. Instantiate dependencies
here using `os.environ.get(...)`, then call exactly one public service method.

```python
class Command(BaseCommand):
    help = 'Short description of what this command does'

    def handle(self, *args, **options):
        api_client = MassiveMarketDataApiClient(base_url=os.environ.get('MASSIVE_API_BASE_URL'))
        TickerIngestionService(api_client=api_client).ingest_current_tickers()
```

---

## Service Layer

- Plain Python class — no Django base class, no model inheritance
- Constructor-based dependency injection only; never read `os.environ` directly
- **Mandatory Dependencies**: All dependencies (Repositories, API Clients, etc.) must be passed as mandatory constructor parameters. Do **not** provide default values or instantiate them inside the service.
- One public method with unique and descriptive name that orchestrates the full flow
- **Strict DRY Principle**: If a service provides both an orchestration method (e.g., for processing multiple entities) and a single-entity method, the orchestration method **must** delegate to the single-entity method to avoid logic duplication.
- All helpers are private and descriptive: `_fetch_data_from_provider`
- Use complete type annotations for all parameter and return values
- Provide comprehensive docstrings for public methods
- Use descriptive variable names (avoid `i`, `data`, `res`)

```python
LOG_PREFIX = '[Ticker Ingestion]'
logger = logging.getLogger(__name__)

class TickerIngestionService:
    ENDPOINT_TICKERS = '/v3/reference/tickers'

    def __init__(self, api_client: MassiveMarketDataApiClient):
        self.api_client = api_client

    def fetch_and_persist_market_tickers(self) -> int:
        """
        Orchestrate the complete flow of fetching market tickers and saving to DB.
        
        Returns:
            int: Number of tickers successfully processed
        """
        raw_api_response_data = self._fetch_active_tickers_from_api()
        if raw_api_response_data is None:
            return 0
            
        # Simple CRUD: Skip DTO, map directly to models
        ticker_model_instances = self._map_api_response_to_ticker_models(raw_api_response_data)
        saved_count = self._save_ticker_instances_to_database(ticker_model_instances)
        return saved_count

    def _fetch_active_tickers_from_api(self): ...
    def _map_api_response_to_ticker_models(self, response_data): ...
    def _save_ticker_instances_to_database(self, instances): ...
```

---

## API Client Pattern

One class per external API; handles transport only — no business logic, no model access.

- Rate-limit via `django.core.cache` (Redis): track requests atomically using `cache.incr()` and `cache.add()`, enforcing limit buckets without hitting the relational database.
- All `requests.get()` calls **must** include `timeout=10`.
- Use the **Exception Translation** pattern: catch `requests.RequestException` inside `make_request()` and re-raise as `ApiClientError`. This keeps the `requests` library as an internal implementation detail — services never import it.

```python
from apps.stock_data.services.api_clients.exceptions import ApiClientError

class SomeApiClient:
    def make_request(self, endpoint: str, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
        except requests.RequestException as e:
            raise ApiClientError(f"Request failed for {url}: {e}") from e
        return response
```

The custom exception lives at `apps/stock_data/services/api_clients/exceptions.py`.

---

## DTO Pattern

Use DTOs **only for complex business flows** (e.g., orchestrating multiple services, complex data transformations across multiple domains). For **simple CRUD operations** (e.g., saving tickers, stock prices, or raw API data directly to a model), skip the DTO and map API responses directly to model instances or use model methods.

```python
# Use for complex flows
from dataclasses import dataclass
from typing import Optional

@dataclass
class ComplexAnalyticsDto:
    ticker: str
    trend_score: float
    signal_type: str
```

- Skip DTOs for simple API-to-Model saves.
- Plain `@dataclass` for DTOs — no Django model imports.
- Field names in `snake_case`.
- Validation should happen in the service or via Pydantic if necessary for the complex flow.

---

## Error Handling

### Exception Translation (API Client → Service)

API clients translate low-level `requests.RequestException` into `ApiClientError`.
Services **never** import `requests` — they catch `ApiClientError` for transport errors
and `ValueError` for JSON parsing failures.

```python
from apps.stock_data.services.api_clients.exceptions import ApiClientError

# Service boundary — catch translated exceptions
try:
    response = self.api_client.make_request(endpoint)
    response.raise_for_status()
    data = response.json()
except ApiClientError as e:
    logger.error("%s Transport error: %s", LOG_PREFIX, e)
    return 0
except ValueError as e:
    logger.error("%s Failed to parse response: %s", LOG_PREFIX, e)
    return 0
```

### Rules

- Catch at the **service boundary**, not deep inside helpers.
- Log with `LOG_PREFIX` context; return `None`, `0`, or `[]` on failure — let callers handle missing data.
- Do **not** use bare `except Exception` — always catch specific exception types.
- Do not re-raise unless the caller needs to decide what to do (e.g., management commands that set exit codes).
- Wrap database-critical operations (status resets + bulk writes) in `transaction.atomic()` so partial failures roll back cleanly.
