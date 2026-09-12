"""Application services and persistence operations for Work Items."""
from typing import List, Optional, Tuple
import uuid
from django.db import IntegrityError, transaction
from work_items.domain import (
    WorkItem,
    WorkItemStatus,
    InvalidStateTransitionError,
    DomainValidationError,
)
from work_items.models import WorkItemModel
from work_items.ai.base import AIProviderError


class WorkItemNotFoundError(Exception):
    """Raised when a work item cannot be found."""


def get_work_item(item_id: uuid.UUID) -> WorkItem:
    try:
        model = WorkItemModel.objects.get(id=item_id)
        return model.to_domain()
    except WorkItemModel.DoesNotExist:
        raise WorkItemNotFoundError(f"Work item with ID '{item_id}' not found.")


def get_work_item_by_external_id(external_id: str) -> Optional[WorkItem]:
    try:
        model = WorkItemModel.objects.get(external_id=external_id.strip())
        return model.to_domain()
    except WorkItemModel.DoesNotExist:
        return None


def list_work_items(status: Optional[str] = None) -> List[WorkItem]:
    qs = WorkItemModel.objects.all()
    if status and status.strip() and status.upper() != "ALL":
        normalized = status.strip().upper()
        # Verify valid status
        try:
            WorkItemStatus(normalized)
            qs = qs.filter(status=normalized)
        except ValueError:
            raise DomainValidationError(f"Invalid status filter '{status}'.")
    return [model.to_domain() for model in qs]


def save_work_item(entity: WorkItem) -> WorkItem:
    """Persist domain entity changes to the database."""
    # Delegate serialisation to the model layer (single source of truth)
    unsaved = WorkItemModel.from_domain(entity)
    model, _ = WorkItemModel.objects.update_or_create(
        id=entity.id,
        defaults={
            "external_id": unsaved.external_id,
            "title": unsaved.title,
            "description": unsaved.description,
            "status": unsaved.status,
            "analysis_result": unsaved.analysis_result,
            "error_message": unsaved.error_message,
        },
    )
    return model.to_domain()


def receive_work_item(external_id: str, title: str, description: str) -> Tuple[WorkItem, bool]:
    """
    Idempotently receive a work item.
    Returns (work_item, created).
    Uses application lookup + DB unique constraint + atomic handling to prevent race conditions.
    """
    cleaned_ext_id = external_id.strip()
    cleaned_title = title.strip()
    cleaned_desc = description.strip()

    if not cleaned_ext_id:
        raise DomainValidationError("external_id cannot be empty.")
    if not cleaned_title:
        raise DomainValidationError("title cannot be empty.")
    if not cleaned_desc:
        raise DomainValidationError("description cannot be empty.")

    # 1. Fast path lookup
    existing = get_work_item_by_external_id(cleaned_ext_id)
    if existing:
        return existing, False

    # 2. Race-safe creation with DB unique constraint
    try:
        with transaction.atomic():
            new_id = uuid.uuid4()
            domain_item = WorkItem(
                id=new_id,
                external_id=cleaned_ext_id,
                title=cleaned_title,
                description=cleaned_desc,
                status=WorkItemStatus.RECEIVED,
            )
            model = WorkItemModel.objects.create(
                id=domain_item.id,
                external_id=domain_item.external_id,
                title=domain_item.title,
                description=domain_item.description,
                status=domain_item.status.value,
            )
            return model.to_domain(), True
    except IntegrityError:
        # Another concurrent thread won the race and created the item
        model = WorkItemModel.objects.get(external_id=cleaned_ext_id)
        return model.to_domain(), False


def trigger_analysis(item_id: uuid.UUID, analyzer=None) -> WorkItem:
    """Execute AI analysis on a work item."""
    from work_items.ai.factory import get_analyzer

    if analyzer is None:
        analyzer = get_analyzer()

    item = get_work_item(item_id)
    item.start_analysis()
    save_work_item(item)

    try:
        result = analyzer.analyse(item.title, item.description)
        item.complete_analysis(result)
    except AIProviderError as exc:
        item.fail_analysis(f"AI analysis failed: {exc}")
    return save_work_item(item)


def retry_analysis(item_id: uuid.UUID, analyzer=None) -> WorkItem:
    """Retry AI analysis on a failed work item."""
    from work_items.ai.factory import get_analyzer

    if analyzer is None:
        analyzer = get_analyzer()

    item = get_work_item(item_id)
    # retry_analysis() verifies that item is in FAILED status
    item.retry_analysis()
    save_work_item(item)

    try:
        result = analyzer.analyse(item.title, item.description)
        item.complete_analysis(result)
    except Exception as exc:
        item.fail_analysis(f"AI analysis retry failed: {str(exc)}")

    return save_work_item(item)


def update_work_item_status(item_id: uuid.UUID, target_status: str) -> WorkItem:
    """Update status, preserving domain invariants."""
    item = get_work_item(item_id)
    normalized = target_status.strip().upper()

    if normalized == WorkItemStatus.COMPLETED.value:
        item.complete()
    else:
        raise InvalidStateTransitionError(
            f"Cannot transition directly to '{target_status}'. Allowed direct action is COMPLETED."
        )

    return save_work_item(item)
