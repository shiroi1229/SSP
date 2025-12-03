# Developer Guide (SSP)

This guide summarizes day-to-day patterns for developing and operating the backend.

## Single-Instance Discipline
- Prefer running a single dev server instance to avoid router collisions and cache confusion.
- VS Code tasks:
  - Run with middleware off + reload (recommended):
    - Label: "Run uvicorn 8020 (middleware off)"
- PowerShell (Windows) example:
```
Push-Location "d:\gemini"
$env:PYTHONUTF8="1"
$env:DISABLE_METRICS_MIDDLEWARE="1"
C:/Python313/python.exe -m uvicorn backend.main:app --app-dir "d:\gemini" --host 127.0.0.1 --port 8020 --reload
Pop-Location
```

## Dependency Injection (DI)
- Use providers from `backend/core/di.py` in API modules.
- Example (OrchestratorService):
  - Inject with `Depends(get_orchestrator_service)`.
  - Keep API layer thin; do not call globals or singletons directly.

## Envelope Pattern
- Unified response envelope: `backend/api/schemas.py` (Envelope[T], ErrorInfo)
- Return helpers: `backend/api/common.py` (`envelope_ok`, `envelope_error`).
- Always annotate routes: `response_model=Envelope[dict]` and prefer `JSONResponse` only when setting explicit status/ctype.

## Input Validation
- Prefer Pydantic v2 patterns:
  - `ConfigDict(extra="forbid")` to reject unknown fields.
  - Field constraints (`min_length`, `max_length`, `ge`, `le`).
  - Field validators to sanitize control characters (allow `\n`, `\r`, `\t`).
- Examples:
  - `backend/api/chat.py` (`ChatRequest`)
  - `backend/api/evaluate.py` (`EvaluationRequest`)
  - `backend/api/sessions.py` (create/update models)

## RAG + DB Quick Wins
- RAG: `modules/rag_engine.py`
  - Qdrant operations already handle legacy params; avoid fetching vectors unless necessary (`with_vectors=False`).
  - Keep `limit` conservative from API (<= 100).
- DB: Prefer selective loads for list views.
  - Use `load_only()` to fetch just needed columns (see `backend/api/sessions.py`).

## Testing
- Run the test suite:
```
Push-Location "d:\gemini"
$env:PYTHONUTF8="1"
C:/Python313/python.exe -m pytest -q
Pop-Location
```
- Contract tests for Envelope lives in `backend/tests/test_api_envelope.py`.

## Error/Deprecation Notes
- Pydantic: prefer `ConfigDict`; generics moved off `GenericModel` (migration in progress).
- SQLAlchemy: `declarative_base()` notice; plan future migration.
- FastAPI: `on_event` deprecated; move to lifespan handlers later.

## PR Hygiene
- Minimal diffs; do not modify generated artifacts under `docs/roadmap/` directly (see `AGENTS.md`).
- Keep changes surgical and focused; avoid broad refactors within unrelated modules.
