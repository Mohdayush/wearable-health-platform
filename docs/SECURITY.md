# PulsePath Security Notes

- Passwords are hashed with Argon2 through `pwdlib`; raw passwords are never stored.
- User APIs require JWT authentication and device ingestion requires a separate device token.
- Measurements are scoped to the owning user before being returned by analytics endpoints.
- Device tokens are generated with `secrets.token_urlsafe`.
- Measurement writes use idempotency keys to prevent accidental duplicate ingestion.
- Input ranges and future timestamps are validated at the API boundary.
- The assistant is constrained to backend summaries and includes a medical-safety disclaimer.
- Do not commit production secrets. Use environment variables or a secret manager.
- Use HTTPS, rate limiting, token rotation/revocation, audit logging and encrypted storage for production health data.
- The demo threshold rules are intentionally conservative examples; they are not clinical reference ranges.
