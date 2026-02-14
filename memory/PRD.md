# AI Crypto Trading Platform - PRD

## Problem Statement
Full-stack AI crypto trading platform with Kraken integration, featuring comprehensive security hardening with dual authentication (CSRF + API key).

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Pydantic
- **Frontend**: React + Vite + Axios
- **Auth**: Dual-mode — session/CSRF for browsers, API key for programmatic access
- **Security**: Defense-in-depth middleware stack (CSRF, rate limiting, input validation, audit logging, error handling)

## Core Security Features (Implemented)
- [x] Global exception handler (prevents internal error leakage)
- [x] CORS policy hardening (restricted origins)
- [x] CSRF double-submit cookie pattern middleware
- [x] Session-based authentication with MongoDB TTL
- [x] API key management (create, list, validate, revoke, delete)
- [x] Rate limiting middleware
- [x] Input validation / NoSQL injection prevention middleware
- [x] Audit logging middleware
- [x] Security headers middleware
- [x] Frontend auto-session + CSRF interceptors (api.jsx)
- [x] Bulk error handling fix (200+ instances of detail=str(e) replaced)

## Key Endpoints
- `GET /api/auth/csrf-token` — Bootstrap CSRF cookie
- `POST /api/auth/session` — Create user session
- `POST /api/auth/session/validate` — Validate session token
- `POST /api/auth/session/revoke` — Log out / revoke session
- `POST /api/api-keys/create` — Create API key
- `GET /api/api-keys/list` — List user's keys
- `GET /api/api-keys/validate` — Validate key (X-API-Key header)
- `POST /api/api-keys/revoke/{key_id}` — Revoke key

## Testing Status
- **Iteration 50**: All 19 backend tests + frontend tests PASSED (100%)
- CSRF protection matrix fully validated
- Session lifecycle fully validated
- API key CRUD fully validated

## Completed Tasks
- [x] Kraken API key discovery
- [x] Comprehensive security hardening
- [x] CSRF + session auth implementation
- [x] API key auth implementation
- [x] Frontend CSRF/session interceptor integration
- [x] Cleanup: Removed /app/scripts/safe_fix.py
- [x] P2: Cookie hardening — Secure flag + SameSite=lax on all CSRF cookies
- [x] P2: CORS tightened from wildcard `*` to specific origin
- [x] P2: Deep frontend UI flow testing — session init, navigation, POST CSRF headers verified
- [x] Vulnerability fixes: Frontend 6→0 (removed react-scripts/craco, upgraded vite 5→7, eslint 9→10)
- [x] Vulnerability fixes: Backend 10→2 (upgraded fastapi, starlette, pymongo, motor, cryptography, pillow, protobuf, pyasn1, python-multipart)

## Remaining Vulnerabilities (No Patch Available)
- diskcache 5.6.3 (CVE-2025-69872) — used in ML caching, no fix released
- ecdsa 0.19.1 (CVE-2024-23342) — transitive dep of python-jose, no fix released

## Backlog
- No remaining actionable items
