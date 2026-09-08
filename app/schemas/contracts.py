from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

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
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class DeviceResponse(BaseModel):
    id: int
    name: str
    device_token: str
    active: bool
    class Config:
        from_attributes = True


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

    @field_validator("value")
    @classmethod
    def plausible_value(cls, value: float, info):
        metric = info.data.get("metric")
        if metric:
            low, high, _ = SUPPORTED_RANGES[metric]
            if not low <= value <= high:
                raise ValueError(f"Value must be between {low} and {high}")
        return value

class SummaryResponse(BaseModel):
    metric: str
    count: int
    average: float | None
    minimum: float | None
    maximum: float | None
    latest_value: float | None
