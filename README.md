# PulsePath — AI-Powered Smart Wearable Health Monitoring System

PulsePath is a portfolio-grade IoT health-monitoring platform that ingests wearable vitals, stores high-volume time-series measurements, calculates trends, generates configurable alerts, and provides a safe natural-language assistant over authenticated user data.

> **Safety boundary:** PulsePath is a monitoring/analytics prototype, not a medical diagnostic or emergency-care service. The assistant summarizes recorded measurements and should not be used to make medical decisions.

## ✨ Features

- Secure email/password authentication with JWT + Argon2
- User-owned wearable devices with per-device tokens
- Real-time measurement ingestion with idempotency protection
- Supported metrics: heart rate, SpO₂, temperature, steps
- PostgreSQL persistence for users, devices, alerts and metadata
- InfluxDB adapter for production-style time-series storage
- 24-hour dashboard summaries and historical time-series API
- Threshold-based anomaly/alert generation
- Alert acknowledgement workflow
- AI-style health assistant that queries authenticated analytics tools rather than raw databases
- Wearable simulator for live demos
- Responsive dashboard with live vitals, trends, devices, alerts and assistant UI
- Docker Compose stack for API + PostgreSQL + InfluxDB
- Automated CI and API tests

## 🏗️ Architecture

```text
Wearable / ESP32 / Simulator
          |
          | X-Device-Token
          v
     FastAPI REST API
          |
    +-----+----------------+
    |                      |
    v                      v
PostgreSQL             InfluxDB
accounts, devices      high-volume vitals
alerts, metadata
    |
    v
Analytics + Alert Rules
    |
    v
Authenticated AI Assistant
    |
    v
Responsive PulsePath Web Dashboard
```

The local demo keeps PostgreSQL as the relational source of truth while also writing measurements to InfluxDB when configured. If InfluxDB is unavailable, the demo remains usable through the relational adapter.

## 🚀 Run the full stack

Prerequisite: Docker Desktop.

```bash
git clone https://github.com/Mohdayush/wearable-health-platform.git
cd wearable-health-platform
docker compose up --build -d
```

Open:

- Dashboard: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- InfluxDB UI: `http://localhost:8086`

Check health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## 🎬 Demo in 3 minutes

Seed realistic wearable history:

```bash
docker compose exec api python scripts/seed_demo.py
```

The seeder prints a local demo account and device token. Use the demo account in the browser, then open **Dashboard**, **Live Vitals**, **Devices**, **Alerts**, and **AI Assistant**.

To simulate live wearable traffic, copy the device token printed by the seeder and run from the repository on your host:

```bash
pip install -r requirements.txt
python scripts/simulate_wearable.py --device-id 1 --token YOUR_DEVICE_TOKEN
```

The dashboard can then be refreshed to see new measurements and trend changes.

## 🔐 API examples

Register:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","name":"You","password":"StrongPass123!"}'
```

Ingest a wearable reading:

```bash
curl -X POST http://localhost:8000/api/v1/devices/1/measurements \
  -H 'Content-Type: application/json' \
  -H 'X-Device-Token: YOUR_DEVICE_TOKEN' \
  -d '{"metric":"heart_rate","value":72,"unit":"bpm","observed_at":"2026-09-08T12:00:00Z","idempotency_key":"reading-001"}'
```

## 🧪 Development

Without Docker, SQLite is used by default:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

## 📁 Project structure

```text
app/
  api/routes.py          REST endpoints
  core/config.py         environment configuration
  core/database.py       SQLAlchemy engine/session
  models/entities.py     users/devices/vitals/alerts
  schemas/contracts.py   validated API contracts
  services/auth.py       password hashing + JWT
  services/analytics.py  summaries + time-series queries
  services/timeseries.py optional InfluxDB writer
web/
  index.html             dashboard shell
  styles.css             responsive visual system
  app.js                 browser application
scripts/
  seed_demo.py           realistic demo data
  simulate_wearable.py   live IoT simulator
tests/
  test_health.py
  test_api.py
```

## 🛡️ Production considerations

For a real deployment, use managed PostgreSQL/InfluxDB, a strong secret from a secret manager, HTTPS, per-device token rotation/revocation, rate limiting, audit logs, encrypted backups, structured observability, and a proper migration system such as Alembic. Health data should be treated as sensitive information and access should be minimized.

The current assistant is deliberately constrained to backend-provided analytics; it does not execute arbitrary database queries or provide diagnoses.

## Resume

Suggested resume entry:

**PulsePath — AI-Powered Smart Wearable Health Monitoring System** | Python, FastAPI, PostgreSQL, InfluxDB, REST APIs, IoT, AI

- Built a secure wearable-health platform for real-time heart-rate, SpO₂, temperature and activity ingestion with JWT/device-token authentication and idempotent writes.
- Designed a time-series analytics pipeline with PostgreSQL + InfluxDB, threshold-based alerts, historical trends and a natural-language assistant over authenticated health summaries.
- Developed a responsive dashboard and IoT simulator, containerized the stack with Docker Compose, and added automated API/CI testing.
