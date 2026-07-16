import pytest

from app.routers import api as api_router


class TestRouterErrorHandling:
    """Every router wraps its service call in try/except so a bug in one
    feature can never crash the whole API with a raw stack trace. These
    tests simulate the service layer throwing and assert the router
    converts it into a clean, generic 500 (or, for /emergency, a safe
    fallback response — safety-critical paths must never go dark)."""

    @pytest.mark.asyncio
    async def test_chat_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.assistant, "chat", boom)
        resp = await client.post("/api/v1/chat", json={"message": "hello"})
        assert resp.status_code == 500
        assert "unexpected" not in resp.json()["detail"].lower() or "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_navigate_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.navigation, "get_navigation", boom)
        resp = await client.post("/api/v1/navigate", json={"origin": "Gate A", "destination": "Gate B"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_crowd_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.crowd, "analyze_crowd", boom)
        resp = await client.post(
            "/api/v1/crowd/analyze", json={"zones": [{"zone_id": "gate_a", "occupancy_percent": 10}]}
        )
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_accessibility_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.accessibility, "get_accessibility_guidance", boom)
        resp = await client.post("/api/v1/accessibility", json={"query": "help"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_translate_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.assistant, "translate", boom)
        resp = await client.post("/api/v1/translate", json={"text": "hi", "target_language": "es"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_sustainability_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.assistant, "get_sustainability_tips", boom)
        resp = await client.post("/api/v1/sustainability", json={"context": "driving"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_transport_service_exception_returns_clean_500(self, client, monkeypatch):
        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.transport, "get_transport_options", boom)
        resp = await client.post("/api/v1/transport", json={})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_emergency_service_exception_still_returns_safe_guidance(self, client, monkeypatch):
        """This is the one endpoint that must NEVER surface a bare 500:
        a crashing emergency endpoint during a real incident is unacceptable,
        so the router catches everything and returns the human-hotline fallback."""

        async def boom(_):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(api_router.assistant, "handle_emergency", boom)
        resp = await client.post("/api/v1/emergency", json={"situation": "fire"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["escalate_to_human"] is True
        assert "control room" in body["hotline"].lower()
