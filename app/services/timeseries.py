from datetime import datetime, timezone

from app.core.config import settings


def write_measurement(*, device_id: int, metric: str, value: float, unit: str, observed_at: datetime) -> bool:
    """Write to InfluxDB when configured; return False when the local adapter is used."""
    if not settings.influx_url or not settings.influx_token:
        return False
    try:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS
        timestamp = observed_at.replace(tzinfo=timezone.utc) if observed_at.tzinfo is None else observed_at
        with InfluxDBClient(url=settings.influx_url, token=settings.influx_token.get_secret_value(), org=settings.influx_org) as client:
            point = (Point("vitals").tag("device_id", str(device_id)).tag("metric", metric)
                     .field("value", float(value)).tag("unit", unit).time(timestamp))
            client.write_api(write_options=SYNCHRONOUS).write(bucket=settings.influx_bucket, org=settings.influx_org, record=point)
        return True
    except Exception:
        # The relational adapter remains the source of truth for the local demo.
        return False
