import os
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.stock_data.services.document_processor.llm_handler_service import ProviderEnum


class TestQuarterlyReportProcessorCommand(TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "LLM_API_MODEL": "test-model",
            "LLM_API_KEY": "test-key",
            "LLM_API_BASE_URL": "https://test.api",
            "SEC_EMAIL": "test@example.com"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("apps.stock_data.management.commands.quarterly_report_processor.LLMHandler")
    @patch("apps.stock_data.management.commands.quarterly_report_processor.Sec10QAnalyzerService")
    @patch("apps.stock_data.management.commands.quarterly_report_processor.SecApiClient")
    @patch("apps.stock_data.management.commands.quarterly_report_processor.SecSubmissions")
    def test_command_uses_openai_adapter_by_default(self, mock_submissions, mock_api_client, mock_analyzer, mock_handler):
        # Setup mocks
        mock_analyzer_instance = mock_analyzer.return_value

        # Call command
        call_command("quarterly_report_processor", ticker="AAPL")

        # Verify LLMHandler.from_env was called with OpenAI provider (default)
        mock_handler.from_env.assert_called_once_with(provider=ProviderEnum.OPENAI)

    @patch("apps.stock_data.management.commands.quarterly_report_processor.LLMHandler")
    @patch("apps.stock_data.management.commands.quarterly_report_processor.Sec10QAnalyzerService")
    @patch("apps.stock_data.management.commands.quarterly_report_processor.SecApiClient")
    @patch("apps.stock_data.management.commands.quarterly_report_processor.SecSubmissions")
    def test_command_uses_ollama_adapter_with_flag(self, mock_submissions, mock_api_client, mock_analyzer, mock_handler):
        # Setup mocks
        mock_analyzer_instance = mock_analyzer.return_value

        # Call command with --provider ollama
        call_command("quarterly_report_processor", ticker="AAPL", provider="ollama")

        # Verify LLMHandler.from_env was called with Ollama provider
        mock_handler.from_env.assert_called_once_with(provider=ProviderEnum.OLLAMA)
