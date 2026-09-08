from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.entities import Device, MetricPoint
from app.schemas.contracts import SUPPORTED_RANGES


def _points(db: Session, user_id: int, metric: str, start: datetime, end: datetime):
    query = (
        select(MetricPoint)
        .join(Device, Device.id == MetricPoint.device_id)
        .where(Device.user_id == user_id, MetricPoint.metric == metric,
               MetricPoint.observed_at >= start, MetricPoint.observed_at <= end)
        .order_by(MetricPoint.observed_at)
    )
    return db.scalars(query).all()


def user_metric_summary(db: Session, user_id: int, metric: str, start: datetime, end: datetime):
    points = _points(db, user_id, metric, start, end)
    values = [point.value for point in points]
    unit = points[-1].unit if points else SUPPORTED_RANGES.get(metric, (0, 0, ""))[2]
    return {
        "metric": metric, "unit": unit, "count": len(values),
        "average": round(sum(values) / len(values), 2) if values else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
        "latest_value": values[-1] if values else None,
        "latest_at": points[-1].observed_at if points else None,
    }


def user_metric_points(db: Session, user_id: int, metric: str, hours: int = 24):
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    return _points(db, user_id, metric, start, end)


def dashboard_snapshot(db: Session, user_id: int):
    return {metric: user_metric_summary(db, user_id, metric, datetime.utcnow() - timedelta(hours=24), datetime.utcnow())
            for metric in ("heart_rate", "spo2", "temperature", "steps")}
