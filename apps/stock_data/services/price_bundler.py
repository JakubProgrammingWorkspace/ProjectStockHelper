from typing import Any


class PriceBundler:
    """
    Service to bundle stock price data based on time intervals.
    """

    @staticmethod
    def bundle(time_interval: str, price_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Bundle price data based on the specified time interval.

        Args:
            time_interval: The time interval to group by ('1D', '1W', '1M', '1X', or 'N D' where N is number of days)
            price_data: List of price dictionaries with date, open, high, low, close, volume

        Returns:
            List of bundled price dictionaries
        """
        if time_interval == "1D":
            return price_data

        if time_interval == "1W":
            return PriceBundler._bundle_weekly(price_data)

        if time_interval == "1M":
            return PriceBundler._bundle_monthly(price_data)

        if time_interval == "Cu":
            return PriceBundler._bundle_by_price_movement(price_data)

        # Handle custom day intervals like '2D', '3D', etc.
        if time_interval.endswith("D"):
            try:
                num_days = int(time_interval[:-1])
                if num_days > 1:
                    return PriceBundler._bundle_custom_days(price_data, num_days)
            except ValueError:
                # If parsing fails, return original data
                pass

        return price_data

    @staticmethod
    def _bundle_weekly(price_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Bundle daily price data into weekly candles.

        For each week:
        - Open price: Monday's open price
        - High price: Maximum high price of the week
        - Low price: Minimum low price of the week
        - Close price: Friday's close price
        - Date: Monday's date
        - Volume: Sum of volumes for the week

        Args:
            price_data: List of daily price dictionaries

        Returns:
            List of weekly price dictionaries
        """
        if not price_data:
            return []

        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x["date"])

        # Group by week
        weekly_bundles = []
        current_week_start = None
        week_data = []

        for price in sorted_data:
            price_date = price["date"]
            weekday = price_date.weekday()  # 0 = Monday, 6 = Sunday

            # If it's Monday, start a new week
            if weekday == 0:
                # Save previous week if exists
                if current_week_start and week_data:
                    weekly_bundles.append(PriceBundler._create_custom_candle(week_data))

                # Start new week
                current_week_start = price_date
                week_data = [price]
            else:
                # Add to current week
                week_data.append(price)

        # Don't forget the last week
        if current_week_start and week_data:
            weekly_bundles.append(PriceBundler._create_custom_candle(week_data))

        return weekly_bundles

    @staticmethod
    def _bundle_monthly(price_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Bundle daily price data into monthly candles.

        For each month:
        - Open price: First day's open price
        - High price: Maximum high price of the month
        - Low price: Minimum low price of the month
        - Close price: Last day's close price
        - Date: First day of the month
        - Volume: Sum of volumes for the month

        Args:
            price_data: List of daily price dictionaries

        Returns:
            List of monthly price dictionaries
        """
        if not price_data:
            return []

        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x["date"])

        # Group by month
        monthly_bundles = []
        current_month_start = None
        month_data = []

        for price in sorted_data:
            price_date = price["date"]

            # If it's the first day of a new month, start a new month
            if current_month_start is None or price_date.month != current_month_start.month:
                # Save previous month if exists
                if current_month_start and month_data:
                    monthly_bundles.append(PriceBundler._create_custom_candle(month_data))

                # Start new month
                current_month_start = price_date.replace(day=1)
                month_data = [price]
            else:
                # Add to current month
                month_data.append(price)

        # Don't forget the last month
        if current_month_start and month_data:
            monthly_bundles.append(PriceBundler._create_custom_candle(month_data))

        return monthly_bundles

    @staticmethod
    def _bundle_custom_days(price_data: list[dict[str, Any]], num_days: int) -> list[dict[str, Any]]:
        """
        Bundle daily price data into custom day intervals.

        For each group of N days:
        - Open price: First day's open price
        - High price: Maximum high price of the group
        - Low price: Minimum low price of the group
        - Close price: Last day's close price
        - Date: First day's date
        - Volume: Sum of volumes for the group

        Args:
            price_data: List of daily price dictionaries
            num_days: Number of days to group together

        Returns:
            List of bundled price dictionaries
        """
        if not price_data or num_days <= 1:
            return price_data

        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x["date"])

        # Group by custom day intervals
        bundled_data = []
        current_group = []
        current_group_start = None

        for price in sorted_data:
            price_date = price["date"]

            # If this is the first price or we're starting a new group
            if not current_group_start:
                current_group_start = price_date
                current_group = [price]
            else:
                # Calculate days since start of current group
                days_since_start = (price_date - current_group_start).days

                # If we've reached the group size limit, save the group
                if days_since_start >= num_days:
                    bundled_data.append(PriceBundler._create_custom_candle(current_group))
                    # Start new group
                    current_group_start = price_date
                    current_group = [price]
                else:
                    # Add to current group
                    current_group.append(price)

        # Don't forget the last group
        if current_group:
            bundled_data.append(PriceBundler._create_custom_candle(current_group))

        return bundled_data

    @staticmethod
    def _bundle_by_price_movement(price_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Bundle daily price data into candles based on price movement direction.

        Creates a new candle when consecutive closing prices change direction:
        - If current close > previous close, continue grouping in ascending direction
        - If current close < previous close, start new group (descending)
        - If current close == previous close, continue grouping (treat as same direction)

        For each group:
        - Open price: First day's open price
        - High price: Maximum high price of the group
        - Low price: Minimum low price of the group
        - Close price: Last day's close price
        - Date: First day's date
        - Volume: Sum of volumes for the group

        Args:
            price_data: List of daily price dictionaries

        Returns:
            List of price dictionaries grouped by price movement direction
        """
        if not price_data:
            return []

        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x["date"])

        if len(sorted_data) == 1:
            return sorted_data

        bundled_data = []
        ascending_group = []
        descending_group = []
        previous_close = sorted_data[0]["close_price"]

        for i in range(len(sorted_data)):
            current_price = sorted_data[i]
            current_close = current_price["close_price"]

            # Check if we should start a new group (price changed direction)
            if current_close < previous_close:
                # Price is decreasing, save any ascending group and start new descending group
                if ascending_group:
                    bundled_data.append(PriceBundler._create_custom_candle(ascending_group))
                    ascending_group = []
                descending_group.append(current_price)
            elif current_close > previous_close:
                # Price is increasing, save any descending group and start new ascending group
                if descending_group:
                    bundled_data.append(PriceBundler._create_custom_candle(descending_group))
                    descending_group = []
                ascending_group.append(current_price)
            else:
                # Price is the same, add to current group
                if ascending_group:
                    ascending_group.append(current_price)
                elif descending_group:
                    descending_group.append(current_price)
                else:
                    # If both groups are empty, start with ascending (default)
                    ascending_group.append(current_price)

            previous_close = current_close

        # Don't forget the last groups
        if ascending_group:
            bundled_data.append(PriceBundler._create_custom_candle(ascending_group))
        if descending_group:
            bundled_data.append(PriceBundler._create_custom_candle(descending_group))

        return bundled_data

    @staticmethod
    def _create_custom_candle(group_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Create a custom interval candle from grouped data.

        Args:
            group_data: List of daily price dictionaries for a group

        Returns:
            Custom interval price dictionary
        """
        if not group_data:
            return {}

        # Sort by date to ensure proper order
        sorted_group_data = sorted(group_data, key=lambda x: x["date"])

        # Get first day's data for open price
        first_day_data = sorted_group_data[0]

        # Get last day's data for close price
        last_day_data = sorted_group_data[-1]

        # Calculate max high and min low for the group
        group_high = max(day["high_price"] for day in sorted_group_data)
        group_low = min(day["low_price"] for day in sorted_group_data)

        # Sum volumes for the group
        group_volume = sum(day["volume"] for day in sorted_group_data)

        # Create custom interval candle
        custom_candle = {
            "date": first_day_data["date"],
            "open_price": first_day_data["open_price"],
            "high_price": group_high,
            "low_price": group_low,
            "close_price": last_day_data["close_price"],
            "volume": group_volume,
        }

        return custom_candle
