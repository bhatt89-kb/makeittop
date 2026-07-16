# Architecture

## 1. Design principle: GenAI as narrator, not decision-maker

Every endpoint in this system follows the same three-layer pattern:

1. **Deterministic core** — plain Python logic (graph pathfinding, threshold classification, keyword
   escalation rules) computes the *correct* answer using verified, structured data. This layer has no
   network dependency and is fully unit-testable.
2. **GenAI narration** — the deterministic result is handed to `services/ai_service.py`, which asks Claude
   to turn it into natural, multilingual, context-appropriate prose. The prompt explicitly constrains the
   model to the *given* facts ("using ONLY the resource list provided", "do not invent landmarks not
   present in the steps") to reduce hallucination risk.
3. **Fallback** — if the GenAI call fails for any reason (no API key, timeout, rate limit, provider outage),
   `ai_service.generate()` returns `None` and the calling service immediately falls back to a
   hand-written, deterministic sentence built from the same verified data. The response schema always
   includes a `source: "genai" | "fallback"` field so the frontend (and evaluators) can see which path
   produced each answer.

This means the safety-critical parts of the system (crowd severity, accessible routing, emergency
escalation) are never at the mercy of an LLM's non-determinism, while fans and operators still get the
fluency and multilingual reach of GenAI whenever it's available.

## 2. Component map

```
backend/
  app/
    main.py              FastAPI app, middleware wiring, global exception handlers
    config.py             Environment-driven settings (pydantic-settings)
    security.py            Rate limiter, security headers, admin auth, prompt-injection filter
    schemas.py              Pydantic request/response models (single source of truth for validation)
    data/
      stadium_map.py         Static venue graph + Dijkstra pathfinding (deterministic core for navigation)
      transit.py              Mock parking-lot / shuttle / transit dataset (deterministic core for transport)
    services/
      ai_service.py           Single choke point to the Anthropic API (retries, timeouts, never raises)
      navigation.py            Route computation + GenAI narrative
      crowd.py                 Occupancy thresholds + GenAI operator briefing
      accessibility.py         Grounded accessibility guidance
      transport.py             Parking/shuttle/transit ranking + GenAI recommendation narrator
      assistant.py             Chat, translation, sustainability tips, emergency guidance
    routers/
      api.py                   Public /api/v1/* endpoints
      admin.py                  Authenticated /admin/* operational status endpoint
frontend/
  index.html               Single-file SPA: accessible UI + local fallback logic mirroring the backend
```

## 3. Endpoint reference

All endpoints are under `/api/v1` and accept/return JSON. Full interactive docs at `/api/docs`.

| Method | Path | Purpose | Deterministic core |
|---|---|---|---|
| POST | `/chat` | Multilingual fan/staff assistant | Keyword-based suggested-action routing |
| POST | `/navigate` | Turn-by-turn wayfinding | Dijkstra shortest path over the venue graph, accessibility-aware |
| POST | `/crowd/analyze` | Crowd safety alerts + operator briefing | Fixed occupancy thresholds (70/85/95%) |
| POST | `/accessibility` | Accessibility concierge | Static, curated resource list (never invented) |
| POST | `/transport` | Parking / shuttle / transit recommendation | Occupancy-aware lot ranking + accessibility filtering over a mock transit dataset |
| POST | `/translate` | Free-text translation | N/A — pure GenAI feature, degrades to a labeled passthrough |
| POST | `/sustainability` | Personalized sustainability tips | Static tip bank fallback |
| POST | `/emergency` | Real-time safety decision support | Keyword-based mandatory human-escalation list |
| GET | `/health` | Liveness + GenAI availability | — |
| GET | `/admin/status` (auth required) | Operator deployment status | — |

## 4. Data flow example — Crowd Pulse

1. Frontend collects zone occupancy readings (in production: fed by turnstile counters, CCTV-derived
   density estimation, or IoT sensors — see `docs/UNFINISHED.md`).
2. `POST /api/v1/crowd/analyze` validates the payload (`CrowdAnalysisRequest`, 1–50 zones, occupancy
   clamped 0–100).
3. `services/crowd.py` classifies every zone against fixed thresholds — this never touches the network.
4. If any alert exists, the alert list is handed to Claude with a tight prompt ("state the biggest risk
   first... max 60 words... no filler") to produce an operator-readable one-paragraph briefing.
5. If GenAI is unavailable, a deterministic summary sentence is generated from the same alert list.
6. The response is rendered in the frontend's "Stadium Pulse" radial gauge plus a severity-sorted alert
   list, colour-coded and screen-reader-labelled.

## 5. Why FastAPI + vanilla JS (not Next.js) for this deliverable

This project intentionally ships a framework-light frontend (no build step, no bundler, no npm install
required) so it can be opened, run, and evaluated in under a minute — important for a hackathon judging
context — while the backend is a clean, swappable REST API that a richer framework (React/Next.js, as used
in other in-progress stadium tooling) can consume directly without any backend changes. See
`docs/UNFINISHED.md` for the planned Next.js migration path.
