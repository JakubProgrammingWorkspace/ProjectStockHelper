class ApiClientError(Exception):
    """
    Raised by API clients when a transport-level error occurs.

    Wraps requests.RequestException and similar low-level errors so that
    service classes never need to import the `requests` library directly.
    """
