"""Create a safe local demo account, wearable and realistic vitals."""
from datetime import datetime, timedelta
import random

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Device, MetricPoint, User
from app.services.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    user = db.query(User).filter(User.email == "demo@pulsepath.local").first()
    if not user:
        user = User(email="demo@pulsepath.local", name="Demo User", password_hash=hash_password("PulsePathDemo123!"))
        db.add(user); db.flush()
    device = db.query(Device).filter(Device.user_id == user.id).first()
    if not device:
        import secrets
        device = Device(user_id=user.id, name="PulsePath Band", model="PP-Band v1", device_token=secrets.token_urlsafe(24))
        db.add(device); db.flush()
    if db.query(MetricPoint).filter(MetricPoint.device_id == device.id).count() < 20:
        start = datetime.utcnow() - timedelta(hours=12)
        random.seed(7)
        for i in range(72):
            t = start + timedelta(minutes=10*i)
            samples = [("heart_rate", max(55, min(105, 72 + random.gauss(0, 7))), "bpm"),
                       ("spo2", max(94, min(99, 97 + random.gauss(0, 0.8))), "percent"),
                       ("temperature", max(36.1, min(37.4, 36.7 + random.gauss(0, 0.15))), "celsius"),
                       ("steps", max(0, int(i * 90 + random.gauss(0, 35))), "count")]
            for metric, value, unit in samples:
                db.add(MetricPoint(device_id=device.id, metric=metric, value=round(value,2), unit=unit, observed_at=t, idempotency_key=f"seed-{device.id}-{metric}-{i}"))
    db.commit()
    print("Demo account: demo@pulsepath.local / PulsePathDemo123!")
    print(f"Device token: {device.device_token}")
finally:
    db.close()
