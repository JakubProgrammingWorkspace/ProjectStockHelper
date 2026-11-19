from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.models.sec_models import SecFinancialData, SecProcessedFinancialData
from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.fetch_historical_prices import YFinanceHistoricalPricesService
from apps.stock_data.services.fetch_sec_financial_data.fetch_sec_financial_data_service import (
    FetchSecFinancialDataService,
)
from apps.stock_data.services.price_bundler import PriceBundler


@method_decorator(csrf_exempt, name="dispatch")
class StockDataView(View):
    def get(self, request, ticker_symbol=None):
        # Get stock prices for the selected ticker
        try:
            ticker = Ticker.objects.get(ticker=ticker_symbol)
        except Ticker.DoesNotExist:
            return JsonResponse({"error": "Ticker not found"}, status=404)

        # Get time interval from query parameters
        time_interval = request.GET.get("time_interval", "1D")

        # Get historical stock prices
        price_data = (
            HistoricalStockPrice.objects.filter(ticker=ticker.ticker)
            .order_by("date")
            .values("date", "open_price", "high_price", "low_price", "close_price", "volume")
        )

        # Convert to list of dictionaries
        price_list = list(price_data)

        # Apply time interval grouping
        price_list = PriceBundler.bundle(time_interval, price_list)

        return JsonResponse(
            {
                "ticker": ticker_symbol,
                "time_interval": time_interval,
                "prices": price_list,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class AdditionalFinancialDataView(View):
    def get(self, request, ticker_symbol=None):
        try:
            ticker = Ticker.objects.get(ticker=ticker_symbol)
        except Ticker.DoesNotExist:
            return JsonResponse({"error": "Ticker not found"}, status=404)

        # Get financial data type from query parameters
        data_type = request.GET.get("data_type")

        # Handle different data types

        # Determine which tags to fetch based on data_type
        tag_ids = []
        if data_type == "revenue":
            tag_ids = [SecFinancialData.TagId.SALES_REVENUE_NET]
        elif data_type == "net_income":
            tag_ids = [SecFinancialData.TagId.NET_INCOME_LOSS]
        elif data_type == "revenue_ttm":
            tag_ids = [SecProcessedFinancialData.TagId.SALES_REVENUE_NET_TTM]
        elif data_type == "net_income_ttm":
            tag_ids = [SecProcessedFinancialData.TagId.NET_INCOME_LOSS_TTM]

        # Get financial data for the specified tags
        financial_data = (
            SecProcessedFinancialData.objects.filter(cik=ticker.cik, tag_id__in=tag_ids)
            .order_by("end_date")
            .values("end_date", "value")
        )

        # Convert to list of dictionaries
        financial_list = list(financial_data)

        return JsonResponse({"ticker": ticker_symbol, "financials": financial_list})


@method_decorator(csrf_exempt, name="dispatch")
class TickersListView(View):
    def get(self, request):
        tickers = Ticker.objects.active().values("ticker", "name").order_by("ticker")

        return JsonResponse({"tickers": list(tickers)})


@method_decorator(csrf_exempt, name="dispatch")
class RefreshTickerDataView(View):
    def get(self, request, ticker_symbol):
        try:
            ticker = Ticker.objects.get(ticker=ticker_symbol)
        except Ticker.DoesNotExist:
            return JsonResponse({"error": "Ticker not found"}, status=404)

        try:
            # Refresh SEC financial data
            sec_api_client = SecApiClient.from_env()
            sec_service = FetchSecFinancialDataService(sec_api_client)
            sec_service.refresh_ticker_data(ticker)

            # Refresh Price data

            fetcher = YFinanceHistoricalPricesService()
            count = fetcher.fetch_and_save_ticker_prices(ticker.ticker)
            return JsonResponse(
                {
                    "message": f"Successfully refreshed {count} records and SEC data for {ticker_symbol}",
                    "records_updated": count,
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def dashboard_view(request):
    """Serve the main dashboard page"""
    return render(request, "dashboard.html")


@method_decorator(csrf_exempt, name="dispatch")
class ScreenerAPIView(View):
    def get(self, request):
        fifty_two_week = request.GET.get("fiftyTwoWeek", "any")
        period_change = request.GET.get("periodChange", "any")
        order_by = request.GET.get("orderBy", "ticker")
        order_dir = request.GET.get("orderDir", "asc")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("pageSize", 50))

        from apps.stock_data.services.screener_service import ScreenerService

        try:
            results_data = ScreenerService().get_screened_tickers(
                fifty_two_week=fifty_two_week,
                period_change=period_change,
                order_by=order_by,
                order_dir=order_dir,
                page=page,
                page_size=page_size,
            )
            return JsonResponse(results_data)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
