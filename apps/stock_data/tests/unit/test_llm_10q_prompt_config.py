from apps.stock_data.services.document_processor.llm_10q_prompt_config import TenQPromptConfig


def test_prompt_rendering():
    text = "Sample 10-Q text"
    config = TenQPromptConfig(document_text=text)

    assert text in config.user_prompt
    assert "REPORT:" in config.user_prompt
    assert config.system_prompt == TenQPromptConfig.SYSTEM_PROMPT
    assert config.with_json_schema is True
    assert config.temperature == 0.0

def test_prompt_rendering_custom_params():
    text = "Another text"
    config = TenQPromptConfig(document_text=text, use_json_schema=False, temperature=0.5)

    assert text in config.user_prompt
    assert config.with_json_schema is False
    assert config.temperature == 0.5
