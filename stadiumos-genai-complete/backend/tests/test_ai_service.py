import pytest

from app.services import ai_service


class TestAIServiceFallbackBehavior:
    @pytest.mark.asyncio
    async def test_generate_returns_none_without_api_key(self):
        # conftest forces GEMINI_API_KEY="" so the client never initializes.
        ai_service._client = None
        ai_service._client_init_failed = False
        result = await ai_service.generate("system", "user")
        assert result is None

    def test_is_ai_available_false_without_key(self):
        ai_service._client = None
        ai_service._client_init_failed = False
        assert ai_service.is_ai_available() is False

    @pytest.mark.asyncio
    async def test_generate_never_raises_on_client_error(self, monkeypatch):
        """Even if the SDK is mocked to explode, generate() must degrade to None,
        never propagate an exception (that's the contract every router relies on)."""

        class ExplodingModel:
            async def generate_content_async(self, *args, **kwargs):
                raise RuntimeError("simulated network failure")

        class ExplodingClient:
            def GenerativeModel(self, *args, **kwargs):
                return ExplodingModel()

        monkeypatch.setattr(ai_service, "_get_client", lambda: ExplodingClient())
        # keep retries fast for the test
        ai_service.settings.ai_max_retries = 0
        result = await ai_service.generate("system", "user")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_returns_text_on_success(self, monkeypatch):
        class Response:
            text = "Hello fan!"

        class WorkingModel:
            async def generate_content_async(self, *args, **kwargs):
                return Response()

        class WorkingClient:
            def GenerativeModel(self, *args, **kwargs):
                return WorkingModel()

        monkeypatch.setattr(ai_service, "_get_client", lambda: WorkingClient())
        result = await ai_service.generate("system", "user")
        assert result == "Hello fan!"
