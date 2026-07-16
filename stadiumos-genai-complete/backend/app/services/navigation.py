from __future__ import annotations

import random
from typing import List

from app.data.stadium_map import STADIUM_GRAPH, is_valid_zone, shortest_path, zone_display_name
from app.schemas import NavigationRequest, NavigationResponse, NavigationStep
from app.security import sanitize_user_text
from app.services import ai_service

_CROWD_LEVELS = ["low", "moderate", "high"]


def _simulated_crowd_level(zone_id: str) -> str:
    # Deterministic-but-varied pseudo occupancy so demos are stable per zone.
    random.seed(zone_id)
    return random.choice(_CROWD_LEVELS)


def _build_steps(path: List[str]) -> List[NavigationStep]:
    steps: List[NavigationStep] = []
    for i in range(len(path) - 1):
        current, nxt = path[i], path[i + 1]
        weight = next(w for n, w in STADIUM_GRAPH[current]["neighbors"] if n == nxt)
        steps.append(
            NavigationStep(
                instruction=f"From {zone_display_name(current)}, proceed to {zone_display_name(nxt)}.",
                zone=nxt,
                estimated_minutes=float(weight),
                crowd_level=_simulated_crowd_level(nxt),
            )
        )
    return steps


async def get_navigation(req: NavigationRequest) -> NavigationResponse:
    origin = req.origin.strip().lower().replace(" ", "_")
    destination = req.destination.strip().lower().replace(" ", "_")

    if not is_valid_zone(origin) or not is_valid_zone(destination):
        return NavigationResponse(
            steps=[], total_minutes=0, accessible=False, source="fallback",
            narrative=(
                f"I couldn't find a match for '{req.origin}' or '{req.destination}' on the venue map. "
                "Try a gate name (Gate A/B/C), a section range (e.g. '101-120'), or a landmark "
                "like 'Family Zone', 'Medical Station' or 'Accessible Seating'."
            ),
        )

    avoid: List[str] = []
    if req.accessibility_needs and "wheelchair" in [n.lower() for n in req.accessibility_needs]:
        avoid = [z for z, meta in STADIUM_GRAPH.items() if not meta["accessible"]]

    path, total_minutes = shortest_path(origin, destination, avoid_zones=avoid)
    if not path:
        return NavigationResponse(
            steps=[], total_minutes=0, accessible=False, source="fallback",
            narrative="No accessible route was found between those two points. Please ask a nearby steward for assisted routing.",
        )

    steps = _build_steps(path)
    accessible = all(STADIUM_GRAPH[z]["accessible"] for z in path)

    narrative = await _generate_narrative(req, path, steps, accessible)
    source = "genai" if narrative else "fallback"
    if not narrative:
        narrative = _fallback_narrative(req, steps, accessible)

    return NavigationResponse(
        steps=steps, total_minutes=total_minutes, narrative=narrative,
        accessible=accessible, source=source,
    )


def _fallback_narrative(req: NavigationRequest, steps: List[NavigationStep], accessible: bool) -> str:
    parts = [s.instruction for s in steps]
    note = " This route avoids stairs and uses accessible ramps throughout." if accessible and req.accessibility_needs else ""
    return " ".join(parts) + note


async def _generate_narrative(req: NavigationRequest, path, steps, accessible) -> str | None:
    system_prompt = (
        "You are the wayfinding assistant for a FIFA World Cup 2026 host stadium. "
        "Turn a list of routing steps into 2-4 short, friendly, encouraging sentences "
        "a fan can follow while walking. Mention crowd levels only if 'high'. "
        "If the fan requested accessibility support, reassure them the route avoids stairs. "
        f"Respond only in {req.language}. Do not invent landmarks not present in the steps."
    )
    steps_text = "\n".join(f"- {s.instruction} (~{s.estimated_minutes} min, crowd: {s.crowd_level})" for s in steps)
    user_prompt = (
        f"Route steps:\n{sanitize_user_text(steps_text)}\n"
        f"Accessibility requested: {bool(req.accessibility_needs)}\n"
        f"Route is fully accessible: {accessible}"
    )
    return await ai_service.generate(system_prompt, user_prompt, max_tokens=220)
