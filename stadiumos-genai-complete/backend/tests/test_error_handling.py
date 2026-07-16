"""
Tests for error handling utilities and service resilience.

This test suite validates the centralized error handling that improves
code quality and provides graceful degradation when services fail.
"""
import pytest
from app.utils.error_handler import (
    ServiceError,
    AIServiceUnavailableError,
    DataValidationError,
    safe_service_call,
    log_and_continue,
    handle_optional_service
)


class TestServiceErrors:
    """Test custom exception hierarchy."""
    
    def test_service_error_is_base_exception(self):
        """Test that ServiceError is the base for all service errors."""
        assert issubclass(AIServiceUnavailableError, ServiceError)
        assert issubclass(DataValidationError, ServiceError)
    
    def test_service_error_message(self):
        """Test that service errors store message and service name."""
        error = ServiceError("Test failure", "test_service")
        assert str(error) == "[test_service] Test failure"
        assert error.service_name == "test_service"
    
    def test_ai_service_error_is_recoverable(self):
        """Test that AI service errors are marked as recoverable."""
        error = AIServiceUnavailableError()
        assert error.recoverable is True
    
    def test_data_validation_error_not_recoverable(self):
        """Test that validation errors are marked as not recoverable."""
        error = DataValidationError("Invalid input")
        assert error.recoverable is False


class TestSafeServiceCall:
    """Test safe_service_call decorator for graceful error handling."""
    
    @pytest.mark.asyncio
    async def test_successful_call_returns_result(self):
        """Test that successful calls return normally."""
        @safe_service_call(fallback_response={"error": True}, service_name="test")
        async def successful_function():
            return {"status": "success", "data": 42}
        
        result = await successful_function()
        assert result == {"status": "success", "data": 42}
    
    @pytest.mark.asyncio
    async def test_service_error_returns_fallback(self):
        """Test that exceptions return fallback response."""
        @safe_service_call(fallback_response={"error": "fallback"}, service_name="test")
        async def failing_function():
            raise ValueError("Something went wrong")
        
        result = await failing_function()
        assert result == {"error": "fallback"}
    
    @pytest.mark.asyncio
    async def test_no_fallback_raises_exception(self):
        """Test that without fallback, exceptions propagate."""
        @safe_service_call(fallback_response=None, service_name="test")
        async def failing_function():
            raise ValueError("Should propagate")
        
        with pytest.raises(ValueError, match="Should propagate"):
            await failing_function()


class TestLogAndContinue:
    """Test log_and_continue helper for non-critical errors."""
    
    def test_logs_error_without_raising(self, caplog):
        """Test that errors are logged but not raised."""
        import logging
        caplog.set_level(logging.WARNING)
        
        error = RuntimeError("Test error")
        log_and_continue(error, "Test operation", level="warning")
        
        # Should have logged
        assert len(caplog.records) > 0
        assert "Test operation" in caplog.text
        assert "RuntimeError" in caplog.text
    
    def test_custom_log_level(self, caplog):
        """Test that custom log levels are respected."""
        import logging
        caplog.set_level(logging.ERROR)
        
        error = Exception("Critical")
        log_and_continue(error, "Critical operation", level="error")
        
        assert len(caplog.records) > 0


class TestHandleOptionalService:
    """Test handle_optional_service for non-critical operations."""
    
    def test_successful_call_returns_result(self):
        """Test that successful calls work normally."""
        def add_numbers(a, b):
            return a + b
        
        result = handle_optional_service(add_numbers, 2, 3, service_name="math")
        assert result == 5
    
    def test_failed_call_returns_default(self):
        """Test that failures return default value."""
        def failing_func():
            raise RuntimeError("Always fails")
        
        result = handle_optional_service(
            failing_func,
            default="default_value",
            service_name="test"
        )
        assert result == "default_value"
    
    def test_kwargs_passed_correctly(self):
        """Test that keyword arguments are passed through."""
        def func_with_kwargs(a, b=10):
            return a * b
        
        result = handle_optional_service(func_with_kwargs, 5, b=3, service_name="test")
        assert result == 15


class TestRealWorldScenarios:
    """Test error handling in realistic failure scenarios."""
    
    @pytest.mark.asyncio
    async def test_ai_service_timeout_fallback(self):
        """Test graceful handling of AI service timeout."""
        @safe_service_call(
            fallback_response={"reply": "Rule-based fallback"},
            service_name="ai_chat"
        )
        async def ai_with_timeout():
            raise TimeoutError("AI service timeout")
        
        result = await ai_with_timeout()
        assert result == {"reply": "Rule-based fallback"}
    
    @pytest.mark.asyncio
    async def test_partial_service_degradation(self):
        """Test that one service failure doesn't break the whole system."""
        results = {}
        
        # Service 1: succeeds
        @safe_service_call(fallback_response=None, service_name="service1")
        async def service1():
            return {"data": "from service 1"}
        
        # Service 2: fails but has fallback
        @safe_service_call(fallback_response={"data": "fallback"}, service_name="service2")
        async def service2():
            raise ConnectionError("Service 2 down")
        
        results["service1"] = await service1()
        results["service2"] = await service2()
        
        # Both should return data, one real, one fallback
        assert results["service1"]["data"] == "from service 1"
        assert results["service2"]["data"] == "fallback"


class TestErrorLogging:
    """Test that errors are properly logged with context."""
    
    @pytest.mark.asyncio
    async def test_error_logged_with_context(self, caplog):
        """Test that errors include contextual information in logs."""
        import logging
        caplog.set_level(logging.ERROR)
        
        @safe_service_call(fallback_response=None, service_name="test_service")
        async def failing_with_context():
            raise ValueError("Test error with context")
        
        try:
            await failing_with_context()
        except ValueError:
            pass  # Expected
        
        # Check that error was logged with service name
        assert any("test_service" in record.message for record in caplog.records)


class TestPerformanceUnderError:
    """Test that error handling doesn't significantly impact performance."""
    
    @pytest.mark.asyncio
    async def test_decorator_overhead_minimal(self):
        """Test that decorators don't add significant overhead."""
        import time
        
        async def without_decorator():
            return sum(range(1000))
        
        @safe_service_call(fallback_response=0, service_name="test")
        async def with_decorator():
            return sum(range(1000))
        
        # Measure without decorator
        start = time.time()
        for _ in range(100):
            await without_decorator()
        baseline = time.time() - start
        
        # Measure with decorator
        start = time.time()
        for _ in range(100):
            await with_decorator()
        decorated = time.time() - start
        
        # Decorator shouldn't add more than 100% overhead (2x slower)
        # This is a generous bound since timing can vary on different systems
        assert decorated < baseline * 2.0

