"""Gemini AI Provider implementation with prompt injection protection and schema validation."""
import json
import re
import requests
from django.conf import settings
from work_items.ai.base import (
    AIAnalyzer,
    AIAnalysisSchema,
    AIAnalysisResult,
    AIProviderError,
    AITimeoutError,
    AIMalformedOutputError,
    AIValidationError,
)
from work_items.ai.prompt import build_user_content, TRIAGE_SYSTEM_INSTRUCTION


class GeminiAIAnalyzer(AIAnalyzer):
    """Real LLM provider using Google Gemini API."""

    _DEFAULT_API_URL_TEMPLATE = (
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    )

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        api_url_template: str = None,
        timeout: float = 10.0,
    ):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "") if api_key is None else api_key
        self.model = getattr(settings, "GEMINI_MODEL", "") if model is None else model
        self.api_url_template = (
            getattr(settings, "GEMINI_API_URL_TEMPLATE", self._DEFAULT_API_URL_TEMPLATE)
            if api_url_template is None
            else api_url_template
        )
        self.timeout = timeout

    def analyse(self, title: str, description: str) -> AIAnalysisResult:
        if not self.api_key:
            raise AIProviderError("Gemini API key is not configured.")

        user_content = build_user_content(title, description)   

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": user_content}]}
            ],
            "systemInstruction": {
                "parts": [{"text": TRIAGE_SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            },
        }

        url = self.api_url_template.format(model=self.model, api_key=self.api_key)

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise AITimeoutError(f"Gemini API request timed out after {self.timeout}s: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise AIProviderError(f"Gemini API connection error: {exc}") from exc

        if response.status_code != 200:
            raise AIProviderError(f"Gemini API returned status code {response.status_code}: {response.text}")

        try:
            response_json = response.json()
            candidates = response_json.get("candidates", [])
            if not candidates:
                raise AIMalformedOutputError("No candidates returned from Gemini API.")
            raw_text = candidates[0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AIMalformedOutputError(f"Failed to extract text from Gemini response: {exc}") from exc

        # Clean any potential markdown code fence wrapping (e.g. ```json ... ```)
        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)

        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            raise AIMalformedOutputError(f"Malformed JSON from Gemini: {exc}") from exc

        try:
            schema = AIAnalysisSchema.model_validate(data)
            return schema.to_domain()
        except Exception as exc:
            raise AIValidationError(f"Gemini output failed schema validation: {exc}") from exc
