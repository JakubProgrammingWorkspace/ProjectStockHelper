from django.db import models


class HistoricalStockPrice(models.Model):
    """
    Model to store historical stock price data for tickers.

    This model stores daily price information including open, high, low,
    close prices and volume data for each ticker symbol.
    """

    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=10, decimal_places=4)
    high_price = models.DecimalField(max_digits=10, decimal_places=4)
    low_price = models.DecimalField(max_digits=10, decimal_places=4)
    close_price = models.DecimalField(max_digits=10, decimal_places=4)
    volume = models.BigIntegerField()
    ticker = models.CharField(max_length=10, db_index=True)

    class Meta:
        unique_together = ("ticker", "date")
        db_table = "historical_stock_price"

    def __str__(self):
        return f"{self.ticker} - {self.date}"


class StockScreenerStats(models.Model):
    """
    Model to store pre-calculated statistics for the stock screener.
    Uses a JSONField to allow flexible metrics without migrations.
    """

    ticker = models.CharField(max_length=10, primary_key=True)
    company_name = models.CharField(max_length=255)
    stats = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_screener_stats"

    def __str__(self):
        return f"Screener Stats: {self.ticker}"
