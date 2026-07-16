from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas import (
    AccessibilityRequest, AccessibilityResponse,
    ChatRequest, ChatResponse,
    CrowdAnalysisRequest, CrowdAnalysisResponse,
    EmergencyRequest, EmergencyResponse,
    NavigationRequest, NavigationResponse,
    SustainabilityRequest, SustainabilityResponse,
    TranslateRequest, TranslateResponse,
    TransportRequest, TransportResponse,
)
from app.security import enforce_rate_limit
from app.services import accessibility, assistant, crowd, navigation, transport
from app.services.ai_service import is_ai_available

logger = logging.getLogger("stadiumos.api")
router = APIRouter(prefix="/api/v1", tags=["stadiumos"])


def _rate_limited(request: Request) -> None:
    enforce_rate_limit(request)


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(_rate_limited)])
async def chat_endpoint(payload: ChatRequest):
    try:
        return await assistant.chat(payload)
    except Exception:
        logger.exception("chat_endpoint failed")
        raise HTTPException(status_code=500, detail="The assistant is temporarily unavailable. Please try again.")


@router.post("/navigate", response_model=NavigationResponse, dependencies=[Depends(_rate_limited)])
async def navigate_endpoint(payload: NavigationRequest):
    try:
        return await navigation.get_navigation(payload)
    except Exception:
        logger.exception("navigate_endpoint failed")
        raise HTTPException(status_code=500, detail="Navigation service is temporarily unavailable.")


@router.post("/crowd/analyze", response_model=CrowdAnalysisResponse, dependencies=[Depends(_rate_limited)])
async def crowd_endpoint(payload: CrowdAnalysisRequest):
    try:
        return await crowd.analyze_crowd(payload)
    except Exception:
        logger.exception("crowd_endpoint failed")
        raise HTTPException(status_code=500, detail="Crowd analysis service is temporarily unavailable.")


@router.post("/accessibility", response_model=AccessibilityResponse, dependencies=[Depends(_rate_limited)])
async def accessibility_endpoint(payload: AccessibilityRequest):
    try:
        return await accessibility.get_accessibility_guidance(payload)
    except Exception:
        logger.exception("accessibility_endpoint failed")
        raise HTTPException(status_code=500, detail="Accessibility service is temporarily unavailable.")


@router.post("/translate", response_model=TranslateResponse, dependencies=[Depends(_rate_limited)])
async def translate_endpoint(payload: TranslateRequest):
    try:
        return await assistant.translate(payload)
    except Exception:
        logger.exception("translate_endpoint failed")
        raise HTTPException(status_code=500, detail="Translation service is temporarily unavailable.")


@router.post("/sustainability", response_model=SustainabilityResponse, dependencies=[Depends(_rate_limited)])
async def sustainability_endpoint(payload: SustainabilityRequest):
    try:
        return await assistant.get_sustainability_tips(payload)
    except Exception:
        logger.exception("sustainability_endpoint failed")
        raise HTTPException(status_code=500, detail="Sustainability service is temporarily unavailable.")


@router.post("/emergency", response_model=EmergencyResponse, dependencies=[Depends(_rate_limited)])
async def emergency_endpoint(payload: EmergencyRequest):
    try:
        return await assistant.handle_emergency(payload)
    except Exception:
        logger.exception("emergency_endpoint failed")
        # Emergency guidance must NEVER 500 into silence — always give the human-hotline fallback.
        return EmergencyResponse(
            instructions=["Contact the nearest steward or the Stadium Emergency Control Room immediately."],
            escalate_to_human=True,
            hotline="Stadium Emergency Control Room: internal ext. 4444 / radio channel 1",
            source="fallback",
        )


@router.post("/transport", response_model=TransportResponse, dependencies=[Depends(_rate_limited)])
async def transport_endpoint(payload: TransportRequest):
    try:
        return await transport.get_transport_options(payload)
    except Exception:
        logger.exception("transport_endpoint failed")
        raise HTTPException(status_code=500, detail="Transport service is temporarily unavailable.")


@router.get("/health")
async def health():
    return {"status": "ok", "genai_available": is_ai_available()}
