"""Serializers for Work Items API."""
from rest_framework import serializers
from work_items.domain import Category, Priority, WorkItemStatus


class WorkItemCreateSerializer(serializers.Serializer):
    """Input serializer for work item intake."""
    externalId = serializers.CharField(max_length=128, required=False)
    external_id = serializers.CharField(max_length=128, required=False)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()

    def validate(self, attrs):
        # Support either externalId or external_id
        ext_id = attrs.get("externalId") or attrs.get("external_id")
        if not ext_id or not ext_id.strip():
            raise serializers.ValidationError({"externalId": "This field is required and cannot be blank."})
        attrs["external_id"] = ext_id.strip()

        title = attrs.get("title", "").strip()
        if not title:
            raise serializers.ValidationError({"title": "Title cannot be blank."})
        attrs["title"] = title

        description = attrs.get("description", "").strip()
        if not description:
            raise serializers.ValidationError({"description": "Description cannot be blank."})
        attrs["description"] = description

        return attrs




class WorkItemResponseSerializer(serializers.Serializer):
    """Output serializer for Work Items."""
    id = serializers.UUIDField()
    externalId = serializers.CharField(source="external_id")
    title = serializers.CharField()
    description = serializers.CharField()
    status = serializers.ChoiceField(choices=[(s.value, s.value) for s in WorkItemStatus])
    analysisResult = serializers.SerializerMethodField()
    errorMessage = serializers.CharField(source="error_message", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")

    def get_analysisResult(self, obj):
        if not obj.analysis_result:
            return None
        return {
            "category": obj.analysis_result.category.value if hasattr(obj.analysis_result.category, 'value') else obj.analysis_result.category,
            "priority": obj.analysis_result.priority.value if hasattr(obj.analysis_result.priority, 'value') else obj.analysis_result.priority,
            "summary": obj.analysis_result.summary,
            "recommendedAction": obj.analysis_result.recommended_action,
        }


class StatusUpdateSerializer(serializers.Serializer):
    """Input serializer for PATCH /api/work-items/:id/status."""
    status = serializers.ChoiceField(choices=["COMPLETED"])
