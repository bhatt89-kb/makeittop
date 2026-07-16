from __future__ import annotations

from typing import List

from app.data.stadium_map import zone_display_name
from app.data.transit import (
    PARKING_LOTS,
    TRANSIT_LINES,
    accessible_spaces_available,
    parking_occupancy_percent,
)
from app.schemas import TransportOption, TransportRequest, TransportResponse
from app.security import sanitize_user_text
from app.services import ai_service

# Deterministic thresholds for parking-lot status. This is the layer that
# must never depend on a network call: a fan deciding whether to drive or
# take the shuttle needs a correct answer even if the AI provider is down.
_LOT_FULL_THRESHOLD = 98.0
_LOT_NEAR_FULL_THRESHOLD = 90.0


def _car_options(req: TransportRequest, needs_accessible: bool) -> List[TransportOption]:
    options: List[TransportOption] = []
    for lot_id, lot in PARKING_LOTS.items():
        occupancy = parking_occupancy_percent(lot_id)
        free_accessible = accessible_spaces_available(lot_id)

        if needs_accessible and free_accessible <= 0:
            continue  # no accessible spaces left at this lot: don't recommend it

        if occupancy >= _LOT_FULL_THRESHOLD:
            status = "full"
        elif occupancy >= _LOT_NEAR_FULL_THRESHOLD:
            status = "near_full"
        else:
            status = "available"

        detail = (
            f"{occupancy:.0f}% full, {lot['walk_minutes_to_gate']} min walk to "
            f"{zone_display_name(lot['nearest_gate'])}."
        )
        if needs_accessible:
            detail += f" {free_accessible} accessible space(s) free."

        options.append(
            TransportOption(
                option_id=lot_id,
                mode="car",
                name=lot["name"],
                detail=detail,
                eta_minutes=float(lot["walk_minutes_to_gate"]),
                accessible=free_accessible > 0,
                status=status,
            )
        )
    return options


def _transit_options(req: TransportRequest, needs_accessible: bool, mode_filter: str | None) -> List[TransportOption]:
    options: List[TransportOption] = []
    for line_id, line in TRANSIT_LINES.items():
        if mode_filter and line["mode"] != mode_filter:
            continue
        if needs_accessible and not line["accessible"]:
            continue

        eta = line["frequency_minutes"] / 2 + line["walk_minutes_to_gate"]  # avg wait + walk
        detail = (
            f"Every {line['frequency_minutes']} min from {line['pickup_point']}, "
            f"{line['walk_minutes_to_gate']} min walk to {zone_display_name(line['nearest_gate'])}."
        )
        options.append(
            TransportOption(
                option_id=line_id,
                mode=line["mode"],
                name=line["name"],
                detail=detail,
                eta_minutes=round(eta, 1),
                accessible=line["accessible"],
                status=line["status"],
            )
        )
    return options


def _rank(options: List[TransportOption]) -> List[TransportOption]:
    # Full/suspended options sink to the bottom regardless of ETA; among the
    # rest, lowest ETA wins. This is the one deterministic ranking the
    # product promises never to compromise, even if GenAI disagrees.
    bad_status = {"full", "suspended"}

    def sort_key(opt: TransportOption):
        return (1 if opt.status in bad_status else 0, opt.eta_minutes)

    return sorted(options, key=sort_key)


async def get_transport_options(req: TransportRequest) -> TransportResponse:
    needs_accessible = any(
        n.lower() in {"wheelchair", "mobility", "accessible"} for n in req.accessibility_needs
    )

    options: List[TransportOption] = []
    if req.mode in (None, "car"):
        options += _car_options(req, needs_accessible)
    if req.mode in (None, "shuttle"):
        options += _transit_options(req, needs_accessible, "shuttle")
    if req.mode in (None, "transit"):
        options += _transit_options(req, needs_accessible, "transit")

    options = _rank(options)
    recommended_id = options[0].option_id if options else None

    summary = await _generate_summary(req, options, needs_accessible)
    source = "genai" if summary else "fallback"
    if not summary:
        summary = _fallback_summary(options, needs_accessible)

    return TransportResponse(
        options=options, recommended_option_id=recommended_id, summary=summary, source=source,
    )


def _fallback_summary(options: List[TransportOption], needs_accessible: bool) -> str:
    if not options:
        if needs_accessible:
            return "No accessible transport options currently match your needs. Please check with Guest Services."
        return "No transport options currently match your filters."
    best = options[0]
    if best.status in {"full", "suspended"}:
        return f"All matching options are currently constrained; the least-delayed is {best.name}."
    return f"Best option: {best.name} — {best.detail}"


async def _generate_summary(
    req: TransportRequest, options: List[TransportOption], needs_accessible: bool
) -> str | None:
    if not options:
        return None
    system_prompt = (
        "You are 'Ana', a transport-advisory assistant for FIFA World Cup 2026 stadium fans. Given a "
        "ranked list of parking, shuttle, and transit options, recommend the single best one in one tight "
        "sentence (max 35 words), then optionally one short backup sentence. Be concrete, warm, and "
        "practical. Never invent an option that isn't in the list. Respond only in "
        f"{req.language}."
    )
    options_text = "\n".join(
        f"- [{o.mode}] {o.name}: {o.detail} (status: {o.status}, ETA {o.eta_minutes:.0f} min)"
        for o in options[:5]
    )
    context_bits = [f"Party size: {req.party_size}"]
    if req.minutes_to_kickoff is not None:
        context_bits.append(f"Minutes to kickoff: {req.minutes_to_kickoff}")
    if needs_accessible:
        context_bits.append("Requires wheelchair-accessible option")
    user_prompt = (
        f"{sanitize_user_text(', '.join(context_bits))}\nRanked options:\n{sanitize_user_text(options_text)}"
    )
    return await ai_service.generate(system_prompt, user_prompt, max_tokens=150)
