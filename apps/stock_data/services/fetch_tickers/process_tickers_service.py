import logging

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from apps.stock_data.models.tickers_models import SecTicker

LOG_PREFIX = "[Process Tickers]"
logger = logging.getLogger(__name__)


class ProcessTickersService:
    """
    Service for processing, cleaning, and deduplicating ticker data.
    """

    def process_all_tickers(self) -> None:
        """Orchestrate all ticker processing steps."""
        logger.info("%s Starting tickers processing...", LOG_PREFIX)

        self._set_update_field_for_inactive_status_records(SecTicker)
        self._set_exclude_status_to_trusts_and_etf(SecTicker)
        self._deduplicate_by_shortest_ticker(SecTicker)
        self._set_excluded_status_for_non_common_stock(SecTicker)

        # Check for any remaining duplicates (logging only)
        self._check_for_duplicated_tickers(SecTicker)

        logger.info("%s Tickers processing completed.", LOG_PREFIX)

    def _set_exclude_status_to_trusts_and_etf(self, model_class) -> None:
        """Mark tickers with specific strings in their name field as excluded."""
        count = model_class.objects.filter(
            Q(name__contains=" Trust")
            | Q(name__contains=" TRUST")
            | Q(name__contains=" Fund")
            | Q(name__contains=" Acquisition ")
            | Q(name__contains=" Right")
            | Q(name__contains=" Warrant")
            | Q(name__endswith=" ETF")
            | Q(name__contains=" ETF ")
        ).update(status=model_class.EXCLUDED)
        logger.info("%s Marked %d tickers as excluded in %s", LOG_PREFIX, count, model_class._meta.model_name)

    def _set_update_field_for_inactive_status_records(self, model_class) -> None:
        """Update records with status INACTIVE and null updated field to current date."""
        count = model_class.objects.filter(status=model_class.INACTIVE, updated__isnull=True).update(
            updated=timezone.now()
        )
        logger.info("%s Updated %d INACTIVE records in %s", LOG_PREFIX, count, model_class._meta.model_name)

    def _check_for_duplicated_tickers(self, model_class):
        """Check for duplicated tickers and log if any exist."""
        duplicated_tickers = (
            model_class.objects.filter(status=model_class.ACTIVE)
            .values("ticker")
            .annotate(count=models.Count("ticker"))
            .filter(count__gt=1)
        )

        if duplicated_tickers.exists():
            ticker_list = [item["ticker"] for item in duplicated_tickers]
            logger.warning(
                "%s Found %d duplicated tickers in %s: %s",
                LOG_PREFIX,
                duplicated_tickers.count(),
                model_class._meta.model_name,
                ", ".join(ticker_list),
            )
        else:
            logger.info("%s No duplicated tickers found in %s.", LOG_PREFIX, model_class._meta.model_name)

    def _deduplicate_by_shortest_ticker(self, model_class) -> None:
        """Deduplicate records by CIK, keeping the shortest ticker string."""
        grouped_records = {}
        # Use .iterator() for memory safety on large datasets
        tickers_with_cik = (
            model_class.objects.filter(cik__isnull=False, updated__isnull=True)
            .values("cik", "ticker", "id")
            .order_by("cik")
            .iterator()
        )

        for ticker in tickers_with_cik:
            cik = ticker["cik"]
            if cik not in grouped_records:
                grouped_records[cik] = []
            grouped_records[cik].append(ticker)

        all_ids_to_deactivate = []
        for _cik, records in grouped_records.items():
            if len(records) <= 1:
                continue

            shortest_ticker_record = min(records, key=lambda x: len(x["ticker"]))
            ids_to_exclude = [r["id"] for r in records if r["id"] != shortest_ticker_record["id"]]
            all_ids_to_deactivate.extend(ids_to_exclude)

        updated_count = 0
        if all_ids_to_deactivate:
            with transaction.atomic():
                # Process in chunks if list is extremely large (Django does this mostly, but good to be aware)
                updated_count = model_class.objects.filter(id__in=all_ids_to_deactivate).update(
                    status=model_class.DEDUPLICATED
                )

        logger.info(
            "%s Successfully updated %d records in %s with DEDUPLICATED status",
            LOG_PREFIX,
            updated_count,
            model_class._meta.model_name,
        )

    def _set_excluded_status_for_non_common_stock(self, model_class) -> None:
        """Set status to EXCLUDED for tickers with non-A-Z characters."""
        count = model_class.objects.filter(ticker__regex=r"[^A-Z]", updated__isnull=True).update(
            status=model_class.EXCLUDED
        )
        logger.info("%s Set status to EXCLUDED for %d tickers in %s", LOG_PREFIX, count, model_class._meta.model_name)
