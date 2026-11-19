from django.db import connection, transaction

from apps.stock_data.models import HistoricalStockPrice, StockScreenerStats, Ticker


class ScreenerStatsRepository:
    """
    Data access layer for stock screener statistics.
    Contains all raw SQL and database write operations.
    """

    _TICKER_STATS_QUERY = f"""
        WITH RankedPrices AS (
            SELECT 
                hsp.ticker,
                hsp.close_price,
                hsp.date,
                ROW_NUMBER() OVER(PARTITION BY hsp.ticker ORDER BY hsp.date DESC) as rn,
                t.name as company_name
            FROM {HistoricalStockPrice._meta.db_table} hsp
            JOIN {Ticker._meta.db_table} t ON hsp.ticker = t.ticker
            WHERE hsp.date >= (CURRENT_DATE - INTERVAL '1 year')
              AND t.status = {Ticker.ACTIVE}
        ),
        Aggregated AS (
            SELECT
                ticker,
                MAX(company_name) as company_name,
                MAX(CASE WHEN rn = 1 THEN close_price END) as latest_close,
                MAX(close_price) as high_52w,
                MIN(close_price) as low_52w,
                MAX(CASE WHEN rn = 2 THEN close_price END) as close_rn2,
                MAX(CASE WHEN rn = 3 THEN close_price END) as close_rn3,
                MAX(CASE WHEN rn = 4 THEN close_price END) as close_rn4,
                MAX(CASE WHEN rn = 5 THEN close_price END) as close_rn5,
                MAX(CASE WHEN rn = 6 THEN close_price END) as close_rn6,
                MAX(CASE WHEN rn = 7 THEN close_price END) as close_rn7
            FROM RankedPrices
            GROUP BY ticker
        )
        SELECT * FROM Aggregated
        WHERE latest_close IS NOT NULL
    """

    def fetch_raw_ticker_stats(self) -> list[dict]:
        """
        Runs the aggregation query and returns raw rows as list of dicts.
        """
        with connection.cursor() as cursor:
            cursor.execute(self._TICKER_STATS_QUERY)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def replace_all_stats(self, stats_instances: list[StockScreenerStats]) -> int:
        """
        Atomically replaces all stats with the given list of model instances.
        Returns the count of saved records.
        """
        with transaction.atomic():
            StockScreenerStats.objects.all().delete()
            StockScreenerStats.objects.bulk_create(stats_instances, batch_size=500)

        return len(stats_instances)
