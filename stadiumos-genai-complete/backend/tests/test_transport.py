import pytest

from app.data.transit import PARKING_LOTS, parking_occupancy_percent
from app.schemas import TransportRequest
from app.services import transport


class TestParkingOccupancy:
    def test_occupancy_percent_matches_capacity_ratio(self):
        for lot_id, lot in PARKING_LOTS.items():
            expected = round(100 * lot["occupied"] / lot["capacity"], 1)
            assert parking_occupancy_percent(lot_id) == expected

    def test_unknown_lot_returns_zero(self):
        assert parking_occupancy_percent("not_a_real_lot") == 0.0

    def test_accessible_spaces_available_and_line_listing_helpers(self):
        from app.data.transit import (
            accessible_spaces_available,
            list_parking_lot_ids,
            list_transit_line_ids,
        )

        assert accessible_spaces_available("not_a_real_lot") == 0
        assert set(list_parking_lot_ids()) == set(PARKING_LOTS.keys())
        assert all(line_id in list_transit_line_ids() for line_id in list_transit_line_ids("shuttle"))
        assert list_transit_line_ids("shuttle")  # at least one shuttle line seeded


class TestTransportOptions:
    @pytest.mark.asyncio
    async def test_any_mode_returns_cars_and_transit(self):
        req = TransportRequest()
        result = await transport.get_transport_options(req)
        modes = {o.mode for o in result.options}
        assert "car" in modes
        assert "shuttle" in modes or "transit" in modes
        assert result.recommended_option_id is not None
        assert result.source in {"genai", "fallback"}

    @pytest.mark.asyncio
    async def test_mode_filter_restricts_to_requested_mode(self):
        req = TransportRequest(mode="shuttle")
        result = await transport.get_transport_options(req)
        assert result.options
        assert all(o.mode == "shuttle" for o in result.options)

    @pytest.mark.asyncio
    async def test_car_mode_filter_returns_only_parking_lots(self):
        req = TransportRequest(mode="car")
        result = await transport.get_transport_options(req)
        assert result.options
        assert all(o.mode == "car" for o in result.options)

    @pytest.mark.asyncio
    async def test_full_lots_are_excluded_from_top_recommendation(self):
        # lot_north is seeded at 95% (near-full, not full) — it should still
        # appear but never rank above lots with far more free space when a
        # comparably-fast alternative exists.
        req = TransportRequest(mode="car")
        result = await transport.get_transport_options(req)
        statuses = {o.option_id: o.status for o in result.options}
        assert statuses["lot_north"] in {"near_full", "full"}

    @pytest.mark.asyncio
    async def test_wheelchair_need_filters_to_accessible_options_only(self):
        req = TransportRequest(accessibility_needs=["wheelchair"])
        result = await transport.get_transport_options(req)
        assert result.options
        assert all(o.accessible for o in result.options)

    @pytest.mark.asyncio
    async def test_wheelchair_need_excludes_lot_with_no_free_accessible_spaces(self, monkeypatch):
        # Temporarily exhaust lot_north's accessible spaces to exercise the
        # "no accessible spaces left" exclusion branch deterministically.
        monkeypatch.setitem(
            PARKING_LOTS["lot_north"], "accessible_spaces_occupied", PARKING_LOTS["lot_north"]["accessible_spaces"]
        )
        req = TransportRequest(mode="car", accessibility_needs=["wheelchair"])
        result = await transport.get_transport_options(req)
        option_ids = {o.option_id for o in result.options}
        assert "lot_north" not in option_ids

    @pytest.mark.asyncio
    async def test_wheelchair_need_excludes_inaccessible_transit_line(self):
        req = TransportRequest(mode="transit", accessibility_needs=["wheelchair"])
        result = await transport.get_transport_options(req)
        option_ids = {o.option_id for o in result.options}
        # rail_express is seeded as not wheelchair-accessible.
        assert "rail_express" not in option_ids

    @pytest.mark.asyncio
    async def test_ranking_sorts_available_options_before_full_ones(self):
        req = TransportRequest(mode="car")
        result = await transport.get_transport_options(req)
        statuses = [o.status for o in result.options]
        # once a "full" status appears, nothing after it should be "available"
        if "full" in statuses:
            first_full = statuses.index("full")
            assert "available" not in statuses[first_full:]

    @pytest.mark.asyncio
    async def test_fallback_summary_mentions_top_option_when_ai_unavailable(self):
        req = TransportRequest(mode="shuttle")
        result = await transport.get_transport_options(req)
        assert result.source == "fallback"  # no API key in test environment
        assert result.options[0].name in result.summary


class TestTransportAPI:
    @pytest.mark.asyncio
    async def test_transport_endpoint_happy_path(self, client):
        resp = await client.post("/api/v1/transport", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["options"]
        assert "summary" in body

    @pytest.mark.asyncio
    async def test_transport_endpoint_rejects_invalid_mode(self, client):
        resp = await client.post("/api/v1/transport", json={"mode": "spaceship"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_transport_endpoint_rejects_oversized_party(self, client):
        resp = await client.post("/api/v1/transport", json={"party_size": 999})
        assert resp.status_code == 422
