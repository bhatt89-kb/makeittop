"""
A small, self-contained transportation dataset (parking lots, shuttle
lines, and public-transit lines) used to power deterministic transport
recommendations without requiring a live venue/transit feed.

Same philosophy as `app/data/stadium_map.py`: this is intentionally a
mocked, hand-authored dataset so the Transport module is demoable and
testable with zero external dependencies. In production this would be
replaced by:

- A live parking-management-system feed for `occupied_spaces` per lot.
- A GTFS-realtime / transit-agency API for shuttle & transit line status
  and headways.

See docs/UNFINISHED.md, item "Transportation feature", for the full
scope note.
"""
from __future__ import annotations

from typing import Dict, List, TypedDict


class ParkingLot(TypedDict):
    name: str
    capacity: int
    occupied: int
    walk_minutes_to_gate: str
    nearest_gate: str
    accessible_spaces: int
    accessible_spaces_occupied: int


class TransitLine(TypedDict):
    name: str
    mode: str  # "shuttle" | "transit"
    frequency_minutes: int
    walk_minutes_to_gate: int
    pickup_point: str
    nearest_gate: str
    accessible: bool
    status: str  # "on_time" | "delayed" | "suspended"


PARKING_LOTS: Dict[str, ParkingLot] = {
    "lot_north": {
        "name": "North Lot (P1)", "capacity": 1200, "occupied": 1140,
        "walk_minutes_to_gate": 6, "nearest_gate": "gate_a",
        "accessible_spaces": 40, "accessible_spaces_occupied": 22,
    },
    "lot_east": {
        "name": "East Lot (P2)", "capacity": 900, "occupied": 540,
        "walk_minutes_to_gate": 8, "nearest_gate": "gate_b",
        "accessible_spaces": 30, "accessible_spaces_occupied": 11,
    },
    "lot_south_overflow": {
        "name": "South Overflow Lot (P3)", "capacity": 1500, "occupied": 300,
        "walk_minutes_to_gate": 15, "nearest_gate": "gate_c",
        "accessible_spaces": 25, "accessible_spaces_occupied": 4,
    },
}

TRANSIT_LINES: Dict[str, TransitLine] = {
    "shuttle_1": {
        "name": "Shuttle Line 1 — Downtown Hub", "mode": "shuttle", "frequency_minutes": 8,
        "walk_minutes_to_gate": 2, "pickup_point": "North Transit Hub", "nearest_gate": "gate_a",
        "accessible": True, "status": "on_time",
    },
    "shuttle_2": {
        "name": "Shuttle Line 2 — Riverside Park & Ride", "mode": "shuttle", "frequency_minutes": 8,
        "walk_minutes_to_gate": 2, "pickup_point": "Riverside Park & Ride", "nearest_gate": "gate_b",
        "accessible": True, "status": "on_time",
    },
    "metro_blue": {
        "name": "Metro Blue Line — Stadium Station", "mode": "transit", "frequency_minutes": 6,
        "walk_minutes_to_gate": 9, "pickup_point": "Stadium Station", "nearest_gate": "gate_b",
        "accessible": True, "status": "on_time",
    },
    "rail_express": {
        "name": "Regional Rail Express — Matchday Special", "mode": "transit", "frequency_minutes": 20,
        "walk_minutes_to_gate": 12, "pickup_point": "Central Station", "nearest_gate": "gate_c",
        "accessible": False, "status": "on_time",
    },
}


def parking_occupancy_percent(lot_id: str) -> float:
    lot = PARKING_LOTS.get(lot_id)
    if not lot or lot["capacity"] <= 0:
        return 0.0
    return round(100 * lot["occupied"] / lot["capacity"], 1)


def accessible_spaces_available(lot_id: str) -> int:
    lot = PARKING_LOTS.get(lot_id)
    if not lot:
        return 0
    return max(0, lot["accessible_spaces"] - lot["accessible_spaces_occupied"])


def list_parking_lot_ids() -> List[str]:
    return list(PARKING_LOTS.keys())


def list_transit_line_ids(mode: str | None = None) -> List[str]:
    if mode is None:
        return list(TRANSIT_LINES.keys())
    return [k for k, v in TRANSIT_LINES.items() if v["mode"] == mode]
