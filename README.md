# AI-Assisted Work Intake System

A small, maintainable, production-ready AI-Assisted Work Intake System built for an operations team to receive, analyse with LLMs, review, and complete incoming work items.

---

## Architecture Overview

The system uses a pragmatic **layered architecture** emphasizing strict separation of concerns, domain-driven invariant enforcement, and defensive boundaries:

```
                            React + TypeScript + TanStack Query
                                             │
                                         HTTP / JSON
                                             │
                                             ▼
                                   Django REST Framework
                           (Input validation, CORS, error handling)
                                             │
                                             ▼
                                    Application Services
                           (Orchestration, intake deduplication, retry)
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
               Work Item Domain                               AI Interface
        (State Machine Invariants & FSM)                   (Protocol / Factory)
                       │                                    ┌──────┴──────┐
                       ▼                                    ▼             ▼
              Django ORM Repository                        Mock         Gemini
                       │
                       ▼
                    SQLite
```

### Key Architectural Principles
1. **Domain-Owned State Machine**: Controllers and serializers never directly mutate status. All workflow transitions (`RECEIVED` → `ANALYSING` → `READY_FOR_REVIEW` → `COMPLETED` / `FAILED`) are guarded by domain invariants on the `WorkItem` aggregate.
2. **Pluggable AI Interface**: `AIAnalyzer` protocol decouples the application from specific LLM vendors. `MockAIAnalyzer` provides fast, deterministic local execution and error simulation, while `GeminiAIAnalyzer` provides real cloud LLM integration.
3. **Strict Validation Boundaries**:
   - HTTP inputs validated via DRF serializers (`WorkItemCreateSerializer`, `StatusUpdateSerializer`).
   - LLM responses strictly validated via **Pydantic schemas** (`AIAnalysisSchema`) before touching domain entities or the database.
4. **Resilient Failure Handling**: AI timeouts, malformed JSON, or unexpected values transition items to `FAILED`, record the error reason, and never corrupt original work item data (`external_id`, `title`, `description`).

---

## State Machine & Transition Matrix

```
       ┌───────────┐
       │ RECEIVED  │
       └─────┬─────┘
             │ analyse
             ▼
       ┌───────────┐
       │ ANALYSING │
       └─┬───────┬─┘
  success│       │ failure
         │       ▼
         │ ┌───────────┐
         │ │  FAILED   │
         │ └─────┬─────┘
         │       │ retry
         │       └─────┐
         ▼             ▼
  ┌───────────────┐ ┌───────────┐
  │READY_FOR_REVIEW│ │ ANALYSING │
  └──────┬────────┘ └───────────┘
         │ complete
         ▼
  ┌───────────┐
  │ COMPLETED │
  └───────────┘
```

| Source State | Target State | Operation | Allowed? | Rule / Invariant |
| :--- | :--- | :--- | :---: | :--- |
| `RECEIVED` | `ANALYSING` | Trigger analysis | **Yes** | Standard analysis initiation |
| `ANALYSING` | `READY_FOR_REVIEW` | Analysis success | **Yes** | Structured AI result saved |
| `ANALYSING` | `FAILED` | Analysis failure | **Yes** | Error message recorded, item data preserved |
| `FAILED` | `ANALYSING` | Retry | **Yes** | Only items that failed during AI are retryable |
| `READY_FOR_REVIEW` | `COMPLETED` | Complete | **Yes** | Marks operational review complete |
| `COMPLETED` | *Any* | Any | **No** | Completed items cannot re-enter analysis |
| `RECEIVED` | `COMPLETED` | Complete | **No** | Must undergo review before completion |
| `READY_FOR_REVIEW` | `ANALYSING` | Retry | **No** | Retry rejected if status is not `FAILED` |

---

## Setup & Running

### Prerequisites
- Python 3.9+
- Node.js 18+ & npm

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (optional, defaults to mock provider)
cp .env.example .env

# Run database migrations
python manage.py migrate

# Run development server
python manage.py runserver 127.0.0.1:8000
```
Backend API will be available at: `http://127.0.0.1:8000/api/`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run Vite development server
npm run dev
```
Frontend interface will be available at: `http://127.0.0.1:5173/`

---

## Running Automated Tests

The test suite covers domain invariants, AI providers & schema validation, API contracts & concurrency races, frontend components, and full end-to-end browser flows:

### Backend Tests (Pytest)
```bash
cd backend
source venv/bin/activate
pytest -v
```
**Test Coverage Includes (27 tests):**
- **Domain Tests (`tests/test_domain.py`)**: Entity initialization, valid state lifecycle, invalid transition rejections, retry guard checks, value object invariants.
- **AI Tests (`tests/test_ai.py`)**: Deterministic extraction, Pydantic schema validation, simulated failure modes (`timeout`, `malformed`, `unexpected`, `error`).
- **API Tests (`tests/test_api.py`)**:
  - **Sequential Idempotent Intake**: Verifies duplicate `externalId` returns existing item with 200 OK without duplicating or overwriting data.
  - **Concurrent Duplicate Race Test (`TransactionTestCase` + multi-threading with `threading.Barrier`)**: Fires simultaneous requests on separate threads to prove database uniqueness constraint + atomic transaction handling catches concurrency races safely.
  - **Invalid Transitions**: Proves illegal transitions return 409 Conflict with standardized error codes.
  - **Failure Resilience**: Proves AI failure cleanly sets status to `FAILED` and preserves work item data without corruption.

### Frontend Component Tests (Vitest)
```bash
cd frontend
npm run test
```
**Coverage Includes (9 tests):**
- Status badge formatting and icon rendering across all 5 states.
- Action button visibility and conditional enabling based on item state.
- Failure banner presentation and retry button rendering.
- Structured AI insight presentation.

### End-to-End Tests (Playwright)
```bash
cd frontend
npm run test:e2e
```
**Coverage Includes (3 full browser flows):**
1. **Happy Path**: Ingest new item → View in list → Trigger AI analysis → View structured insights (category, priority, summary, recommended action) → Complete item.
2. **Failure & Retry Path**: Ingest failing item (`[SIMULATE_TIMEOUT]`) → Trigger analysis → Verify `FAILED` state and error banner → Click retry.
3. **Idempotency Flow**: Submitting duplicate `externalId` in UI confirms existing item is returned without duplicate list entries.

---

## Assumptions

1. **Idempotency Key (`externalId`)**:
   - `externalId` is provided by the external upstream business system (e.g. CRM, ticketing system).
   - A subsequent request with an already-known `externalId` returns the existing work item (HTTP 200) rather than failing with an unhandled exception or creating a duplicate row.
   - Subsequent duplicate requests do not overwrite the original work item's title or description.
2. **Synchronous Analysis for Assessment Scope**:
   - AI analysis is executed synchronously within the request-response lifecycle for simplicity of evaluation and zero external infrastructure dependencies (e.g. no Redis/Celery required).
3. **Strict Retry Eligibility**:
   - In accordance with requirement 4, only work items in `FAILED` status are eligible for retry. Initiating retry on items in `RECEIVED`, `READY_FOR_REVIEW`, or `COMPLETED` is rejected by the domain model.
4. **Terminal Completion**:
   - Once a work item reaches `COMPLETED`, its status is final and cannot re-enter analysis or be modified.

---

## Technical Decisions & Trade-Offs

### 1. Concurrency Handling: Database Constraint + Atomic Transaction
- **Decision**: Rather than relying solely on application-level checks (`if not exists: create`), which suffers from race conditions under simultaneous requests, we enforced a database-level `UNIQUE(external_id)` constraint wrapped in `transaction.atomic()` with `IntegrityError` handling.
- **Trade-Off**: Catching database integrity errors requires slightly more defensive exception handling in the service layer, but guarantees 100% data integrity even across multiple parallel application worker processes.
- **Verification**: Verified using a multi-threaded `TransactionTestCase` utilizing `threading.Barrier` to ensure two requests hit the database at the exact same instant.

### 2. Domain-Enforced State Machine vs Controller-Level Status Checks
- **Decision**: All state transition logic is encapsulated strictly inside methods on the `WorkItem` domain model (`start_analysis()`, `complete_analysis()`, `fail_analysis()`, `retry_analysis()`, `complete()`).
- **Trade-Off**: Slightly more code than updating `model.status = "COMPLETED"`, but guarantees business rules cannot be bypassed by any endpoint, serializer, or future worker.

### 3. Pydantic Schema Validation for AI Outputs
- **Decision**: Raw LLM output is parsed through a strict Pydantic model (`AIAnalysisSchema`) before being converted into domain value objects.
- **Trade-Off**: Rejects outputs if the LLM invents a non-standard enum category or omits required fields; however, it ensures invalid AI responses cleanly trigger the `fail_analysis()` path rather than corrupting database records.

---

## OWASP Top 10 Security Defenses

- **A01: Broken Access Control & IDOR**: UUIDv4 primary keys prevent sequential ID enumeration; CORS is restricted to frontend origins.
- **A02: Cryptographic Failures**: Secrets and API keys are managed exclusively via environment variables (`.env`). `.env` is gitignored; `.env.example` is provided with dummy defaults.
- **A03: Injection (SQL & Prompt Injection)**:
  - Zero raw SQL queries; Django ORM parameterized queries used exclusively.
  - **Prompt Injection Defense**: Untrusted user inputs (`title`, `description`) are wrapped in explicit `<work_item_data>` XML delimiters with explicit system instructions commanding the model to treat content strictly as untrusted data to classify and never as instructions.
- **A04: Insecure Design**: Finite state machine transitions and database idempotency guards prevent unauthorized workflow bypass.
- **A05: Security Misconfiguration**: Security headers enabled (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).
- **A08: Software and Data Integrity Failures**: Strict input schema validation (DRF serializers) and output schema validation (Pydantic).
- **A09: Security Logging and Monitoring**: Errors logged without leaking sensitive API keys or stack traces to end users.
- **A10: SSRF**: Outbound requests are strictly restricted to official provider endpoints (Google Gemini API). No arbitrary user-supplied URLs are fetched.

---

## Production Considerations

If moving this application to a high-volume production environment, the following enhancements would be recommended:

1. **Asynchronous Background Processing**:
   - Move LLM analysis to an asynchronous worker queue (e.g. Celery with Redis or AWS SQS).
   - Ingested items immediately return `202 Accepted` with a task ID or status `ANALYSING`, and WebSocket / Server-Sent Events (SSE) stream status updates to the operations UI.
2. **Authentication & Role-Based Access Control (RBAC)**:
   - Integrate OAuth2 / OIDC (e.g. Okta, Auth0) or JWT session auth.
   - Separate permissions: `operations:view`, `operations:analyse`, `operations:approve_complete`.
3. **Database Scalability**:
   - Migrate from SQLite to PostgreSQL with connection pooling (PgBouncer).
   - Add read replicas for high-frequency dashboard queries.
4. **Observability & Distributed Tracing**:
   - Instrument with OpenTelemetry, Prometheus metrics (measuring intake rate, LLM latency, failure rates), and Sentry for error tracking.
5. **LLM Cost Control & Reliability**:
   - Implement response caching for identical work item descriptions.
   - Add circuit breakers and exponential backoff retries for transient upstream provider 429/500 errors.

---

## AI Usage

- **Tools Used**: Antigravity / Gemini for scaffolding initial DDD layer blueprints, test case design, and component templates.
- **Application**: Used to accelerate test suite creation (domain, integration, concurrency race test, and Playwright E2E scenarios) and ensure OWASP Top 10 coverage.
- **Verification**: Every generated unit test, API endpoint, migration, and E2E browser test was verified by executing test commands directly in the local runtime environment.
- **Modifications & Decisions**:
  - Replaced overly abstract multi-package DDD structures with a pragmatic, testable layered architecture as requested in the revised plan.
  - Tailored concurrency race test using `TransactionTestCase` and `threading.Barrier` to ensure real multi-threaded database testing rather than relying on standard single-transaction `TestCase`.

---

## Submission Details

- **Backend Language**: Python 3.9+ / Django 4.2 / Django REST Framework
- **Frontend Framework**: React 19 / TypeScript / Vite / TanStack Query
- **LLM Provider / Mock Used**: Pluggable `MockAIAnalyzer` (default with failure simulation tokens) and `GeminiAIAnalyzer` (Google Gemini API)
