"""Unit tests for AI analyzers, schemas, and error handling (TDD)."""
import pytest
from pydantic import ValidationError
from work_items.ai.base import (
    AIAnalysisSchema,
    AITimeoutError,
    AIMalformedOutputError,
    AIValidationError,
    AIProviderError,
)
from work_items.ai.mock import MockAIAnalyzer
from work_items.ai.gemini import GeminiAIAnalyzer
from work_items.domain import Category, Priority


def test_mock_analyzer_determines_document_request_for_income():
    analyzer = MockAIAnalyzer()
    result = analyzer.analyse(
        title="Missing income document",
        description="The applicant submitted application without latest payslip.",
    )
    assert result.category == Category.DOCUMENT_REQUEST
    assert result.priority == Priority.HIGH
    assert "payslip" in result.summary.lower()
    assert "payslip" in result.recommended_action.lower()


def test_mock_analyzer_determines_identity_for_passport():
    analyzer = MockAIAnalyzer()
    result = analyzer.analyse(
        title="Unverified passport",
        description="The photo on the passport is blurry and requires re-upload.",
    )
    assert result.category == Category.IDENTITY_VERIFICATION
    assert result.priority == Priority.URGENT


def test_mock_analyzer_handles_simulated_timeout():
    analyzer = MockAIAnalyzer(simulation_mode="timeout")
    with pytest.raises(AITimeoutError) as exc_info:
        analyzer.analyse("Title", "Description")
    assert "timed out" in str(exc_info.value).lower()


def test_mock_analyzer_handles_simulated_malformed_json():
    analyzer = MockAIAnalyzer(simulation_mode="malformed")
    with pytest.raises(AIMalformedOutputError) as exc_info:
        analyzer.analyse("Title", "Description")
    assert "malformed" in str(exc_info.value).lower()


def test_mock_analyzer_handles_simulated_unexpected_schema():
    analyzer = MockAIAnalyzer(simulation_mode="unexpected")
    with pytest.raises(AIValidationError) as exc_info:
        analyzer.analyse("Title", "Description")
    assert "unexpected" in str(exc_info.value).lower()


def test_mock_analyzer_handles_simulated_complete_failure():
    analyzer = MockAIAnalyzer(simulation_mode="error")
    with pytest.raises(AIProviderError) as exc_info:
        analyzer.analyse("Title", "Description")
    assert "failed" in str(exc_info.value).lower()


def test_token_in_text_triggers_simulation():
    analyzer = MockAIAnalyzer()
    with pytest.raises(AITimeoutError):
        analyzer.analyse("Special case [SIMULATE_TIMEOUT]", "Body")


def test_pydantic_schema_validation():
    # Valid data with recommendedAction camelCase
    data = {
        "category": "DOCUMENT_REQUEST",
        "priority": "HIGH",
        "summary": "Valid summary",
        "recommendedAction": "Valid action",
    }
    schema = AIAnalysisSchema.model_validate(data)
    domain_obj = schema.to_domain()
    assert domain_obj.category == Category.DOCUMENT_REQUEST
    assert domain_obj.priority == Priority.HIGH

    # Invalid category
    with pytest.raises(ValidationError):
        AIAnalysisSchema.model_validate({**data, "category": "INVALID_CAT"})

    # Empty summary
    with pytest.raises(ValidationError):
        AIAnalysisSchema.model_validate({**data, "summary": "   "})


@override_settings(GEMINI_MODEL="gemini-2.0-flash", GEMINI_API_URL_TEMPLATE="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}")
def test_gemini_analyzer_config_defaults():
    analyzer = GeminiAIAnalyzer(api_key="test-key")
    assert analyzer.model == "gemini-2.0-flash"
    assert "{model}" in analyzer.api_url_template
    formatted_url = analyzer.api_url_template.format(model=analyzer.model, api_key=analyzer.api_key)
    assert "gemini-2.0-flash" in formatted_url
    assert analyzer.api_key == "test-key"


def test_gemini_analyzer_custom_model_and_template():
    custom_template = "https://custom-gateway.local/v1beta/models/{model}:generateContent?key={api_key}"
    analyzer = GeminiAIAnalyzer(
        api_key="custom-key",
        model="gemini-2.5-flash",
        api_url_template=custom_template,
    )
    assert analyzer.model == "gemini-2.5-flash"
    assert analyzer.api_url_template == custom_template
    formatted_url = analyzer.api_url_template.format(model=analyzer.model, api_key=analyzer.api_key)
    assert "gemini-2.5-flash" in formatted_url
    assert "key=custom-key" in formatted_url


def test_gemini_analyzer_raises_when_no_api_key():
    analyzer = GeminiAIAnalyzer(api_key="")
    with pytest.raises(AIProviderError) as exc_info:
        analyzer.analyse("Test Title", "Test Description")
    assert "API key is not configured" in str(exc_info.value)
