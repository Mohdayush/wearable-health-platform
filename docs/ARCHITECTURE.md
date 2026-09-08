# PulsePath Architecture

## Request path

1. A wearable/ESP32 sends a measurement with `X-Device-Token`.
2. FastAPI authenticates the device and validates the metric/value/timestamp.
3. The relational adapter stores the measurement with an idempotency key.
4. The optional InfluxDB adapter writes the same point for time-series workloads.
5. Alert rules evaluate the reading and persist a user-owned alert when it crosses a configured demo range.
6. Authenticated dashboard endpoints aggregate data for the current user only.
7. The assistant endpoint consumes those backend summaries and returns a constrained natural-language explanation.

## Storage split

PostgreSQL is appropriate for users, devices, credentials, configuration and alerts. InfluxDB is appropriate for high-cardinality time-series queries and retention policies. The local fallback makes the project easy to run without external infrastructure.

## IoT integration

The repository's `scripts/simulate_wearable.py` behaves like an ESP32/device client. A real device can call the same REST ingestion endpoint over HTTPS. Production devices should support token rotation, secure provisioning and TLS certificate validation.

## Scaling path

For higher throughput, place an API load balancer in front of stateless FastAPI instances, buffer ingestion through a durable queue, batch Influx writes, and run analytics/alert evaluation asynchronously. Keep device authentication and authorization at the API boundary.
