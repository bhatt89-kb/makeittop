"""
Tests for conversation memory and context tracking in assistant service.

This test suite validates the critical conversation memory features that
prevent repetitive chatbot responses and enable natural follow-up questions.
"""
import pytest
from app.schemas import ChatRequest
from app.services.assistant import (
    _get_conversation_context,
    _update_conversation_context,
    _detect_topic,
    _get_smart_fallback,
    _conversation_memory
)


class TestConversationMemory:
    """Test conversation memory tracking across messages."""
    
    def setup_method(self):
        """Clear conversation memory before each test."""
        _conversation_memory.clear()
    
    def test_new_conversation_initializes_context(self):
        """Test that new conversations start with empty context."""
        req = ChatRequest(message="Hello", language="en", role="fan")
        ctx = _get_conversation_context(req)
        
        assert ctx["message_count"] == 0
        assert ctx["last_topic"] is None
        assert ctx["last_gate"] is None
        assert ctx["last_transport_mode"] is None
        assert ctx["last_messages"] == []
    
    def test_conversation_context_persists_across_messages(self):
        """Test that context is stored and retrieved for same user."""
        req = ChatRequest(message="How do I get to Gate B?", language="en", role="fan")
        
        # First message
        _update_conversation_context(req, "Gate B is on the east side", topic="navigation", gate="Gate_B")
        
        # Second message from same user
        ctx = _get_conversation_context(req)
        assert ctx["message_count"] == 1
        assert ctx["last_topic"] == "navigation"
        assert ctx["last_gate"] == "Gate_B"
    
    def test_message_pairs_stored_in_history(self):
        """Test that message pairs are stored for conversation context."""
        req = ChatRequest(message="Where is Gate B?", language="en", role="fan")
        reply = "Gate B is on the east side of the stadium."
        
        _update_conversation_context(req, reply, topic="navigation")
        ctx = _get_conversation_context(req)
        
        assert len(ctx["last_messages"]) == 1
        assert ctx["last_messages"][0]["user"] == "Where is Gate B?"
        assert "Gate B is on the east side" in ctx["last_messages"][0]["assistant"]
    
    def test_conversation_history_limited_to_max(self):
        """Test that conversation history doesn't grow unbounded."""
        req = ChatRequest(message="Test message", language="en", role="fan")
        
        # Add 10 messages
        for i in range(10):
            _update_conversation_context(req, f"Reply {i}", topic="navigation")
        
        ctx = _get_conversation_context(req)
        # Should only keep last 5 (MAX_CONVERSATION_HISTORY)
        assert len(ctx["last_messages"]) == 5
        # Should have the most recent messages
        assert "Reply 9" in ctx["last_messages"][-1]["assistant"]
    
    def test_different_users_have_separate_contexts(self):
        """Test that different users don't share conversation context."""
        req_en = ChatRequest(message="Hello", language="en", role="fan")
        req_es = ChatRequest(message="Hola", language="es", role="fan")
        
        _update_conversation_context(req_en, "Reply EN", topic="navigation")
        _update_conversation_context(req_es, "Reply ES", topic="transport")
        
        ctx_en = _get_conversation_context(req_en)
        ctx_es = _get_conversation_context(req_es)
        
        assert ctx_en["last_topic"] == "navigation"
        assert ctx_es["last_topic"] == "transport"


class TestTopicDetection:
    """Test topic detection for conversation context tracking."""
    
    def test_detect_navigation_topic(self):
        """Test detection of navigation-related messages."""
        assert _detect_topic("How do I get to Gate B?") == "navigation"
        assert _detect_topic("Where is the nearest restroom?") == "navigation"
        assert _detect_topic("Directions to section 101") == "navigation"
        assert _detect_topic("Find the VIP lounge") == "navigation"
    
    def test_detect_transport_topic(self):
        """Test detection of transport-related messages."""
        assert _detect_topic("Tell me about parking options") == "transport"
        assert _detect_topic("Is there a shuttle service?") == "transport"
        assert _detect_topic("Which train should I take?") == "transport"
    
    def test_detect_accessibility_topic(self):
        """Test detection of accessibility-related messages."""
        assert _detect_topic("I need wheelchair access") == "accessibility"
        assert _detect_topic("Are there accessible restrooms?") == "accessibility"
        assert _detect_topic("Do you have hearing assistance?") == "accessibility"
        assert _detect_topic("Vision impaired services") == "accessibility"
    
    def test_detect_crowd_topic(self):
        """Test detection of crowd-related messages."""
        assert _detect_topic("How long is the wait?") == "crowd"
        assert _detect_topic("Are there long queues?") == "crowd"
        assert _detect_topic("What's the crowd like right now?") == "crowd"
    
    def test_no_topic_detected(self):
        """Test that unrelated messages return None."""
        assert _detect_topic("Hello") is None
        assert _detect_topic("Thanks") is None
        assert _detect_topic("Who won the match?") is None


class TestSmartFallback:
    """Test intelligent fallback responses that avoid repetitive templates."""
    
    def setup_method(self):
        """Clear conversation memory before each test."""
        _conversation_memory.clear()
    
    def test_fallback_with_zone_context_data(self):
        """Test fallback uses venue data when available."""
        req = ChatRequest(message="Where is gate b?", language="en", role="fan")
        ctx = _get_conversation_context(req)
        context_data = "ZONE INFO: Gate A - North Side, Gate B - East Side"
        
        result = _get_smart_fallback(req, ctx, context_data)
        
        assert "gate" in result.lower()
        assert "I can help with..." not in result  # Never generic template!
        assert any(word in result for word in ["A", "B", "C", "north", "east", "west"])
    
    def test_fallback_with_transport_context_data(self):
        """Test fallback references transport data when available."""
        req = ChatRequest(message="parking info", language="en", role="fan")
        ctx = _get_conversation_context(req)
        context_data = "TRANSPORT STATUS: North Lot 95% full, East Lot 60% full"
        
        result = _get_smart_fallback(req, ctx, context_data)
        
        assert "parking" in result.lower() or "lot" in result.lower()
        assert "I can help with..." not in result
    
    def test_fallback_with_crowd_context_data(self):
        """Test fallback mentions crowd data when available."""
        req = ChatRequest(message="is it busy?", language="en", role="fan")
        ctx = _get_conversation_context(req)
        context_data = "CROWD CONDITIONS: Gate A - moderate, North Concourse - busy"
        
        result = _get_smart_fallback(req, ctx, context_data)
        
        assert "crowd" in result.lower() or "congestion" in result.lower() or "busy" in result.lower()
        assert "I can help with..." not in result
    
    def test_fallback_uses_conversation_history(self):
        """Test fallback references previous messages when no venue data."""
        req = ChatRequest(message="What about that?", language="en", role="fan")
        
        # Simulate conversation history
        _update_conversation_context(req, "Gate B is on the east side", topic="navigation")
        ctx = _get_conversation_context(req)
        
        result = _get_smart_fallback(req, ctx, "")
        
        # Should reference previous context - either mentioning the exact previous message
        # or providing navigation-related guidance
        assert "clarify" in result.lower() or "navigation" in result.lower() or "directions" in result.lower()
        assert "I can help with..." not in result
    
    def test_fallback_uses_last_topic(self):
        """Test fallback provides topic-specific response."""
        req = ChatRequest(message="Tell me more", language="en", role="fan")
        ctx = {"last_topic": "transport", "message_count": 2, "last_messages": []}
        
        result = _get_smart_fallback(req, ctx, "")
        
        assert "transport" in result.lower() or "parking" in result.lower() or "shuttle" in result.lower()
        assert "I can help with..." not in result
    
    def test_fallback_never_generic_template(self):
        """Test that fallback NEVER uses 'I can help with...' template."""
        test_cases = [
            ("hello", "en", "fan", {}),
            ("hi there", "en", "fan", {"message_count": 0}),
            ("what can you do", "en", "staff", {"message_count": 1}),
        ]
        
        for message, language, role, extra_ctx in test_cases:
            req = ChatRequest(message=message, language=language, role=role)
            ctx = _get_conversation_context(req)
            ctx.update(extra_ctx)
            
            result = _get_smart_fallback(req, ctx, "")
            
            # The forbidden phrase
            assert "I can help with directions, accessibility" not in result
            assert "I can help with..." not in result
            # Should still be helpful but specific
            assert len(result) > 20  # Not empty


class TestMessageCountIncrement:
    """Test that message count properly increments."""
    
    def setup_method(self):
        """Clear conversation memory before each test."""
        _conversation_memory.clear()
    
    def test_message_count_starts_at_zero(self):
        """Test new conversations start with count 0."""
        req = ChatRequest(message="Hello", language="en", role="fan")
        ctx = _get_conversation_context(req)
        assert ctx["message_count"] == 0
    
    def test_message_count_increments(self):
        """Test that message count increases with each update."""
        req = ChatRequest(message="Test", language="en", role="fan")
        
        _update_conversation_context(req, "Reply 1")
        assert _get_conversation_context(req)["message_count"] == 1
        
        _update_conversation_context(req, "Reply 2")
        assert _get_conversation_context(req)["message_count"] == 2
        
        _update_conversation_context(req, "Reply 3")
        assert _get_conversation_context(req)["message_count"] == 3


class TestContextDataExtraction:
    """Test that context data is properly extracted and formatted."""
    
    # Note: _extract_context_data is not directly exported, so we test through
    # the chat endpoint behavior. These tests would go in test_assistant_features.py
    pass
