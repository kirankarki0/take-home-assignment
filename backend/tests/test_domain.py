"""Unit tests for the WorkItem domain model and state machine transitions (TDD)."""
import uuid
import pytest
from work_items.domain import (
    WorkItem,
    WorkItemStatus,
    Category,
    Priority,
    AIAnalysisResult,
    InvalidStateTransitionError,
    DomainValidationError,
)

def make_sample_work_item(status: WorkItemStatus = WorkItemStatus.RECEIVED) -> WorkItem:
    return WorkItem(
        id=uuid.uuid4(),
        external_id="CRM-12345",
        title="Missing income document",
        description="Applicant submitted application without latest payslip.",
        status=status,
    )

def make_sample_analysis_result() -> AIAnalysisResult:
    return AIAnalysisResult(
        category=Category.DOCUMENT_REQUEST,
        priority=Priority.HIGH,
        summary="Applicant needs to provide their latest payslip.",
        recommended_action="Request missing payslip.",
    )

def test_initial_work_item_creation():
    item = make_sample_work_item()
    assert item.status == WorkItemStatus.RECEIVED
    assert item.external_id == "CRM-12345"
    assert item.analysis_result is None
    assert item.error_message is None

def test_work_item_validation_rejects_empty_external_id():
    with pytest.raises(DomainValidationError):
        WorkItem(
            id=uuid.uuid4(),
            external_id="   ",
            title="Title",
            description="Desc",
        )

def test_work_item_validation_rejects_empty_title():
    with pytest.raises(DomainValidationError):
        WorkItem(
            id=uuid.uuid4(),
            external_id="CRM-1",
            title="",
            description="Desc",
        )

def test_valid_happy_path_workflow_lifecycle():
    """RECEIVED -> ANALYSING -> READY_FOR_REVIEW -> COMPLETED"""
    item = make_sample_work_item()

    # 1. Start analysis
    item.start_analysis()
    assert item.status == WorkItemStatus.ANALYSING

    # 2. Complete analysis
    result = make_sample_analysis_result()
    item.complete_analysis(result)
    assert item.status == WorkItemStatus.READY_FOR_REVIEW
    assert item.analysis_result == result

    # 3. Complete work item
    item.complete()
    assert item.status == WorkItemStatus.COMPLETED

def test_failure_and_retry_workflow():
    """RECEIVED -> ANALYSING -> FAILED -> retry -> ANALYSING -> READY_FOR_REVIEW"""
    item = make_sample_work_item()
    item.start_analysis()
    assert item.status == WorkItemStatus.ANALYSING

    # Fail analysis
    item.fail_analysis("LLM timed out after 10s")
    assert item.status == WorkItemStatus.FAILED
    assert item.error_message == "LLM timed out after 10s"
    # Original data preserved
    assert item.title == "Missing income document"
    assert item.description == "Applicant submitted application without latest payslip."

    # Retry analysis
    item.retry_analysis()
    assert item.status == WorkItemStatus.ANALYSING
    assert item.error_message is None

    # Success on retry
    result = make_sample_analysis_result()
    item.complete_analysis(result)
    assert item.status == WorkItemStatus.READY_FOR_REVIEW
    assert item.analysis_result == result

def test_retry_rejected_for_non_failed_items():
    """Only work items that failed during AI processing should be eligible for retry."""
    # From RECEIVED
    item_received = make_sample_work_item(WorkItemStatus.RECEIVED)
    with pytest.raises(InvalidStateTransitionError):
        item_received.retry_analysis()

    # From ANALYSING
    item_analysing = make_sample_work_item(WorkItemStatus.ANALYSING)
    with pytest.raises(InvalidStateTransitionError):
        item_analysing.retry_analysis()

    # From READY_FOR_REVIEW
    item_ready = make_sample_work_item(WorkItemStatus.READY_FOR_REVIEW)
    with pytest.raises(InvalidStateTransitionError):
        item_ready.retry_analysis()

    # From COMPLETED
    item_completed = make_sample_work_item(WorkItemStatus.COMPLETED)
    with pytest.raises(InvalidStateTransitionError):
        item_completed.retry_analysis()

def test_completed_item_cannot_re_enter_analysis():
    """A completed work item should not simply be moved back into analysis."""
    item = make_sample_work_item(WorkItemStatus.COMPLETED)
    with pytest.raises(InvalidStateTransitionError):
        item.start_analysis()

def test_invalid_direct_transition_received_to_completed():
    item = make_sample_work_item(WorkItemStatus.RECEIVED)
    with pytest.raises(InvalidStateTransitionError):
        item.complete()

def test_invalid_complete_analysis_when_not_analysing():
    item = make_sample_work_item(WorkItemStatus.RECEIVED)
    with pytest.raises(InvalidStateTransitionError):
        item.complete_analysis(make_sample_analysis_result())

def test_analysis_result_validation():
    result = make_sample_analysis_result()
    assert result.category == Category.DOCUMENT_REQUEST
    assert result.priority == Priority.HIGH

    with pytest.raises(DomainValidationError):
        AIAnalysisResult(
            category=Category.DOCUMENT_REQUEST,
            priority=Priority.HIGH,
            summary="",
            recommended_action="Do something",
        )
