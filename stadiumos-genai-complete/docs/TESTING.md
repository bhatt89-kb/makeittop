# Testing

## 1. How to run

```bash
cd backend
pip install -r requirements.txt
pytest                                   # run the suite
pytest --cov=app --cov-report=term-missing   # with coverage
```

No network access, no API key, and no external service is required — every test runs against the app in
its default "no `ANTHROPIC_API_KEY` configured" fallback mode (forced in `tests/conftest.py`), and the AI
layer is exercised in isolation via monkeypatching, not live calls. This keeps CI fast, free, and
deterministic.

## 2. Current results (as of this submission)

```
69 passed in ~1.1s
TOTAL coverage: 94% (699 statements, 39 missed)
```

## 3. Test suite structure

| File | Focus |
|---|---|
| `tests/test_ai_service.py` | The GenAI abstraction layer: no-key behaviour, exception containment (never raises), successful-response parsing |
| `tests/test_navigation.py` | Dijkstra pathfinding correctness, accessibility-aware routing, invalid-input handling, API-level validation |
| `tests/test_crowd.py` | Occupancy threshold classification (parametrized across all four severity bands), alert sort order, all-clear summary, API validation |
| `tests/test_transport.py` | Parking-lot occupancy math, mode/accessibility filtering, deterministic ranking (available before near-full before full), fallback summary, API validation |
| `tests/test_assistant_features.py` | Chat, translation, sustainability, accessibility, and emergency service-level behaviour, including language validation |
| `tests/test_security.py` | Prompt-injection sanitizer, security headers, admin auth (missing/wrong/correct key), input validation (control chars, oversized payload, unsupported language), rate limiter |
| `tests/test_router_error_handling.py` | Every router's exception path — simulates each service layer throwing (including `transport`) and asserts a clean, information-minimal 500, **except** `/emergency`, which is asserted to degrade to safe guidance rather than ever surfacing a bare error |

## 4. What the suite deliberately proves, not just covers

Line coverage alone doesn't prove correctness, so several tests target specific *behavioural guarantees*
that matter for this domain:

- **"GenAI down ≠ app down."** `test_ai_service.py::test_generate_never_raises_on_client_error` and the
  various `*_fallback_mode` tests assert that every user-facing feature still returns a complete, valid
  response with zero configured API key.
- **"Emergency guidance never goes dark."**
  `test_router_error_handling.py::test_emergency_service_exception_still_returns_safe_guidance` deliberately
  breaks the emergency service layer and asserts the endpoint still returns HTTP 200 with
  `escalate_to_human: true` and a hotline — the one place in the system where a raw 500 would be
  unacceptable.
- **"Crowd alerts fire on real thresholds, not vibes."**
  `test_crowd.py::test_severity_thresholds` is parametrized directly against the documented 70/85/95%
  boundaries so a future refactor can't silently drift the safety thresholds without failing a test.
- **"Malicious input can't reach a raw prompt."** `test_security.py::TestPromptInjectionSanitizer` and
  `TestInputValidationSecurity` assert both the sanitizer function and the full HTTP validation layer
  reject or neutralize adversarial input.

## 5. Frontend testing

The frontend is intentionally build-tool-free (a single static HTML/CSS/JS file), so it does not currently
have an automated test harness (e.g. Playwright/Cypress) — this is the top frontend item in
`docs/UNFINISHED.md`. In its place:

- `node --check` is run against the extracted inline script during development to catch syntax errors.
- The manual accessibility checklist in `docs/ACCESSIBILITY.md` doubles as a functional smoke test, since
  it requires exercising every module via keyboard alone.
- The frontend's local fallback logic (`localShortestPath`, `classifyOccupancy`, `localChatFallback`,
  `localTransportOptions`) is a deliberate line-for-line mirror of the backend's tested Python logic, so
  the backend test suite is effectively a correctness spec for the frontend's offline demo mode too.
