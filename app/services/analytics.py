from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.entities import Device, MetricPoint


def user_metric_summary(db: Session, user_id: int, metric: str, start: datetime, end: datetime):
    query = select(MetricPoint).join(Device).where(Device.user_id == user_id, MetricPoint.metric == metric, MetricPoint.observed_at >= start, MetricPoint.observed_at <= end)
    points = db.scalars(query.order_by(MetricPoint.observed_at)).all()
    values = [point.value for point in points]
    return {"metric": metric, "count": len(values), "average": round(sum(values) / len(values), 2) if values else None, "minimum": min(values) if values else None, "maximum": max(values) if values else None, "latest_value": values[-1] if values else None}
