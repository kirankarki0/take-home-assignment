"""Domain models, value objects, and state machine transitions for Work Items."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class WorkItemStatus(str, Enum):
    RECEIVED = "RECEIVED"
    ANALYSING = "ANALYSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Category(str, Enum):
    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"
    IDENTITY_VERIFICATION = "IDENTITY_VERIFICATION"
    INCOME_ASSESSMENT = "INCOME_ASSESSMENT"
    COMPLIANCE_REVIEW = "COMPLIANCE_REVIEW"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DomainException(Exception):
    """Base domain exception."""


class DomainValidationError(DomainException):
    """Raised when domain entities or value objects fail invariant checks."""


class InvalidStateTransitionError(DomainException):
    """Raised when an illegal workflow state transition is attempted."""


@dataclass(frozen=True)
class AIAnalysisResult:
    category: Category
    priority: Priority
    summary: str
    recommended_action: str

    def __post_init__(self):
        if not isinstance(self.category, Category):
            try:
                object.__setattr__(self, 'category', Category(self.category))
            except ValueError:
                raise DomainValidationError(f"Invalid category: {self.category}")

        if not isinstance(self.priority, Priority):
            try:
                object.__setattr__(self, 'priority', Priority(self.priority))
            except ValueError:
                raise DomainValidationError(f"Invalid priority: {self.priority}")

        if not self.summary or not self.summary.strip():
            raise DomainValidationError("Summary cannot be empty")

        if not self.recommended_action or not self.recommended_action.strip():
            raise DomainValidationError("Recommended action cannot be empty")


@dataclass
class WorkItem:
    id: uuid.UUID
    external_id: str
    title: str
    description: str
    status: WorkItemStatus = WorkItemStatus.RECEIVED
    analysis_result: Optional[AIAnalysisResult] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.external_id or not self.external_id.strip():
            raise DomainValidationError("external_id cannot be empty")
        self.external_id = self.external_id.strip()

        if not self.title or not self.title.strip():
            raise DomainValidationError("title cannot be empty")
        self.title = self.title.strip()

        if not self.description or not self.description.strip():
            raise DomainValidationError("description cannot be empty")
        self.description = self.description.strip()

        if not isinstance(self.status, WorkItemStatus):
            try:
                self.status = WorkItemStatus(self.status)
            except ValueError:
                raise DomainValidationError(f"Invalid status: {self.status}")

        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    def start_analysis(self) -> None:
        """Move from RECEIVED into ANALYSING."""
        if self.status != WorkItemStatus.RECEIVED:
            raise InvalidStateTransitionError(
                f"Cannot start analysis from status '{self.status}'. Must be RECEIVED."
            )
        self.status = WorkItemStatus.ANALYSING
        self.error_message = None
        self.updated_at = datetime.now(timezone.utc)

    def complete_analysis(self, result: AIAnalysisResult) -> None:
        """Move from ANALYSING to READY_FOR_REVIEW upon successful AI output."""
        if self.status != WorkItemStatus.ANALYSING:
            raise InvalidStateTransitionError(
                f"Cannot complete analysis from status '{self.status}'. Must be in ANALYSING."
            )
        self.analysis_result = result
        self.status = WorkItemStatus.READY_FOR_REVIEW
        self.error_message = None
        self.updated_at = datetime.now(timezone.utc)

    def fail_analysis(self, reason: str) -> None:
        """Move from ANALYSING to FAILED without corrupting original work item data."""
        if self.status != WorkItemStatus.ANALYSING:
            raise InvalidStateTransitionError(
                f"Cannot fail analysis from status '{self.status}'. Must be in ANALYSING."
            )
        self.status = WorkItemStatus.FAILED
        self.error_message = reason or "Unknown AI analysis failure"
        self.updated_at = datetime.now(timezone.utc)

    def retry_analysis(self) -> None:
        """Retry analysis: Only work items that failed during AI processing are eligible."""
        if self.status != WorkItemStatus.FAILED:
            raise InvalidStateTransitionError(
                f"Only work items in FAILED status are eligible for retry. Current status is '{self.status}'."
            )
        self.status = WorkItemStatus.ANALYSING
        self.error_message = None
        self.updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Move from READY_FOR_REVIEW to COMPLETED."""
        if self.status != WorkItemStatus.READY_FOR_REVIEW:
            raise InvalidStateTransitionError(
                f"Cannot complete work item from status '{self.status}'. Must be READY_FOR_REVIEW."
            )
        self.status = WorkItemStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)
