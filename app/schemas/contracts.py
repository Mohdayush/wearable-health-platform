from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

SUPPORTED_RANGES = {
    "heart_rate": (20, 250, "bpm"),
    "spo2": (50, 100, "percent"),
    "temperature": (25, 45, "celsius"),
    "steps": (0, 100000, "count"),
}


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str
    created_at: datetime


class DeviceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    model: str = Field(default="PulsePath Band", min_length=2, max_length=80)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    model: str
    device_token: str
    battery_percent: int
    active: bool
    last_seen_at: datetime | None


class MeasurementCreate(BaseModel):
    metric: str
    value: float
    unit: str
    observed_at: datetime
    idempotency_key: str = Field(min_length=8, max_length=100)

    @field_validator("metric")
    @classmethod
    def supported_metric(cls, value: str):
        if value not in SUPPORTED_RANGES:
            raise ValueError("Unsupported metric")
        return value

    @field_validator("unit")
    @classmethod
    def non_empty_unit(cls, value: str):
        if not value.strip():
            raise ValueError("Unit is required")
        return value.strip()[:20]

    @field_validator("value")
    @classmethod
    def finite_value(cls, value: float):
        if value != value or abs(value) == float("inf"):
            raise ValueError("Value must be finite")
        return value


class SummaryResponse(BaseModel):
    metric: str
    unit: str | None = None
    count: int
    average: float | None
    minimum: float | None
    maximum: float | None
    latest_value: float | None
    latest_at: datetime | None = None


class PointResponse(BaseModel):
    metric: str
    value: float
    unit: str
    observed_at: datetime


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    metric: str
    value: float
    severity: str
    message: str
    created_at: datetime
    acknowledged: bool


class AlertPreferenceRequest(BaseModel):
    metric: str
    lower_threshold: float | None = None
    upper_threshold: float | None = None

    @field_validator("metric")
    @classmethod
    def metric_known(cls, value: str):
        if value not in SUPPORTED_RANGES:
            raise ValueError("Unsupported metric")
        return value

    @field_validator("upper_threshold")
    @classmethod
    def positive_upper(cls, value):
        return value


class AssistantRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


class AssistantResponse(BaseModel):
    answer: str
    disclaimer: str
