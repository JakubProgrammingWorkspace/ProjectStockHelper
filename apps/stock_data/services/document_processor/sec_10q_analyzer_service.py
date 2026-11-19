import logging

from apps.stock_data.dto.sec_submission_dto import SecSubmissionDTO
from apps.stock_data.models.tickers_models import Ticker
from apps.stock_data.services.api_clients.exceptions import ApiClientError
from apps.stock_data.services.api_clients.sec_api_client import SecApiClient
from apps.stock_data.services.document_processor.process_10q_documents import TenQDocumentProcessor
from apps.stock_data.services.document_processor.sec_submissions import SecSubmissions
from apps.stock_data.services.file_service import FileService

LOG_PREFIX = "[SEC 10-Q Analyzer]"
logger = logging.getLogger(__name__)


class Sec10QAnalyzerService:
    def __init__(
        self,
        sec_submissions: SecSubmissions,
        sec_api_client: SecApiClient,
        document_processor: TenQDocumentProcessor,
    ):
        self.sec_submissions = sec_submissions
        self.sec_api_client = sec_api_client
        self.document_processor = document_processor

    def analyze(self, target_ticker: str | None = None):
        """Orchestrate the full 10-Q analysis flow.

        Args:
            target_ticker: Optional ticker symbol to filter the processing to a single company.
        """
        queryset = Ticker.objects.active()
        if target_ticker:
            queryset = queryset.filter(ticker=target_ticker.upper())

        tickers = queryset.order_by("cik", "ticker").distinct("cik")

        for ticker in tickers:
            logger.info("%s Processing %s", LOG_PREFIX, ticker.ticker)
            self._analyze_single_ticker(ticker)

    def _analyze_single_ticker(self, ticker):
        submissions = self.sec_submissions.find_submissions(ticker)

        for submission in submissions:
            filepath = self._fetch_and_save_document(submission)

            if filepath:
                submission.filepath = filepath
                self.document_processor.process_single(submission)

    def _fetch_and_save_document(self, submission: SecSubmissionDTO) -> str | None:
        """Fetch the 10-Q HTML document from SEC and save to file."""
        try:
            response = self.sec_api_client.make_request(submission.document_endpoint)
            filepath = submission.create_filepath()
            # The document from SEC is likely binary/bytes in response.content
            if FileService.save_content(response.content, filepath, binary=True):
                return filepath
            else:
                logger.error("%s Failed to save 10-Q document for %s", LOG_PREFIX, submission.ticker)
                return None
        except ApiClientError as e:
            logger.error("%s Error fetching 10-Q document for %s: %s", LOG_PREFIX, submission.ticker, e)
            return None
