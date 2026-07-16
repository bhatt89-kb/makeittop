# What's unfinished, simplified, or left for future work

Honesty about scope boundaries is part of the deliverable. Everything below is a conscious, documented
trade-off made to ship a working, tested, secure application within a single build session — not a
silently-cut corner. If you're a judge or a future contributor, this is the map of where to invest next.

## 1. Data: mocked venue graph instead of live venue systems

`app/data/stadium_map.py` is a small, hand-authored 16-zone graph. In production this would be replaced by:

- A live integration with the venue's **turnstile / ticketing system** for real entry counts per gate.
- **CCTV-derived crowd density estimation** (a computer-vision model feeding `occupancy_percent` in
  real time instead of a manually-submitted number) — this is the single highest-impact next step for the
  Crowd Pulse module, and the API contract (`CrowdAnalysisRequest`) is already shaped to accept it without
  any breaking change.
- A **full venue BIM/GIS export** for the navigation graph (accurate distances, multi-floor routing,
  elevator/escalator status) instead of the current flat, illustrative zone list.
- **IoT occupancy sensors** at gates and concourses instead of simulated `_simulated_crowd_level()` per-step
  crowd tags in the navigation service.

## 2. Transportation module: built on mock data, not a live transit/parking feed

`/api/v1/transport` is now a dedicated endpoint (`app/services/transport.py`, `app/data/transit.py`),
following the exact same deterministic-core + GenAI-narrator + rule-based-fallback pattern as every other
module, with its own request/response schemas, router entry, frontend tab, and test suite. Given a mode
filter, party size, optional minutes-to-kickoff, and accessibility needs, it ranks parking lots, shuttle
lines, and transit lines by occupancy/ETA/accessibility and asks Claude to narrate the top pick — falling
back to a deterministic "Best option: X — detail" sentence if GenAI is unavailable.

What's still mocked, and the natural next step:

- **Parking occupancy is hand-authored**, not fed by a live parking-management system. Swapping
  `app/data/transit.py`'s static `PARKING_LOTS` dict for a real feed requires no change to
  `services/transport.py`'s ranking logic or the `/transport` API contract.
- **No GTFS-realtime / transit-agency API integration** — shuttle and transit line status/headways are
  fixed values, not live signals.
- **No parking reservation or payment flow** — this module recommends, it doesn't book.

## 3. Frontend: no build pipeline, no framework, no automated UI tests

The frontend is deliberately a single dependency-free HTML file so it's instantly runnable for judging.
For a real production rollout this should become:

- A proper **Next.js/React app** (matching the stack direction already used in the team's other stadium
  tooling), consuming the exact same `/api/v1/*` REST contract this backend already exposes — no backend
  changes required to make that swap.
- **Automated UI/E2E tests** (Playwright or Cypress), including automated accessibility scanning
  (`axe-core` or `pa11y`) wired into CI, rather than the manual checklist in `docs/ACCESSIBILITY.md`.
- **Real i18n**, i.e. translated *UI chrome* (button labels, headings) via a proper i18n library, not just
  translated *assistant responses*. Right now only Ana's replies are multilingual; the interface labels
  around her are English-only.

## 4. Authentication & multi-tenancy

There is no user login, no session persistence beyond an optional client-supplied `session_id` on chat
requests (currently unused for actual conversation memory — each chat call is stateless), and no
per-venue/per-tournament tenant isolation. A production version would need:

- OAuth/SSO for staff and volunteer roles (the `UserRole` enum already exists in `schemas.py` and is
  threaded through to the chat prompt, but nothing currently verifies a caller actually *is* that role).
- Conversation memory per fan session (would change `chat()` from stateless to conversation-aware, likely
  via a short-lived Redis-backed history keyed by `session_id`).
- Multi-venue configuration (today's stadium graph, thresholds, and resource list are all hard-coded for
  one illustrative venue).

## 5. Operational hardening not yet done

- **No secrets manager integration** — `.env` / plain environment variables only. Production should use
  AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
- **No dependency vulnerability scanning in CI** (e.g. `pip-audit`, `npm audit`, Dependabot) — the
  `requirements.txt` versions are pinned but not continuously monitored.
- **No persistent, queryable audit log** — the app logs to stdout via the standard `logging` module;
  there's no structured log shipping to something like CloudWatch/Datadog, and no retained record of
  emergency-endpoint calls for post-incident review, which a real deployment would need for accountability.
- **In-memory rate limiter** resets on process restart and doesn't share state across multiple backend
  instances — a real multi-instance deployment needs a shared store (Redis) for rate-limit state.
- **No load testing performed.** The architecture (async FastAPI, capped AI timeouts, short-circuited
  "no alerts → skip the AI call entirely" logic in crowd analysis) is designed with matchday burst traffic
  in mind, but no k6/Locust load test has actually been run against it.

## 6. GenAI quality work not yet done

- **No prompt regression test suite against the live model** — the test suite proves the *code contract*
  around the AI layer (never raises, degrades correctly, etc.) but does not evaluate actual GenAI *output
  quality* (e.g. via a golden-answer eval set), since that requires live API calls and human/LLM-graded
  review, which is out of scope for an offline-runnable CI suite.
- **No conversation memory / follow-up question handling** in chat (see item 4) — today each message to
  Ana is answered independently.
- **Translation quality has not been benchmarked** against a reference translation service; the `/translate`
  endpoint is a straightforward Claude call with no back-translation verification step.

## 7. What I'd build next, in priority order

1. CCTV/IoT-fed live crowd data (replaces the mocked occupancy input with the real signal that makes Crowd
   Pulse actually operational).
2. Live parking/transit data feeds for the Transport module (real occupancy + GTFS-realtime), replacing
   `app/data/transit.py`'s static dataset without any change to the ranking logic or API contract.
3. Automated accessibility testing in CI (`axe-core`) to convert the manual checklist into a hard gate.
4. Session-aware chat memory for more natural multi-turn conversations with Ana.
5. Next.js frontend migration, reusing the existing REST API unchanged.
