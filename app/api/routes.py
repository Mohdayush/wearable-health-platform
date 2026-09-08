import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Device, MetricPoint, User
from app.schemas.contracts import DeviceCreate, DeviceResponse, LoginRequest, MeasurementCreate, RegisterRequest, SummaryResponse, TokenResponse
from app.services.analytics import user_metric_summary
from app.services.auth import create_access_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(email=payload.email, name=payload.name, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=create_access_token(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user))


@router.post("/devices", response_model=DeviceResponse, status_code=201)
def register_device(payload: DeviceCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    device = Device(user_id=user.id, name=payload.name, device_token=secrets.token_urlsafe(32))
    db.add(device); db.commit(); db.refresh(device)
    return device


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Device).where(Device.user_id == user.id)).all()


@router.post("/devices/{device_id}/measurements", status_code=202)
def ingest_measurement(device_id: int, payload: MeasurementCreate, x_device_token: str = Header(), db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device or not device.active or not secrets.compare_digest(device.device_token, x_device_token):
        raise HTTPException(status_code=401, detail="Invalid device credentials")
    if payload.observed_at > datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=5):
        raise HTTPException(status_code=422, detail="Future timestamps are not accepted")
    point = MetricPoint(device_id=device.id, **payload.model_dump())
    device.last_seen_at = datetime.utcnow()
    try:
        db.add(point); db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate_ignored"}
    return {"status": "accepted"}


@router.get("/health/summary", response_model=SummaryResponse)
def health_summary(metric: str, hours: int = 24, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not 1 <= hours <= 24 * 30:
        raise HTTPException(status_code=422, detail="hours must be between 1 and 720")
    end = datetime.utcnow(); start = end - timedelta(hours=hours)
    return user_metric_summary(db, user.id, metric, start, end)
