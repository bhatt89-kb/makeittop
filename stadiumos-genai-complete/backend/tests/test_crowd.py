import pytest

from app.schemas import CrowdAnalysisRequest, CrowdZoneReading
from app.services import crowd


class TestCrowdClassification:
    @pytest.mark.parametrize(
        "occupancy,expected_severity",
        [(10, None), (72, "medium"), (88, "high"), (97, "critical")],
    )
    @pytest.mark.asyncio
    async def test_severity_thresholds(self, occupancy, expected_severity):
        req = CrowdAnalysisRequest(zones=[CrowdZoneReading(zone_id="gate_a", occupancy_percent=occupancy)])
        result = await crowd.analyze_crowd(req)
        if expected_severity is None:
            assert result.alerts == []
        else:
            assert result.alerts[0].severity == expected_severity

    @pytest.mark.asyncio
    async def test_alerts_sorted_by_severity_descending(self):
        req = CrowdAnalysisRequest(
            zones=[
                CrowdZoneReading(zone_id="gate_a", occupancy_percent=72),
                CrowdZoneReading(zone_id="gate_b", occupancy_percent=97),
                CrowdZoneReading(zone_id="gate_c", occupancy_percent=88),
            ]
        )
        result = await crowd.analyze_crowd(req)
        severities = [a.severity for a in result.alerts]
        assert severities == ["critical", "high", "medium"]

    @pytest.mark.asyncio
    async def test_all_clear_summary_when_no_alerts(self):
        req = CrowdAnalysisRequest(zones=[CrowdZoneReading(zone_id="gate_a", occupancy_percent=20)])
        result = await crowd.analyze_crowd(req)
        assert "safe capacity" in result.overall_summary.lower()

    @pytest.mark.asyncio
    async def test_rejects_out_of_range_occupancy(self):
        with pytest.raises(Exception):
            CrowdZoneReading(zone_id="gate_a", occupancy_percent=150)


class TestCrowdAPI:
    @pytest.mark.asyncio
    async def test_crowd_endpoint_happy_path(self, client):
        resp = await client.post(
            "/api/v1/crowd/analyze",
            json={"zones": [{"zone_id": "gate_a", "occupancy_percent": 96, "inflow_rate": 12}]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["alerts"][0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_crowd_endpoint_requires_at_least_one_zone(self, client):
        resp = await client.post("/api/v1/crowd/analyze", json={"zones": []})
        assert resp.status_code == 422
