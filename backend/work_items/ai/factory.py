from django.conf import settings
from work_items.ai.base import AIAnalyzer, AIProviderError
from work_items.ai.mock import MockAIAnalyzer
from work_items.ai.gemini import GeminiAIAnalyzer


_PROVIDERS = {
    "mock": MockAIAnalyzer,
    "gemini": GeminiAIAnalyzer,
}

def get_analyzer() -> AIAnalyzer:
    name = getattr(settings, "AI_PROVIDER", "mock").lower()
    try:
        return _PROVIDERS[name]()
    except KeyError:
        raise AIProviderError(f"Unknown AI_PROVIDER '{name}'. Valid: {list(_PROVIDERS)}")