# Hemo Chain Backend

Flask REST API for Hemo Chain authentication, role-based dashboards, and secure record verification status.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Edit `.env`, then seed the first admin:

```bash
python3 -m flask --app backend.app seed-admin
```

Run the API:

```bash
python3 -m flask --app backend.app run --host 0.0.0.0 --port 5000
```

## Auth Endpoints

- `POST /api/auth/donor/signup`
- `POST /api/auth/hospital/signup`
- `POST /api/auth/bloodbank/signup`
- `POST /api/auth/donor/login`
- `POST /api/auth/hospital/login`
- `POST /api/auth/bloodbank/login`
- `POST /api/auth/admin/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

Login responses include `role`, `redirect`, `token`, `refresh_token`, and public user data.

## Protected Dashboard APIs

- `GET /api/dashboard/me`
- `GET /api/dashboard/donor`
- `GET /api/dashboard/hospital`
- `GET /api/dashboard/bloodbank`
- `GET /api/dashboard/admin`
- `GET /api/dashboard/blockchain-verification`

Send JWTs as:

```http
Authorization: Bearer <token>
```
