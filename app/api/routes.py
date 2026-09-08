import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Alert, AlertPreference, Device, MetricPoint, User
from app.schemas.contracts import (
    AlertPreferenceRequest, AlertResponse, AssistantRequest, AssistantResponse,
    DeviceCreate, DeviceResponse, LoginRequest, MeasurementCreate, PointResponse,
    RegisterRequest, SummaryResponse, TokenResponse, UserResponse,
)
from app.services.analytics import dashboard_snapshot, user_metric_points, user_metric_summary
from app.services.auth import create_access_token, current_user, hash_password, verify_password
from app.services.timeseries import write_measurement

router = APIRouter(prefix="/api/v1")


def _default_alert(metric: str, value: float):
    defaults = {"heart_rate": (45, 120), "spo2": (92, 100), "temperature": (35, 39), "steps": (0, None)}
    low, high = defaults[metric]
    if low is not None and value < low:
        return "warning", f"{metric.replace('_', ' ').title()} is below the configured demo range ({value:g})."
    if high is not None and value > high:
        return "warning", f"{metric.replace('_', ' ').title()} is above the configured demo range ({value:g})."
    return None


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(email=payload.email.lower(), name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/users/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return user


@router.post("/devices", response_model=DeviceResponse, status_code=201)
def register_device(payload: DeviceCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    device = Device(user_id=user.id, name=payload.name.strip(), model=payload.model.strip())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Device).where(Device.user_id == user.id).order_by(Device.created_at.desc())).all()


@router.patch("/devices/{device_id}/status")
def set_device_status(device_id: int, active: bool, db: Session = Depends(get_db), user: User = Depends(current_user)):
    device = db.scalar(select(Device).where(Device.id == device_id, Device.user_id == user.id))
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.active = active
    db.commit()
    return {"status": "updated", "active": active}


@router.post("/devices/{device_id}/measurements", status_code=202)
def ingest_measurement(device_id: int, payload: MeasurementCreate, x_device_token: str = Header(), db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device or not device.active or not secrets.compare_digest(device.device_token, x_device_token):
        raise HTTPException(status_code=401, detail="Invalid device credentials")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    observed_at = payload.observed_at.replace(tzinfo=None)
    if observed_at > now + timedelta(minutes=5):
        raise HTTPException(status_code=422, detail="Future timestamps are not accepted")
    point = MetricPoint(device_id=device.id, metric=payload.metric, value=payload.value, unit=payload.unit, observed_at=observed_at, idempotency_key=payload.idempotency_key)
    device.last_seen_at = datetime.utcnow()
    try:
        db.add(point)
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate_ignored"}
    write_measurement(device_id=device.id, metric=point.metric, value=point.value, unit=point.unit, observed_at=point.observed_at)
    alert = _default_alert(point.metric, point.value)
    if alert:
        severity, message = alert
        db.add(Alert(user_id=device.user_id, device_id=device.id, metric=point.metric, value=point.value, severity=severity, message=message))
        db.commit()
    return {"status": "accepted", "metric": point.metric, "value": point.value}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    devices = db.scalars(select(Device).where(Device.user_id == user.id).order_by(Device.created_at.desc())).all()
    alerts = db.scalars(select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()).limit(8)).all()
    return {"user": UserResponse.model_validate(user), "metrics": dashboard_snapshot(db, user.id),
            "devices": [DeviceResponse.model_validate(d) for d in devices],
            "alerts": [AlertResponse.model_validate(a) for a in alerts]}


@router.get("/health/summary", response_model=SummaryResponse)
def health_summary(metric: str = Query(...), hours: int = 24, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not 1 <= hours <= 24 * 30:
        raise HTTPException(status_code=422, detail="hours must be between 1 and 720")
    end = datetime.utcnow()
    return user_metric_summary(db, user.id, metric, end - timedelta(hours=hours), end)


@router.get("/health/timeseries/{metric}", response_model=list[PointResponse])
def health_timeseries(metric: str, hours: int = 24, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not 1 <= hours <= 24 * 30:
        raise HTTPException(status_code=422, detail="hours must be between 1 and 720")
    return user_metric_points(db, user.id, metric, hours)


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()).limit(50)).all()


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    alert = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"status": "acknowledged"}


@router.put("/alerts/preferences")
def set_alert_preference(payload: AlertPreferenceRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if payload.lower_threshold is not None and payload.upper_threshold is not None and payload.lower_threshold >= payload.upper_threshold:
        raise HTTPException(status_code=422, detail="lower_threshold must be below upper_threshold")
    pref = db.scalar(select(AlertPreference).where(AlertPreference.user_id == user.id, AlertPreference.metric == payload.metric))
    if pref:
        pref.lower_threshold = payload.lower_threshold
        pref.upper_threshold = payload.upper_threshold
    else:
        pref = AlertPreference(user_id=user.id, **payload.model_dump())
        db.add(pref)
    db.commit()
    return {"status": "saved", "metric": payload.metric}


@router.post("/assistant/chat", response_model=AssistantResponse)
def assistant_chat(payload: AssistantRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    text = payload.message.lower()
    metrics = dashboard_snapshot(db, user.id)
    if "heart" in text or "pulse" in text:
        item = metrics["heart_rate"]
        answer = f"Your last 24h heart-rate data contains {item['count']} readings. The latest value is {item['latest_value']} {item['unit']} and the average is {item['average']} {item['unit']}."
    elif "oxygen" in text or "spo2" in text:
        item = metrics["spo2"]
        answer = f"Your last 24h SpO₂ data contains {item['count']} readings. The latest value is {item['latest_value']}% and the average is {item['average']}%."
    elif "temperature" in text:
        item = metrics["temperature"]
        answer = f"Your last 24h temperature data contains {item['count']} readings. The latest value is {item['latest_value']}°C and the average is {item['average']}°C."
    elif "step" in text or "activity" in text:
        item = metrics["steps"]
        answer = f"Your last 24h activity data contains {item['count']} readings. The latest step count reading is {item['latest_value']}."
    else:
        answer = "I can summarize your recent heart rate, SpO₂, temperature, and activity data. Ask me about one of those metrics."
    return AssistantResponse(answer=answer, disclaimer="PulsePath is a monitoring and analytics tool, not a diagnostic or emergency-care service. Seek professional care for concerning symptoms.")
