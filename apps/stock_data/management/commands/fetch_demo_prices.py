import logging

from django.core.management.base import BaseCommand, CommandError

from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.fetch_historical_prices import YFinanceHistoricalPricesService

logger = logging.getLogger(__name__)

DEMO_TICKER_SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "WMT"]


class Command(BaseCommand):
    """
    Fetch a small demo data set (default: 1 year of prices for 10 well-known stocks) from Yahoo Finance.

    Requires tickers to be loaded first (``make fetch-tickers``). Usage::

        manage.py fetch_demo_prices
        manage.py fetch_demo_prices --years 2 --tickers AAPL MSFT
    """

    help = "Fetch yfinance prices for a few well-known tickers (demo / screenshot data)"

    def add_arguments(self, parser):
        parser.add_argument("--years", type=int, default=1, help="Years of history to fetch (default: 1)")
        parser.add_argument("--tickers", nargs="+", default=DEMO_TICKER_SYMBOLS, help="Ticker symbols to fetch")

    def handle(self, *args, **options):
        requested_symbols = [symbol.upper() for symbol in options["tickers"]]
        known_symbols = set(Ticker.objects.filter(ticker__in=requested_symbols).values_list("ticker", flat=True))
        if not known_symbols:
            raise CommandError("None of the tickers exist in the database. Run `make fetch-tickers` first.")

        service = YFinanceHistoricalPricesService()
        total_saved = 0
        for symbol in requested_symbols:
            if symbol not in known_symbols:
                self.stdout.write(self.style.WARNING(f"Skipping {symbol}: not in the ticker table"))
                continue
            saved_count = service.fetch_and_save_ticker_prices(symbol, lookback_years=options["years"])
            self.stdout.write(f"{symbol}: {saved_count} records")
            total_saved += saved_count

        self.stdout.write(self.style.SUCCESS(f"Done. Total records saved: {total_saved}"))
