"""Integration and API tests for Work Items (TDD).

Includes:
1. Sequential duplicate/idempotent intake test.
2. Concurrent duplicate intake test using TransactionTestCase and multi-threading with Barrier.
3. Invalid state transition rejection tests.
4. AI failure resilience and non-corruption tests.
5. Workflow lifecycle (receive -> analyse -> ready -> complete).
6. Retry eligibility tests.
"""
import threading
from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection
from rest_framework.test import APIClient
from rest_framework import status
from work_items.models import WorkItemModel
from work_items.domain import WorkItemStatus


@override_settings(AI_PROVIDER="mock")
class WorkItemAPITestCase(TestCase):
    """Standard API tests for work items."""

    def setUp(self):
        self.client = APIClient()

    def test_create_work_item_success(self):
        payload = {
            "externalId": "CRM-1001",
            "title": "Missing income document",
            "description": "Applicant has not provided their latest payslip.",
        }
        response = self.client.post("/api/work-items/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["externalId"] == "CRM-1001"
        assert data["status"] == "RECEIVED"
        assert WorkItemModel.objects.filter(external_id="CRM-1001").count() == 1

    def test_sequential_duplicate_intake_is_idempotent(self):
        """
        Test 1 (Sequential): Sending the same externalId twice:
        - Exactly 1 row created.
        - First returns 201, second returns 200.
        - Original payload is preserved even if second request attempts different title/description.
        """
        payload = {
            "externalId": "CRM-1002",
            "title": "Initial Title",
            "description": "Initial Description",
        }
        resp1 = self.client.post("/api/work-items/", payload, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        # Second request with same externalId
        payload_duplicate = {
            "externalId": "CRM-1002",
            "title": "Modified Title Should Not Overwrite",
            "description": "Modified Description",
        }
        resp2 = self.client.post("/api/work-items/", payload_duplicate, format="json")
        assert resp2.status_code == status.HTTP_200_OK

        # Verify only 1 database row exists
        assert WorkItemModel.objects.filter(external_id="CRM-1002").count() == 1

        # Verify original payload was NOT overwritten
        item = WorkItemModel.objects.get(external_id="CRM-1002")
        assert item.title == "Initial Title"
        assert item.description == "Initial Description"

    def test_status_filtering(self):
        """Verify GET /api/work-items/?status=... returns filtered results."""
        self.client.post("/api/work-items/", {"externalId": "CRM-A", "title": "A", "description": "A"}, format="json")
        self.client.post("/api/work-items/", {"externalId": "CRM-B", "title": "B", "description": "B"}, format="json")

        resp = self.client.get("/api/work-items/?status=RECEIVED")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) >= 2
        assert all(item["status"] == "RECEIVED" for item in data)

        # Filter by non-existent status in DB
        resp_failed = self.client.get("/api/work-items/?status=FAILED")
        assert resp_failed.status_code == status.HTTP_200_OK
        assert len(resp_failed.json()) == 0

    def test_invalid_workflow_transition_rejected(self):
        """
        Test 2: Invalid state transitions must be rejected with 409 Conflict.
        Example: RECEIVED -> COMPLETED directly, or COMPLETED -> ANALYSING.
        """
        # Create item
        resp = self.client.post("/api/work-items/", {
            "externalId": "CRM-2001",
            "title": "Transition Test",
            "description": "Testing invalid transitions",
        }, format="json")
        item_id = resp.json()["id"]

        # 1. Try to COMPLETE directly from RECEIVED -> Must fail (409)
        patch_resp = self.client.patch(f"/api/work-items/{item_id}/status/", {"status": "COMPLETED"}, format="json")
        assert patch_resp.status_code == status.HTTP_409_CONFLICT
        assert patch_resp.json()["error"] == "INVALID_STATE_TRANSITION"

        # 2. Complete the item legitimately (RECEIVED -> ANALYSING -> READY_FOR_REVIEW -> COMPLETED)
        analyse_resp = self.client.post(f"/api/work-items/{item_id}/analyse/")
        assert analyse_resp.status_code == status.HTTP_200_OK
        assert analyse_resp.json()["status"] == "READY_FOR_REVIEW"

        complete_resp = self.client.patch(f"/api/work-items/{item_id}/status/", {"status": "COMPLETED"}, format="json")
        assert complete_resp.status_code == status.HTTP_200_OK
        assert complete_resp.json()["status"] == "COMPLETED"

        # 3. Try to move COMPLETED item back to ANALYSING -> Must fail (409)
        reanalyse_resp = self.client.post(f"/api/work-items/{item_id}/analyse/")
        assert reanalyse_resp.status_code == status.HTTP_409_CONFLICT
        assert reanalyse_resp.json()["error"] == "INVALID_STATE_TRANSITION"

    def test_failed_ai_response_does_not_corrupt_data(self):
        """
        Test 3: Simulating AI timeout or malformed output:
        - Status becomes FAILED
        - external_id, title, description are preserved unchanged
        - error_message is recorded
        """
        resp = self.client.post("/api/work-items/", {
            "externalId": "CRM-3001",
            "title": "Failing item [SIMULATE_TIMEOUT]",
            "description": "This request simulates an AI provider timeout.",
        }, format="json")
        item_id = resp.json()["id"]

        # Trigger analysis
        analyse_resp = self.client.post(f"/api/work-items/{item_id}/analyse/")
        assert analyse_resp.status_code == status.HTTP_200_OK
        data = analyse_resp.json()

        assert data["status"] == "FAILED"
        assert "timed out" in data["errorMessage"].lower()
        # Data integrity preserved
        assert data["externalId"] == "CRM-3001"
        assert data["title"] == "Failing item [SIMULATE_TIMEOUT]"
        assert data["description"] == "This request simulates an AI provider timeout."

    def test_retry_allowed_only_for_failed_items(self):
        """Verify retry endpoint is only valid from FAILED state."""
        # 1. Item in RECEIVED state -> retry must fail (409)
        resp = self.client.post("/api/work-items/", {
            "externalId": "CRM-4001",
            "title": "Retry guard test",
            "description": "Description",
        }, format="json")
        item_id = resp.json()["id"]

        retry_resp = self.client.post(f"/api/work-items/{item_id}/retry/")
        assert retry_resp.status_code == status.HTTP_409_CONFLICT

        # 2. Force item to fail
        fail_item = WorkItemModel.objects.get(id=item_id)
        fail_item.status = WorkItemStatus.FAILED.value
        fail_item.error_message = "Previous failure"
        fail_item.save()

        # 3. Now retry should succeed and transition to READY_FOR_REVIEW
        retry_success_resp = self.client.post(f"/api/work-items/{item_id}/retry/")
        assert retry_success_resp.status_code == status.HTTP_200_OK
        data = retry_success_resp.json()
        assert data["status"] == "READY_FOR_REVIEW"
        assert data["analysisResult"] is not None
        assert data["errorMessage"] is None

    def test_missing_work_item_returns_404(self):
        random_uuid = "00000000-0000-0000-0000-000000000000"
        resp = self.client.get(f"/api/work-items/{random_uuid}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json()["error"] == "NOT_FOUND"

    def test_invalid_input_payload_returns_400(self):
        resp = self.client.post("/api/work-items/", {"externalId": ""}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"] == "INVALID_REQUEST_DATA"


@override_settings(AI_PROVIDER="mock")
class ConcurrentWorkItemIntakeTestCase(TransactionTestCase):
    """
    Test 1 (Concurrent duplicate intake / race test).
    Uses TransactionTestCase so each thread operates with real database transactions.
    Fires 2 simultaneous requests using a threading.Barrier to guarantee simultaneous execution.
    """

    def test_concurrent_duplicate_intake_creates_only_one_record(self):
        barrier = threading.Barrier(2)
        results = []

        def submit_work_item():
            client = APIClient()
            try:
                barrier.wait(timeout=5)  # Synchronize both threads to fire at the exact same instant
                response = client.post(
                    "/api/work-items/",
                    {
                        "externalId": "CRM-CONCURRENT-RACE",
                        "title": "Concurrent Race Work Item",
                        "description": "Two requests arriving simultaneously with the same externalId",
                    },
                    format="json",
                )
                results.append(response)
            except Exception as e:
                results.append(e)
            finally:
                connection.close()

        t1 = threading.Thread(target=submit_work_item)
        t2 = threading.Thread(target=submit_work_item)

        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        # Both requests should succeed (no 500 internal errors)
        assert len(results) == 2
        status_codes = [r.status_code for r in results if hasattr(r, 'status_code')]
        assert all(code in (status.HTTP_200_OK, status.HTTP_201_CREATED) for code in status_codes)

        # Exactly ONE row must exist in the database
        assert WorkItemModel.objects.filter(external_id="CRM-CONCURRENT-RACE").count() == 1

        # Both responses returned the same work item ID
        ids = [r.json()["id"] for r in results if hasattr(r, 'json')]
        assert len(ids) == 2
        assert ids[0] == ids[1]
