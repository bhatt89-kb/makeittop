"""
Pydantic schemas shared across routers.

Every inbound field has an explicit max length / allowed-value constraint.
This is a security control as much as a data-quality one: it stops
oversized or malformed payloads reaching the GenAI layer (prompt-injection
surface reduction, denial-of-service mitigation) — see docs/SECURITY.md.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

SUPPORTED_LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "pt": "Portuguese",
    "de": "German", "ar": "Arabic", "hi": "Hindi", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean",
}


class UserRole(str, Enum):
    fan = "fan"
    volunteer = "volunteer"
    staff = "staff"
    organizer = "organizer"


def _no_control_chars(v: str) -> str:
    if any(ord(ch) < 9 for ch in v):
        raise ValueError("input contains disallowed control characters")
    return v.strip()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en")
    role: UserRole = UserRole.fan
    session_id: Optional[str] = Field(default=None, max_length=100)

    _clean_message = field_validator("message")(lambda cls, v: _no_control_chars(v))

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported language code '{v}'")
        return v


class ChatResponse(BaseModel):
    reply: str
    language: str
    suggested_actions: List[str] = Field(default_factory=list)
    source: str  # "genai" | "fallback"


class NavigationRequest(BaseModel):
    origin: str = Field(..., min_length=1, max_length=80)
    destination: str = Field(..., min_length=1, max_length=80)
    accessibility_needs: List[str] = Field(default_factory=list, max_length=6)
    language: str = Field(default="en")
    avoid_crowds: bool = True

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported language code '{v}'")
        return v


class NavigationStep(BaseModel):
    instruction: str
    zone: str
    estimated_minutes: float
    crowd_level: str


class NavigationResponse(BaseModel):
    steps: List[NavigationStep]
    total_minutes: float
    narrative: str
    accessible: bool
    source: str


class CrowdZoneReading(BaseModel):
    zone_id: str = Field(..., max_length=40)
    occupancy_percent: float = Field(..., ge=0, le=100)
    inflow_rate: float = Field(default=0, ge=-1000, le=1000)


class CrowdAnalysisRequest(BaseModel):
    zones: List[CrowdZoneReading] = Field(..., min_length=1, max_length=50)
    event_phase: str = Field(default="pre-match", max_length=30)


class CrowdAlert(BaseModel):
    zone_id: str
    severity: str  # low | medium | high | critical
    message: str
    recommended_action: str


class CrowdAnalysisResponse(BaseModel):
    alerts: List[CrowdAlert]
    overall_summary: str
    source: str


class AccessibilityRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    needs: List[str] = Field(default_factory=list, max_length=8)
    language: str = Field(default="en")


class AccessibilityResponse(BaseModel):
    guidance: str
    resources: List[str]
    source: str


class SustainabilityRequest(BaseModel):
    context: str = Field(..., min_length=1, max_length=300)


class SustainabilityResponse(BaseModel):
    tips: List[str]
    estimated_co2_savings_kg: Optional[float] = None
    source: str


class EmergencyRequest(BaseModel):
    situation: str = Field(..., min_length=1, max_length=300)
    zone_id: Optional[str] = Field(default=None, max_length=40)
    language: str = Field(default="en")


class EmergencyResponse(BaseModel):
    instructions: List[str]
    escalate_to_human: bool
    hotline: str
    source: str


class TransportRequest(BaseModel):
    mode: Optional[str] = Field(default=None, max_length=20)  # "car" | "shuttle" | "transit" | None (any)
    party_size: int = Field(default=1, ge=1, le=20)
    accessibility_needs: List[str] = Field(default_factory=list, max_length=6)
    minutes_to_kickoff: Optional[int] = Field(default=None, ge=0, le=600)
    language: str = Field(default="en")

    @field_validator("mode")
    @classmethod
    def check_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"car", "shuttle", "transit"}:
            raise ValueError("mode must be one of 'car', 'shuttle', 'transit'")
        return v

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported language code '{v}'")
        return v


class TransportOption(BaseModel):
    option_id: str
    mode: str  # "car" | "shuttle" | "transit"
    name: str
    detail: str
    eta_minutes: float
    accessible: bool
    status: str  # "on_time" | "delayed" | "suspended" | "full" | "near_full" | "available"


class TransportResponse(BaseModel):
    options: List[TransportOption]
    recommended_option_id: Optional[str] = None
    summary: str
    source: str


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    target_language: str

    @field_validator("target_language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported language code '{v}'")
        return v


class TranslateResponse(BaseModel):
    translated_text: str
    target_language: str
    source: str
