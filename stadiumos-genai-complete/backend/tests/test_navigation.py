import pytest

from app.data.stadium_map import shortest_path
from app.schemas import NavigationRequest
from app.services import navigation


class TestShortestPath:
    def test_direct_neighbor(self):
        path, minutes = shortest_path("gate_a", "concourse_north")
        assert path == ["gate_a", "concourse_north"]
        assert minutes == 2

    def test_multi_hop(self):
        path, minutes = shortest_path("gate_a", "section_401_420")
        assert path[0] == "gate_a"
        assert path[-1] == "section_401_420"
        assert minutes > 0

    def test_unknown_zone_returns_empty(self):
        path, minutes = shortest_path("gate_a", "not_a_real_zone")
        assert path == []
        assert minutes == 0

    def test_avoid_zones_forces_detour(self):
        # concourse_west is not accessible; avoiding it should route elsewhere
        # for a destination reachable without it.
        path, _ = shortest_path("gate_a", "concourse_south", avoid_zones=["concourse_west"])
        assert "concourse_west" not in path


class TestNavigationEndpointLogic:
    @pytest.mark.asyncio
    async def test_valid_route_returns_steps(self):
        req = NavigationRequest(origin="Gate A", destination="Family Zone")
        result = await navigation.get_navigation(req)
        assert result.steps
        assert result.total_minutes > 0
        assert result.source in {"genai", "fallback"}

    @pytest.mark.asyncio
    async def test_invalid_zone_returns_helpful_message_not_error(self):
        req = NavigationRequest(origin="Nonexistent Place", destination="Gate A")
        result = await navigation.get_navigation(req)
        assert result.steps == []
        assert "couldn't find" in result.narrative.lower()

    @pytest.mark.asyncio
    async def test_wheelchair_request_avoids_inaccessible_zones(self):
        req = NavigationRequest(
            origin="Gate A", destination="Concourse South", accessibility_needs=["wheelchair"]
        )
        result = await navigation.get_navigation(req)
        assert result.accessible is True


class TestNavigationAPI:
    @pytest.mark.asyncio
    async def test_navigate_endpoint_happy_path(self, client):
        resp = await client.post(
            "/api/v1/navigate",
            json={"origin": "Gate A", "destination": "Medical Station"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "steps" in body and "narrative" in body

    @pytest.mark.asyncio
    async def test_navigate_endpoint_rejects_empty_origin(self, client):
        resp = await client.post("/api/v1/navigate", json={"origin": "", "destination": "Gate A"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_navigate_endpoint_rejects_oversized_field(self, client):
        resp = await client.post(
            "/api/v1/navigate", json={"origin": "A" * 500, "destination": "Gate A"}
        )
        assert resp.status_code == 422
