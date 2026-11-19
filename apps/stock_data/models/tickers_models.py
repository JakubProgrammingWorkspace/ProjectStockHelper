from django.db import models
from django.utils import timezone


class CommonTicker(models.Model):
    """
    Represents a stock ticker symbol with associated company information.

    This model stores financial data from the SEC including CIK, company name,
    ticker symbol, and exchange information along with timestamps for tracking.
    """

    # Status constants
    ACTIVE = 1
    INACTIVE = 0
    EXCLUDED = 2
    DEDUPLICATED = 3

    cik = models.BigIntegerField(db_index=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=10, unique=True)
    exchange = models.CharField(max_length=50)
    status = models.SmallIntegerField()
    updated = models.DateField(null=True, default=None)
    created = models.DateField(default=timezone.now)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.ticker} - {self.name}"

    # Format CIK to 10 digits with leading zeros and 'CIK' prefix
    # if add @property it acts as property, if not it is a regular method
    # access property: formatted_cik, access regular method: formatted_cik()
    @property
    def formatted_cik(self):
        return f"{self.cik:010d}"


class SecTicker(CommonTicker):
    class Meta:
        db_table = "sec_tickers"
        verbose_name = "SEC Ticker"
        verbose_name_plural = "SEC Tickers"


class TickerQuerySet(models.QuerySet):
    def active(self) -> "TickerQuerySet":
        """Retrieve all active tickers with a valid CIK."""
        return self.filter(status=CommonTicker.ACTIVE, cik__isnull=False)


class Ticker(SecTicker):
    """
    Read model for tickers, providing a unified interface for active tickers.
    Reads from the sec_tickers table.
    """

    objects = TickerQuerySet.as_manager()

    class Meta:
        proxy = True
        verbose_name = "Ticker"
        verbose_name_plural = "Tickers"


class MassiveTicker(CommonTicker):
    class Meta:
        db_table = "massive_tickers"


