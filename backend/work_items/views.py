"""API Views and Exception Handlers for Work Items."""
import uuid
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.views import exception_handler

from work_items.domain import (
    InvalidStateTransitionError,
    DomainValidationError,
)
from work_items.services import (
    WorkItemNotFoundError,
    get_work_item,
    list_work_items,
    receive_work_item,
    trigger_analysis,
    retry_analysis,
    update_work_item_status,
)
from work_items.serializers import (
    WorkItemCreateSerializer,
    WorkItemResponseSerializer,
    StatusUpdateSerializer,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Standardized custom exception handler returning consistent JSON responses:
    {"error": "<CODE>", "message": "<DESCRIPTION>", "details": ...}
    """
    if isinstance(exc, InvalidStateTransitionError):
        return Response(
            {"error": "INVALID_STATE_TRANSITION", "message": str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, WorkItemNotFoundError):
        return Response(
            {"error": "NOT_FOUND", "message": str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, DomainValidationError):
        return Response(
            {"error": "VALIDATION_ERROR", "message": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Let DRF handle standard exceptions, then format consistently
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            return Response(
                {
                    "error": "INVALID_REQUEST_DATA",
                    "message": "The provided request data failed validation.",
                    "details": response.data,
                },
                status=response.status_code,
            )
        if isinstance(exc, NotFound):
            return Response(
                {"error": "NOT_FOUND", "message": "The requested resource was not found."},
                status=response.status_code,
            )
        return Response(
            {
                "error": "REQUEST_FAILED",
                "message": "An error occurred while processing your request.",
                "details": response.data,
            },
            status=response.status_code,
        )

    # Unhandled unexpected exceptions
    logger.exception("Unhandled server error: %s", exc)
    return Response(
        {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class WorkItemListCreateView(APIView):
    """
    GET  /api/work-items - List work items, filterable with ?status=...
    POST /api/work-items - Idempotent intake of work items
    """

    def get(self, request):
        status_filter = request.query_params.get("status")
        items = list_work_items(status=status_filter)
        serializer = WorkItemResponseSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WorkItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        item, created = receive_work_item(
            external_id=validated_data["external_id"],
            title=validated_data["title"],
            description=validated_data["description"],
        )

        response_serializer = WorkItemResponseSerializer(item)
        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=http_status)


class WorkItemDetailView(APIView):
    """
    GET /api/work-items/:id - Retrieve a single work item
    """

    def get(self, request, item_id):
        try:
            parsed_id = uuid.UUID(str(item_id))
        except ValueError:
            return Response(
                {"error": "INVALID_ID", "message": f"'{item_id}' is not a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_work_item(parsed_id)
        serializer = WorkItemResponseSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkItemAnalyseView(APIView):
    """
    POST /api/work-items/:id/analyse - Trigger AI analysis (from RECEIVED)
    """

    def post(self, request, item_id):
        try:
            parsed_id = uuid.UUID(str(item_id))
        except ValueError:
            return Response(
                {"error": "INVALID_ID", "message": f"'{item_id}' is not a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_item = trigger_analysis(parsed_id)
        serializer = WorkItemResponseSerializer(updated_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkItemRetryView(APIView):
    """
    POST /api/work-items/:id/retry - Retry AI analysis (only from FAILED)
    """

    def post(self, request, item_id):
        try:
            parsed_id = uuid.UUID(str(item_id))
        except ValueError:
            return Response(
                {"error": "INVALID_ID", "message": f"'{item_id}' is not a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_item = retry_analysis(parsed_id)
        serializer = WorkItemResponseSerializer(updated_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkItemStatusUpdateView(APIView):
    """
    PATCH /api/work-items/:id/status - Update work item status (e.g. COMPLETE)
    """

    def patch(self, request, item_id):
        try:
            parsed_id = uuid.UUID(str(item_id))
        except ValueError:
            return Response(
                {"error": "INVALID_ID", "message": f"'{item_id}' is not a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_item = update_work_item_status(
            parsed_id,
            serializer.validated_data["status"],
        )
        response_serializer = WorkItemResponseSerializer(updated_item)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
