from django.urls import path

from apps.stock_data.views import (
    AdditionalFinancialDataView,
    RefreshTickerDataView,
    ScreenerAPIView,
    StockDataView,
    TickersListView,
    dashboard_view,
)

urlpatterns = [
    path("tickers/", TickersListView.as_view(), name="tickers-list"),
    path("stock-data/screener/", ScreenerAPIView.as_view(), name="stock-screener"),
    path("stock-data/<str:ticker_symbol>/", StockDataView.as_view(), name="stock-data"),
    path(
        "additional-financial-data/<str:ticker_symbol>/",
        AdditionalFinancialDataView.as_view(),
        name="additional-financial-data",
    ),
    path("refresh-ticker-data/<str:ticker_symbol>/", RefreshTickerDataView.as_view(), name="refresh-ticker-data"),
    path("", dashboard_view, name="dashboard"),
]
