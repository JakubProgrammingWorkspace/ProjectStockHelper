from django.core.management.base import BaseCommand

from apps.stock_data.constants.sec_constants import FormType
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.document_processor.llm_handler_service import LLMHandler, ProviderEnum
from apps.stock_data.services.document_processor.process_10q_documents import TenQDocumentProcessor
from apps.stock_data.services.document_processor.sec_10q_analyzer_service import Sec10QAnalyzerService
from apps.stock_data.services.document_processor.sec_submissions import SecSubmissions


class Command(BaseCommand):
    help = """
    Process 10-Q quarterly reports
    make uv -- run manage.py quarterly_report_processor --ticker AAPL
    make uv -- run manage.py quarterly_report_processor --ticker AAPL --provider openai
    make uv -- run manage.py quarterly_report_processor --ticker AAPL --provider ollama
    """
    LOG_PREFIX = "[Quarterly report processor]"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ticker",
            type=str,
            help="Specify a single ticker to process (e.g. AAPL)",
            required=False,
        )
        parser.add_argument(
            "--provider",
            type=str,
            choices=[ProviderEnum.OPENAI, ProviderEnum.OLLAMA],
            default=ProviderEnum.OPENAI,
            help="Specify which LLM provider to use (default: openai)",
        )

    def handle(self, *args, **options):
        self.stdout.write(f"{self.LOG_PREFIX} ===========STARTING==========")

        target_ticker = options.get("ticker")
        provider_type = options.get("provider")

        try:
            llm_handler = LLMHandler.from_env(provider=provider_type)
        except ValueError as e:
            self.stderr.write(f"{self.LOG_PREFIX} ERROR: {e}")
            return

        sec_api_client = SecApiClient.from_env()
        sec_www_client = SecApiClient.from_env("SEC_WWW_BASE_URL")

        sec_submissions = SecSubmissions(
            sec_api_client=sec_api_client,
            form_type=FormType.FORM_10_Q,
            max_results=1,
        )

        Sec10QAnalyzerService(
            sec_submissions=sec_submissions,
            sec_api_client=sec_www_client,
            document_processor=TenQDocumentProcessor(llm_handler),
        ).analyze(target_ticker=target_ticker)
