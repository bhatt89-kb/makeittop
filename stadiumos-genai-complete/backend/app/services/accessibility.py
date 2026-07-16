from __future__ import annotations

from app.schemas import AccessibilityRequest, AccessibilityResponse
from app.security import sanitize_user_text
from app.services import ai_service

_STATIC_RESOURCES = [
    "Accessible Seating Platform — South Concourse, step-free from Gate A/B/D",
    "Sensory Room — quiet, low-light space near the Family Zone for neurodivergent fans",
    "Wheelchair loan desk — Gate A Guest Services, no reservation required",
    "Assistive listening devices — available at any Guest Services desk",
    "Companion/carer free-entry policy — present accessibility documentation at any gate",
]


async def get_accessibility_guidance(req: AccessibilityRequest) -> AccessibilityResponse:
    reply = await _generate(req)
    source = "genai" if reply else "fallback"
    if not reply:
        reply = _fallback(req)
    return AccessibilityResponse(guidance=reply, resources=_STATIC_RESOURCES, source=source)


def _fallback(req: AccessibilityRequest) -> str:
    needs = ", ".join(req.needs) if req.needs else "your accessibility needs"
    return (
        f"For {needs}, the Accessible Seating Platform on the South Concourse is step-free from Gates A, B and D. "
        "Guest Services desks near every gate can arrange a wheelchair escort, assistive listening device, "
        "or sensory-room access on request. Staff wearing a teal armband are trained accessibility stewards."
    )


async def _generate(req: AccessibilityRequest) -> str | None:
    system_prompt = (
        "You are the accessibility concierge for a FIFA World Cup 2026 stadium. Answer the fan's question "
        "using ONLY the resource list provided, in 2-4 plain-language sentences. Never invent a service, "
        "room, or policy that isn't in the list. If nothing in the list matches, say so and suggest asking "
        f"a teal-armband accessibility steward. Respond only in {req.language}."
    )
    user_prompt = (
        f"Fan question: {sanitize_user_text(req.query)}\n"
        f"Stated needs: {', '.join(req.needs) if req.needs else 'none specified'}\n"
        f"Available resources:\n" + "\n".join(f"- {r}" for r in _STATIC_RESOURCES)
    )
    return await ai_service.generate(system_prompt, user_prompt, max_tokens=200)
