# Security

This document describes the threat model and controls implemented in `app/security.py` and elsewhere,
and is explicit about what is **not** covered by this hackathon-scope deliverable.

## 1. Controls implemented

| Control | Where | Mitigates |
|---|---|---|
| Strict input validation (length caps, enum checks, control-char rejection) | `app/schemas.py` | Oversized payloads, malformed input, log/terminal injection via control characters |
| Sliding-window rate limiter (per client IP, configurable) | `app/security.py::enforce_rate_limit` | Abuse, brute force, cost-exhaustion attacks against the GenAI provider |
| Request body size guard | `app/security.py::BodySizeLimitMiddleware` | Oversized-payload denial of service |
| Security response headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS in production) | `app/security.py::SecurityHeadersMiddleware` | Clickjacking, MIME sniffing, referrer leakage, unwanted browser feature access |
| CORS allow-list (no wildcard, explicit methods/headers) | `app/main.py` | Cross-origin abuse from untrusted sites |
| Constant-time admin API key comparison | `app/security.py::require_admin_key` (`hmac.compare_digest`) | Timing attacks against the admin key |
| Prompt-injection / jailbreak heuristic filter | `app/security.py::sanitize_user_text` | Basic "ignore previous instructions", "developer mode", raw `<script>` payloads reaching the LLM prompt or being reflected to other users |
| System-prompt instruction to ignore in-message role-change attempts | `app/services/assistant.py` (chat system prompt) | Defense-in-depth against prompt injection, layered on top of the heuristic filter |
| Global exception handlers that never leak stack traces | `app/main.py` | Information disclosure |
| Non-root Docker user | `backend/Dockerfile` | Container breakout blast radius |
| Secrets only via environment variables, `.env` excluded from version control, `.env.example` committed instead | `backend/.env.example`, `.gitignore` | Credential leakage |
| No secrets ever logged; AI service logs only exception messages, never prompts/payloads containing user PII | `app/services/ai_service.py` | Log-based data leakage |
| `ai_service.generate()` never raises to callers — always degrades to `None` → rule-based fallback | `app/services/ai_service.py` | A provider outage or malicious/slow response can't cascade into a service crash |

## 2. Prompt-injection posture

This app treats every field that reaches an LLM prompt as **untrusted input**, and every LLM *output* that
is rendered back to a user as **untrusted output**:

- Inbound: `sanitize_user_text()` strips known injection patterns before interpolation; system prompts
  additionally instruct the model to ignore embedded role-change or instruction-reveal attempts.
- Outbound: the frontend renders all AI-generated text via `textContent`/`escapeHtml()`, never
  `innerHTML` with raw text, which prevents a successfully-injected response from executing script in a
  fan's or operator's browser.
- Accessibility and navigation prompts explicitly constrain the model to *only* use facts it was given
  ("using ONLY the resource list provided", "do not invent landmarks not present in the steps"), reducing
  hallucination that could otherwise misdirect a fan or misstate an accessibility resource.

## 3. Explicitly out of scope for this deliverable

Being transparent about this is itself part of good security practice — see `docs/UNFINISHED.md` for the
full list and rationale. In short: this app does not yet implement authenticated user accounts / OAuth,
a persistent audit log store, a production-grade WAF, secrets-manager integration, or automated dependency
vulnerability scanning in CI. All of these are named, scoped, and prioritized in `docs/UNFINISHED.md` rather
than silently omitted.
