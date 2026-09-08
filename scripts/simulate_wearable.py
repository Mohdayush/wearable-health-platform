"""Send live-looking wearable readings to PulsePath.

Usage:
  python scripts/simulate_wearable.py --url http://localhost:8000 --device-id 1 --token TOKEN
"""
import argparse, random, time
from datetime import datetime, timezone
import uuid
import httpx

p=argparse.ArgumentParser();p.add_argument("--url",default="http://localhost:8000");p.add_argument("--device-id",type=int,required=True);p.add_argument("--token",required=True);p.add_argument("--interval",type=float,default=2);a=p.parse_args()
series=[("heart_rate",72,"bpm",6),("spo2",97,"percent",0.5),("temperature",36.7,"celsius",0.08),("steps",4500,"count",120)]
with httpx.Client(timeout=10) as client:
    while True:
        metric,base,unit,jitter=random.choice(series)
        value=base+random.gauss(0,jitter) if metric!="steps" else max(0,int(base+random.gauss(0,jitter)))
        payload={"metric":metric,"value":round(value,2),"unit":unit,"observed_at":datetime.now(timezone.utc).isoformat(),"idempotency_key":str(uuid.uuid4())}
        r=client.post(f"{a.url}/api/v1/devices/{a.device_id}/measurements",headers={"X-Device-Token":a.token},json=payload)
        print(r.status_code,r.json());time.sleep(a.interval)
