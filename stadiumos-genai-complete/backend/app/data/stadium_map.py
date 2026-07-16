"""
A small, self-contained stadium graph used to power deterministic
navigation and crowd simulation without requiring a live venue feed.

In a production deployment this module would be replaced by a connector
to the venue's real IoT / turnstile / CCTV-derived occupancy feed — see
docs/UNFINISHED.md, item "Live venue data integration".
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# zone_id -> (display name, list of (neighbor_zone_id, walk_minutes))
STADIUM_GRAPH: Dict[str, Dict] = {
    "gate_a": {"name": "Gate A (Main Entrance)", "neighbors": [("concourse_north", 2)], "accessible": True},
    "gate_b": {"name": "Gate B (East Entrance)", "neighbors": [("concourse_east", 2)], "accessible": True},
    "gate_c": {"name": "Gate C (West Entrance)", "neighbors": [("concourse_west", 2)], "accessible": False},
    "concourse_north": {
        "name": "North Concourse", "accessible": True,
        "neighbors": [("gate_a", 2), ("section_101_120", 3), ("food_court_north", 1), ("concourse_east", 4)],
    },
    "concourse_east": {
        "name": "East Concourse", "accessible": True,
        "neighbors": [("gate_b", 2), ("section_201_220", 3), ("family_zone", 2), ("concourse_north", 4), ("concourse_south", 4)],
    },
    "concourse_west": {
        "name": "West Concourse", "accessible": False,
        "neighbors": [("gate_c", 2), ("section_301_320", 4), ("press_zone", 2), ("concourse_south", 4)],
    },
    "concourse_south": {
        "name": "South Concourse", "accessible": True,
        "neighbors": [("section_401_420", 3), ("accessible_seating", 1), ("medical_station", 1), ("concourse_east", 4), ("concourse_west", 4)],
    },
    "section_101_120": {"name": "Lower Bowl North (101-120)", "accessible": True, "neighbors": [("concourse_north", 3)]},
    "section_201_220": {"name": "Lower Bowl East (201-220)", "accessible": True, "neighbors": [("concourse_east", 3)]},
    "section_301_320": {"name": "Upper Bowl West (301-320)", "accessible": False, "neighbors": [("concourse_west", 4)]},
    "section_401_420": {"name": "Lower Bowl South (401-420)", "accessible": True, "neighbors": [("concourse_south", 3)]},
    "accessible_seating": {"name": "Accessible Seating Platform", "accessible": True, "neighbors": [("concourse_south", 1)]},
    "family_zone": {"name": "Family & Fan Zone", "accessible": True, "neighbors": [("concourse_east", 2)]},
    "food_court_north": {"name": "North Food Court", "accessible": True, "neighbors": [("concourse_north", 1)]},
    "medical_station": {"name": "Medical Station", "accessible": True, "neighbors": [("concourse_south", 1)]},
    "press_zone": {"name": "Media & Press Zone", "accessible": False, "neighbors": [("concourse_west", 2)]},
}


def zone_display_name(zone_id: str) -> str:
    zone = STADIUM_GRAPH.get(zone_id)
    return zone["name"] if zone else zone_id


def is_valid_zone(zone_id: str) -> bool:
    return zone_id in STADIUM_GRAPH


def shortest_path(origin: str, destination: str, avoid_zones: List[str] | None = None) -> Tuple[List[str], float]:
    """Dijkstra over the static graph. Returns (zone_path, total_minutes)."""
    import heapq

    avoid_zones = set(avoid_zones or [])
    if origin not in STADIUM_GRAPH or destination not in STADIUM_GRAPH:
        return [], 0.0

    distances: Dict[str, float] = {origin: 0.0}
    previous: Dict[str, str] = {}
    visited = set()
    heap: List[Tuple[float, str]] = [(0.0, origin)]

    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == destination:
            break
        for neighbor, weight in STADIUM_GRAPH[node]["neighbors"]:
            if neighbor in avoid_zones and neighbor != destination:
                continue
            new_dist = dist + weight
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                previous[neighbor] = node
                heapq.heappush(heap, (new_dist, neighbor))

    if destination not in distances:
        return [], 0.0

    path = [destination]
    while path[-1] != origin:
        path.append(previous[path[-1]])
    path.reverse()
    return path, distances[destination]
