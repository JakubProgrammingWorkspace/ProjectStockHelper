import json
import logging
import re

import sec2md
from django.db import IntegrityError, OperationalError

from apps.stock_data.dto.sec_submission_dto import SecSubmissionDTO
from apps.stock_data.models.sec_models import Sec10QLLMAnalysis
from apps.stock_data.services.document_processor.llm_10q_prompt_config import TenQPromptConfig
from apps.stock_data.services.document_processor.llm_handler_service import LLMHandler
from apps.stock_data.services.file_service import FileService

LOG_PREFIX = "[Process 10-Q Documents]"
logger = logging.getLogger(__name__)


class TenQDocumentProcessor:
    def __init__(self, llm_handler: LLMHandler):
        self.llm_handler = llm_handler

    def process_single(self, dto: SecSubmissionDTO):
        """Convert 10-Q document to markdown and extract financials via LLM."""
        if not dto.filepath:
            logger.error("%s No filepath provided for 10-Q processing.", LOG_PREFIX)
            return

        content = self._load_from_file(dto.filepath)
        if not content:
            return

        md_content = self._convert_to_markdown(content)
        if not md_content:
            return

        md_content = self._convert_negative_numbers(md_content)

        response = self.llm_handler.ask(TenQPromptConfig(md_content))
        if response:
            dto.llm_response.append(response)
            self._save_to_db(dto, response)

    def _convert_negative_numbers(self, text: str) -> str:
        if not text:
            return text
        return re.sub(r"\(\s*([0-9][0-9,\.]*)\s*\)", r"-\1", text)

    def _save_to_db(self, dto: SecSubmissionDTO, response: str):
        try:
            Sec10QLLMAnalysis.objects.update_or_create(
                ticker=dto.ticker,
                filing_date=dto.filing_date,
                defaults={
                    "cik": dto.cik,
                    "llm_response": json.loads(response),
                },
            )
        except json.JSONDecodeError as e:
            logger.error("%s LLM returned invalid JSON for %s: %s", LOG_PREFIX, dto.ticker, e)
        except (IntegrityError, OperationalError) as e:
            logger.error("%s DB error saving 10-Q LLM analysis to DB for %s: %s", LOG_PREFIX, dto.ticker, e)

    @staticmethod
    def _load_from_file(file_path: str) -> str | None:
        return FileService.read_content(file_path, True)

    @staticmethod
    def _convert_to_markdown(html_content):
        try:
            return sec2md.convert_to_markdown(html_content)
        except Exception:
            logger.exception("%s Error converting document to markdown via sec2md", LOG_PREFIX)
        return None
