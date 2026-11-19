from apps.stock_data.models.sec_models import SecFinancialData


class FiscalPeriod:
    FY = "FY"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class FormType:
    FORM_8_K = "8-K"
    FORM_10_Q = "10-Q"
    FORM_10_K = "10-K"
    FORM_20_F = "20-F"
    FORM_6_K = "6-K"


SEC_TAG_MAPPING = {
    "SalesRevenueNet": SecFinancialData.TagId.SALES_REVENUE_NET,
    "RevenueFromContractWithCustomerExcludingAssessedTax": SecFinancialData.TagId.SALES_REVENUE_NET,
    "Revenues": SecFinancialData.TagId.SALES_REVENUE_NET,
    "NetIncomeLoss": SecFinancialData.TagId.NET_INCOME_LOSS,
}
