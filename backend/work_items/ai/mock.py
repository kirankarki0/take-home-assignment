"""Deterministic Mock AI Analyzer with simulation capabilities for testing."""
from typing import Optional
from work_items.ai.base import (
    AIAnalyzer,
    AIAnalysisSchema,
    AIAnalysisResult,
    AIProviderError,
    AITimeoutError,
    AIMalformedOutputError,
    AIValidationError,
)
from work_items.domain import Category, Priority


class MockAIAnalyzer(AIAnalyzer):
    """
    Deterministic Mock AI Analyzer.
    Can be configured via explicit mode or by special tokens in the work item title/description.
    """

    def __init__(self, simulation_mode: Optional[str] = None):
        self.simulation_mode = simulation_mode

    def analyse(self, title: str, description: str) -> AIAnalysisResult:
        full_text = f"{title} {description}"

        # 1. Check simulation mode or embedded simulation trigger tokens
        mode = self.simulation_mode
        if not mode:
            if "[SIMULATE_TIMEOUT]" in full_text:
                mode = "timeout"
            elif "[SIMULATE_MALFORMED]" in full_text:
                mode = "malformed"
            elif "[SIMULATE_UNEXPECTED]" in full_text:
                mode = "unexpected"
            elif "[SIMULATE_ERROR]" in full_text:
                mode = "error"

        if mode == "timeout":
            raise AITimeoutError("AI provider request timed out after 10.0 seconds.")
        if mode == "malformed":
            raise AIMalformedOutputError("Malformed output received from AI provider: invalid JSON.")
        if mode == "unexpected":
            raise AIValidationError("Unexpected category 'INVALID_CATEGORY' returned by AI provider.")
        if mode == "error":
            raise AIProviderError("AI provider failed completely with HTTP 500 internal server error.")

        # 2. Deterministic, contextual categorization
        lower_text = full_text.lower()
        if "payslip" in lower_text or "income" in lower_text or "salary" in lower_text:
            category = Category.DOCUMENT_REQUEST
            priority = Priority.HIGH
            summary = "The applicant needs to provide their latest payslip."
            recommended_action = "Request the missing payslip from the applicant."
        elif "identity" in lower_text or "passport" in lower_text or "license" in lower_text:
            category = Category.IDENTITY_VERIFICATION
            priority = Priority.URGENT
            summary = "Identity document verification is required."
            recommended_action = "Request verified photo identification."
        elif "compliance" in lower_text or "fraud" in lower_text or "sanction" in lower_text:
            category = Category.COMPLIANCE_REVIEW
            priority = Priority.HIGH
            summary = "Potential compliance or policy trigger identified."
            recommended_action = "Escalate to compliance team for manual check."
        elif "tax" in lower_text or "statement" in lower_text or "financial" in lower_text:
            category = Category.INCOME_ASSESSMENT
            priority = Priority.MEDIUM
            summary = "Financial assessment documents require review."
            recommended_action = "Verify submitted financial statements."
        else:
            category = Category.GENERAL_INQUIRY
            priority = Priority.LOW
            summary = f"Review requested for: {title.strip()}"
            recommended_action = "Assess request details and route to operations team."

        # Schema validation pass
        schema = AIAnalysisSchema(
            category=category,
            priority=priority,
            summary=summary,
            recommendedAction=recommended_action,
        )
        return schema.to_domain()
