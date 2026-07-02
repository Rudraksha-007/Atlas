<h1>Atlas</h1>

https://img.shields.io/badge/readme%2520style-standard-brightgreen.svg

Backend service for capsule-based data management with OAuth 2.0 authentication.

Atlas provides a secure REST API for creating, storing, and managing digital capsules—encrypted containers for sensitive data. It handles user authentication via OAuth 2.0, refresh token rotation, and integrates with PostgreSQL through SQLAlchemy, with Alembic managing schema migrations.

The project is built with FastAPI and is designed to be deployed as a standalone service.
Table of Contents

    Security

    Background

    Install

    Usage

    API

Security

Atlas implements OAuth 2.0 with refresh token expiry and versioning to mitigate replay attacks. All passwords are hashed using bcrypt, and tokens are signed with HS256. Environment variables must be set for SECRET_KEY, DATABASE_URL, and OAuth client credentials.
Background

This service was built to provide a lightweight, self‑hostable backend for applications that require secure data encapsulation. The capsule abstraction allows users to group related data under a single access‑controlled entity, with each capsule owning its own permissions.

Key dependencies:

    FastAPI – web framework

    SQLAlchemy – ORM

    Alembic – migrations

    python-jose – JWT handling

    passlib – password hashing

The authentication flow follows the OAuth 2.0 authorization code grant, with provisions for third‑party identity providers (planned).
Install

Atlas requires Python 3.12 or newer and uv for dependency management.
sh

# Clone the repository

git clone https://github.com/your-org/atlas.git
cd atlas

# Install dependencies with uv (recommended)

uv sync

# Alternatively, using pip and requirements.txt

pip install -r requirements.txt

Dependencies

    PostgreSQL (version 13+)

    uv (optional, but recommended)

    Python 3.12+

Database Setup

Run Alembic migrations to set up the schema:
sh

alembic upgrade head

Usage

    Copy .env.example to .env and fill in the required variables (see Security).

    Start the development server:

sh

uv run uvicorn main:app --reload

Or with plain Python:
sh

python -m uvicorn main:app --reload

The API will be available at http://localhost:8000. Interactive documentation is served at /docs.
CLI

Atlas does not provide a CLI; all interactions happen via the REST API. Use tools like curl or the Swagger UI for testing.
Example Request
sh

# Obtain an access token via OAuth 2.0 password grant (for testing)

curl -X POST http://localhost:8000/auth/token \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=user@example.com&password=secret&grant_type=password"

API

Full API specification is available in the OpenAPI schema at /openapi.json and in the interactive docs at /docs.

Major endpoints:

    POST /auth/token – obtain access/refresh tokens

    POST /auth/refresh – refresh an access token

    GET /capsules – list all capsules for the authenticated user

    POST /capsules – create a new capsule

    GET /capsules/{id} – retrieve a specific capsule

    PUT /capsules/{id} – update a capsule

    DELETE /capsules/{id} – delete a capsule

All protected endpoints require the Authorization: Bearer <access_token> header.
