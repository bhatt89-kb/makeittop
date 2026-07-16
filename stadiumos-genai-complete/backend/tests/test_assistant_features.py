import pytest

from app.schemas import (
    AccessibilityRequest, ChatRequest, EmergencyRequest,
    SustainabilityRequest, TranslateRequest,
)
from app.services import accessibility, assistant


class TestEmergency:
    @pytest.mark.asyncio
    async def test_medical_keyword_forces_escalation(self):
        req = EmergencyRequest(situation="Someone is having chest pain near section 201")
        result = await assistant.handle_emergency(req)
        assert result.escalate_to_human is True
        assert result.hotline

    @pytest.mark.asyncio
    async def test_minor_situation_does_not_force_escalation(self):
        req = EmergencyRequest(situation="A fan lost their child's jacket")
        result = await assistant.handle_emergency(req)
        assert result.escalate_to_human is False

    @pytest.mark.asyncio
    async def test_emergency_endpoint_never_5xx(self, client):
        resp = await client.post("/api/v1/emergency", json={"situation": "fire near gate C"})
        assert resp.status_code == 200
        assert resp.json()["escalate_to_human"] is True


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_fallback_mode_returns_reply(self):
        req = ChatRequest(message="How do I get to Gate B?")
        result = await assistant.chat(req)
        assert result.reply
        assert result.source in {"genai", "fallback"}

    @pytest.mark.asyncio
    async def test_chat_suggests_navigation_action(self):
        req = ChatRequest(message="Where is Gate B?")
        result = await assistant.chat(req)
        assert "open_navigation" in result.suggested_actions

    @pytest.mark.asyncio
    async def test_chat_rejects_unsupported_language(self):
        with pytest.raises(Exception):
            ChatRequest(message="hello", language="xx")

    @pytest.mark.asyncio
    async def test_chat_endpoint_via_api(self, client):
        resp = await client.post("/api/v1/chat", json={"message": "Is it crowded near Gate A?"})
        assert resp.status_code == 200
        assert "open_crowd_dashboard" in resp.json()["suggested_actions"]


class TestTranslate:
    @pytest.mark.asyncio
    async def test_translate_fallback_mode(self):
        req = TranslateRequest(text="Welcome to the stadium", target_language="es")
        result = await assistant.translate(req)
        assert result.target_language == "es"
        assert result.translated_text


class TestSustainability:
    @pytest.mark.asyncio
    async def test_sustainability_returns_tips(self):
        req = SustainabilityRequest(context="I'm driving to the match")
        result = await assistant.get_sustainability_tips(req)
        assert len(result.tips) >= 1


class TestAccessibility:
    @pytest.mark.asyncio
    async def test_accessibility_guidance_returns_resources(self):
        req = AccessibilityRequest(query="Where can I get a wheelchair?", needs=["wheelchair"])
        result = await accessibility.get_accessibility_guidance(req)
        assert result.guidance
        assert len(result.resources) >= 1
