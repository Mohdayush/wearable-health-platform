# PulsePath — Wearable Health Monitoring Platform

An authenticated IoT health-data ingestion API. PostgreSQL holds accounts, devices, and access controls. The development adapter stores measurements locally; the production adapter will write high-volume time-series points to InfluxDB.

## Current data flow

`Wearable -> device-token authentication -> validation -> idempotent metric write -> summary API`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Important scope

This is a monitoring and analytics product, not a diagnostic or emergency-care service. The forthcoming AI agent will query authenticated backend tools, never databases directly.
