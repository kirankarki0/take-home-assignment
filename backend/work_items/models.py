"""Django ORM models for Work Items."""
import uuid
from django.db import models
from work_items.domain import (
    WorkItem,
    WorkItemStatus,
    Category,
    Priority,
    AIAnalysisResult,
)


class WorkItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=128, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=[(s.value, s.value) for s in WorkItemStatus],
        default=WorkItemStatus.RECEIVED.value,
        db_index=True,
    )
    analysis_result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "work_items"
        ordering = ["-created_at"]
        verbose_name = "Work Item"
        verbose_name_plural = "Work Items"

    def to_domain(self) -> WorkItem:
        """Convert ORM model to pure Domain entity."""
        parsed_result = None
        if self.analysis_result and isinstance(self.analysis_result, dict):
            try:
                parsed_result = AIAnalysisResult(
                    category=Category(self.analysis_result.get("category")),
                    priority=Priority(self.analysis_result.get("priority")),
                    summary=self.analysis_result.get("summary", ""),
                    recommended_action=self.analysis_result.get("recommended_action")
                    or self.analysis_result.get("recommendedAction", ""),
                )
            except (ValueError, TypeError):
                parsed_result = None

        return WorkItem(
            id=self.id,
            external_id=self.external_id,
            title=self.title,
            description=self.description,
            status=WorkItemStatus(self.status),
            analysis_result=parsed_result,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: WorkItem) -> "WorkItemModel":
        """Convert pure Domain entity to ORM model instance (unsaved)."""
        result_json = None
        if entity.analysis_result:
            result_json = {
                "category": entity.analysis_result.category.value,
                "priority": entity.analysis_result.priority.value,
                "summary": entity.analysis_result.summary,
                "recommended_action": entity.analysis_result.recommended_action,
            }

        return cls(
            id=entity.id,
            external_id=entity.external_id,
            title=entity.title,
            description=entity.description,
            status=entity.status.value,
            analysis_result=result_json,
            error_message=entity.error_message,
        )
