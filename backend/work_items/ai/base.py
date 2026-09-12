"""Base interface and schemas for AI analysis providers."""
from typing import Protocol
from pydantic import BaseModel, ConfigDict, Field, field_validator
from work_items.domain import AIAnalysisResult, Category, Priority


class AIAnalysisSchema(BaseModel):
    """Pydantic schema for strict validation of LLM output."""
    model_config = ConfigDict(populate_by_name=True)

    category: Category
    priority: Priority
    summary: str
    recommended_action: str = Field(alias="recommendedAction")

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("summary cannot be empty")
        return v.strip()

    @field_validator("recommended_action")
    @classmethod
    def validate_recommended_action(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("recommended_action cannot be empty")
        return v.strip()

    def to_domain(self) -> AIAnalysisResult:
        return AIAnalysisResult(
            category=self.category,
            priority=self.priority,
            summary=self.summary,
            recommended_action=self.recommended_action,
        )


class AIProviderError(Exception):
    """Base exception for AI provider errors."""


class AITimeoutError(AIProviderError):
    """Raised when LLM request times out."""


class AIMalformedOutputError(AIProviderError):
    """Raised when LLM returns invalid JSON or unparseable text."""


class AIValidationError(AIProviderError):
    """Raised when LLM output violates schema or has unexpected values."""


class AIAnalyzer(Protocol):
    """Protocol for AI Analyzer implementations."""
    def analyse(self, title: str, description: str) -> AIAnalysisResult:
        """Analyse work item title and description to produce structured AIAnalysisResult."""
        ...
