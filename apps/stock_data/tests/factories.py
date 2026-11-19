import factory

from apps.stock_data.models.historical_price_models import HistoricalStockPrice
from apps.stock_data.models.sec_models import SecFinancialData
from apps.stock_data.models.tickers_models import SecTicker, Ticker


class SecTickerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SecTicker

    cik = factory.Sequence(lambda n: 1000 + n)
    name = factory.Faker("company")
    ticker = factory.Sequence(lambda n: f"TICK{n}")
    exchange = "NASDAQ"
    status = SecTicker.ACTIVE

class HistoricalStockPriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HistoricalStockPrice

    date = factory.Faker("date_this_year")
    open_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    high_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    low_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    close_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    volume = factory.Faker("pyint", min_value=1000, max_value=1000000)
    ticker = factory.Sequence(lambda n: f"TICK{n}")

class SecFinancialDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SecFinancialData

    cik = factory.Sequence(lambda n: 100000 + n)
    start_date = factory.Faker("date_this_year")
    end_date = factory.Faker("date_this_year")
    value = factory.Faker("pyint", min_value=1000000, max_value=1000000000)
    accession_number = factory.Sequence(lambda n: 100000 + n)
    fiscal_year = 2023
    fiscal_period = "FY"
    form_type = "10-K"
    filed_date = factory.Faker("date_this_year")
    tag_id = SecFinancialData.TagId.NET_INCOME_LOSS

class TickerFactory(SecTickerFactory):
    class Meta:
        model = Ticker
