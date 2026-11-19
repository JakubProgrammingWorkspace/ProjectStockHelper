from typing import Any

from apps.stock_data.models import StockScreenerStats


class ScreenerService:
    """
    Service for executing the stock screener filters using pre-calculated stats.
    Acts as a controller/reader service.
    """

    def get_screened_tickers(
        self,
        fifty_two_week: str = "any",
        period_change: str = "any",
        order_by: str = "priceChange",
        order_dir: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """
        Filters and returns tickers based on criteria with pagination.
        """
        # If all selectors are "any", return nothing
        if fifty_two_week == "any" and period_change == "any":
            return {"results": [], "total_count": 0}

        # Fetch all pre-calculated stats
        all_stats = StockScreenerStats.objects.all()

        filtered_results = []
        for item in all_stats:
            # Reconstruct the row dict for the filters
            row_dict = {"ticker": item.ticker, "company_name": item.company_name, **item.stats}

            if self._passes_filters(row_dict, fifty_two_week, period_change):
                filtered_results.append(row_dict)

        # Sorting
        if order_by == "priceChange":
            reverse = order_dir == "desc"
            sort_field = "chg_1d_pct"
            if period_change != "any":
                parts = period_change.split("_")
                if len(parts) == 2:
                    sort_field = f"chg_{parts[1]}_pct"

            filtered_results.sort(key=lambda x: x.get(sort_field) or 0.0, reverse=reverse)
        else:
            reverse = order_dir == "desc"
            filtered_results.sort(key=lambda x: x["ticker"], reverse=reverse)

        total_count = len(filtered_results)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "results": filtered_results[start:end],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
        }

    def _passes_filters(self, row: dict[str, Any], fifty_two_week: str, period_change: str) -> bool:
        latest = row.get("latest_close")
        if not latest:
            return False

        latest = float(latest)
        high = float(row.get("high_52w", 0))
        low = float(row.get("low_52w", 0))

        # 52-week checks
        if fifty_two_week == "new_high":
            if latest < high:
                return False
        elif fifty_two_week == "new_low":
            if latest > low:
                return False
        elif fifty_two_week == "0-3_below":
            if not (0.97 * high <= latest <= high):
                return False
        elif fifty_two_week == "0-5_below":
            if not (0.95 * high <= latest <= high):
                return False
        elif fifty_two_week == "0-10_below":
            if not (0.90 * high <= latest <= high):
                return False

        # Period change checks
        if period_change != "any":
            try:
                direction, period = period_change.split("_")
                days = int(period.replace("d", ""))

                change_pct = row.get(f"chg_{days}d_pct")

                if change_pct is None:
                    return False

                if direction == "up" and change_pct <= 0:
                    return False
                if direction == "down" and change_pct >= 0:
                    return False
            except (ValueError, TypeError, KeyError):
                return False

        return True
