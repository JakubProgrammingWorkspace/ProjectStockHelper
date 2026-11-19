from django.db import models


class SecFinancialData(models.Model):
    """
    Model to store financial data from SEC API.

    This model stores the parsed financial data from SEC XBRL reports,
    including key information about net income and other financial metrics.
    """

    """
    SEC accession number Format and Structure:
    Example: 0001193125-15-118890
    The first part (e.g., 0001193125) is the CIK (Central Index Key) of the entity submitting the filing.
    The next two digits (e.g., 15) represent the year of submission (last two digits of the year, e.g., 2015).
    The final part (e.g., 118890) is a sequential count of filings submitted by that CIK in that year.
    This count typically resets to 0 at the start of each calendar year but not always.
    """

    class TagId(models.IntegerChoices):
        SALES_REVENUE_NET = 1, "Sales Revenue Net"
        NET_INCOME_LOSS = 4, "Net Income/Loss"
        COST_OF_REVENUE = 5, "Cost of Revenue"

    cik = models.BigIntegerField(help_text="Central Index Key")
    start_date = models.DateField(help_text="Start date of the reporting period")
    end_date = models.DateField(help_text="End date of the reporting period")
    value = models.BigIntegerField(help_text="Financial value")
    accession_number = models.IntegerField(help_text="SEC accession number, last part")
    fiscal_year = models.IntegerField(help_text="Fiscal year")
    fiscal_period = models.CharField(max_length=10, help_text="Fiscal period (e.g., FY, Q1, Q2)")
    form_type = models.CharField(max_length=10, help_text="Form type (e.g., 10-K, 10-Q)")
    filed_date = models.DateField(help_text="Date when the report was filed")
    tag_id = models.PositiveSmallIntegerField(help_text="SEC financial tag ID (1-99)")

    # Add a unique constraint to prevent duplicate records
    class Meta:
        unique_together = ("cik", "start_date", "end_date", "tag_id")
        db_table = "sec_financial_data"

    def __str__(self):
        return f"SEC Data: {self.cik} - {self.form_type} ({self.fiscal_year}-{self.fiscal_period})"


class SecProcessedFinancialData(models.Model):
    class TagId(models.IntegerChoices):
        SALES_REVENUE_NET_TTM = 21, "Sales Revenue Net TTM"
        NET_INCOME_LOSS_TTM = 24, "Net Income/Loss TTM"

    cik = models.BigIntegerField(help_text="Central Index Key")
    end_date = models.DateField(help_text="End date of the reporting period")
    value = models.BigIntegerField(help_text="Financial value")
    tag_id = models.PositiveSmallIntegerField(help_text="SEC financial tag ID (1-99)")

    # Add a unique constraint to prevent duplicate records
    class Meta:
        unique_together = ("cik", "end_date", "tag_id")
        db_table = "sec_processed_financial_data"

    def __str__(self):
        return f"SEC processed: {self.cik} - {self.fiscal_period} ({self.end_date}-{self.tag_id})"


class Sec10QLLMAnalysis(models.Model):
    ticker = models.CharField(max_length=20)
    cik = models.CharField(max_length=20)
    filing_date = models.CharField(max_length=20)
    llm_response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sec_10q_llm_analysis"
        unique_together = [("ticker", "filing_date")]

    def __str__(self):
        return f"10-Q LLM Analysis: {self.ticker} ({self.filing_date})"
