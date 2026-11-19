import json

from django.contrib import admin
from django.utils.html import format_html

from apps.stock_data.models.historical_price_models import HistoricalStockPrice, StockScreenerStats
from apps.stock_data.models.sec_models import Sec10QLLMAnalysis, SecFinancialData, SecProcessedFinancialData
from apps.stock_data.models.tickers_models import SecTicker


@admin.register(SecTicker)
class SecTickerAdmin(admin.ModelAdmin):
    list_display = ("ticker", "name", "display_cik", "exchange", "status_icon", "updated", "created")
    list_display_links = ("ticker", "name")
    list_filter = ("exchange", "status", "created")
    search_fields = ("ticker", "name", "cik")
    ordering = ("-created",)

    def display_cik(self, obj):
        if obj.cik is None:
            return "-"
        return f"{obj.cik:010d}"
    display_cik.short_description = "CIK"
    display_cik.admin_order_field = "cik"

    def status_icon(self, obj):
        colors = {1: "green", 0: "red"}
        color = colors.get(obj.status, "gray")
        return format_html('<b style="color: {};">{}</b>', color, obj.get_status_display() if hasattr(obj, "get_status_display") else obj.status)
    status_icon.short_description = "Status"


@admin.register(Sec10QLLMAnalysis)
class Sec10QLLMAnalysisAdmin(admin.ModelAdmin):
    list_display = ("ticker", "cik", "filing_date", "created_at")
    list_filter = ("ticker", "filing_date")
    search_fields = ("ticker", "cik")
    readonly_fields = ("formatted_llm_response", "created_at", "updated_at")
    exclude = ("llm_response",)

    def formatted_llm_response(self, obj):
        """Displays the JSON response in a readable format in the admin."""
        return format_html(
            '<pre style="background: #f4f4f4; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">{}</pre>',
            json.dumps(obj.llm_response, indent=4)
        )
    formatted_llm_response.short_description = "LLM Response Details"


@admin.register(SecFinancialData)
class SecFinancialDataAdmin(admin.ModelAdmin):
    list_display = ("cik", "tag_id", "fiscal_year", "fiscal_period", "form_type", "value", "filed_date")
    list_filter = ("form_type", "fiscal_year", "fiscal_period")
    search_fields = ("cik",)


@admin.register(SecProcessedFinancialData)
class SecProcessedFinancialDataAdmin(admin.ModelAdmin):
    list_display = ("cik", "tag_id", "end_date", "value")
    list_filter = ("tag_id",)
    search_fields = ("cik",)


@admin.register(HistoricalStockPrice)
class HistoricalStockPriceAdmin(admin.ModelAdmin):
    list_display = ("ticker", "date", "close_price", "volume")
    list_filter = ("ticker", "date")
    search_fields = ("ticker",)


@admin.register(StockScreenerStats)
class StockScreenerStatsAdmin(admin.ModelAdmin):
    list_display = ("ticker", "company_name", "last_updated")
    search_fields = ("ticker", "company_name")
    readonly_fields = ("formatted_stats", "last_updated")
    exclude = ("stats",)

    def formatted_stats(self, obj):
        return format_html(
            '<pre style="background: #f4f4f4; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">{}</pre>',
            json.dumps(obj.stats, indent=4)
        )
    formatted_stats.short_description = "Stats JSON"
