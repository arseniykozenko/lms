# LMS Backend

Simple backend foundation for an online learning platform built with FastAPI, SQLAlchemy, PostgreSQL, and JWT.

## Quick start

1. Create a virtual environment and install dependencies.
2. Copy `.env.example` to `.env`.
3. Update `DATABASE_URL` for your PostgreSQL instance.
4. Start the API with `uvicorn app.main:app --reload`.

Tables are created automatically on startup for this simplified stage.

## Main endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

## Swagger testing

1. Open `/docs`.
2. Call `POST /api/v1/auth/register` or `POST /api/v1/auth/login`.
3. Copy `access_token`.
4. Click `Authorize` and paste `Bearer <access_token>`.
5. Call `GET /api/v1/auth/me`.
