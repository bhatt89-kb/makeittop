from __future__ import annotations

from typing import List

from app.data.stadium_map import zone_display_name
from app.schemas import CrowdAlert, CrowdAnalysisRequest, CrowdAnalysisResponse
from app.security import sanitize_user_text
from app.services import ai_service

# Deterministic, auditable thresholds. This is the layer that must never
# depend on a network call: crowd-safety alerts fire even if the GenAI
# provider is completely unavailable.
_THRESHOLDS = [
    (95, "critical", "Immediate action required: halt inflow and open overflow route."),
    (85, "high", "Deploy additional stewards and open an alternate concourse."),
    (70, "medium", "Monitor closely; consider soft crowd redirection."),
    (0, "low", "No action required."),
]


def _classify(occupancy: float) -> tuple[str, str]:
    for threshold, severity, action in _THRESHOLDS:
        if occupancy >= threshold:
            return severity, action
    return "low", "No action required."


async def analyze_crowd(req: CrowdAnalysisRequest) -> CrowdAnalysisResponse:
    alerts: List[CrowdAlert] = []
    for zone in req.zones:
        severity, action = _classify(zone.occupancy_percent)
        if severity == "low":
            continue
        alerts.append(
            CrowdAlert(
                zone_id=zone.zone_id,
                severity=severity,
                message=(
                    f"{zone_display_name(zone.zone_id)} is at {zone.occupancy_percent:.0f}% capacity "
                    f"(inflow {zone.inflow_rate:+.0f}/min)."
                ),
                recommended_action=action,
            )
        )

    # Highest severity first for operator triage.
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda a: order[a.severity])

    summary = await _generate_summary(req, alerts)
    source = "genai" if summary else "fallback"
    if not summary:
        summary = _fallback_summary(alerts)

    return CrowdAnalysisResponse(alerts=alerts, overall_summary=summary, source=source)


def _fallback_summary(alerts: List[CrowdAlert]) -> str:
    if not alerts:
        return "All monitored zones are within safe capacity thresholds. No operator action needed."
    critical = [a for a in alerts if a.severity == "critical"]
    if critical:
        zones = ", ".join(zone_display_name(a.zone_id) for a in critical)
        return f"URGENT: {zones} at critical capacity. Dispatch stewards and open overflow routes immediately."
    return f"{len(alerts)} zone(s) require attention. Highest priority: {alerts[0].message}"


async def _generate_summary(req: CrowdAnalysisRequest, alerts: List[CrowdAlert]) -> str | None:
    if not alerts:
        return None  # fallback text is already the ideal "all clear" message; skip an AI call
    system_prompt = (
        "You are an operations-intelligence assistant for FIFA World Cup 2026 stadium control room staff. "
        "Given a list of crowd alerts, produce a single tight paragraph (max 60 words) an operator can read "
        "in 5 seconds during a live match: state the biggest risk first, then the recommended action. "
        "Be concrete and calm. No filler, no apologies."
    )
    alerts_text = "\n".join(
        f"- [{a.severity.upper()}] {a.message} Action: {a.recommended_action}" for a in alerts
    )
    user_prompt = f"Event phase: {sanitize_user_text(req.event_phase)}\nAlerts:\n{sanitize_user_text(alerts_text)}"
    return await ai_service.generate(system_prompt, user_prompt, max_tokens=150)
