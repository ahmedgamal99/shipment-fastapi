# FastShip

FastShip is a FastAPI-based delivery management platform that helps sellers hand off shipments and gives delivery partners the tools they need to fulfill orders. The service exposes a REST API, asynchronous workers for notifications, and email templates for customer communication.

## Tech stack
- FastAPI with Pydantic for the HTTP layer (`app/main.py`)
- SQLModel + SQLAlchemy + Alembic for persistence (`app/database`) 
- Celery and Redis for asynchronous tasks (`app/worker`)
- Twilio and transactional email templates for notifications (`app/templates`)
- Pytest for testing (`app/tests`)

## Getting started
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install project dependencies (adjust to your tooling):
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env` to `.env.local` (or similar) and populate the values noted in [Configuration](#configuration).
4. Launch backing services (PostgreSQL and Redis) and start the API:
   ```bash
   redis-server
   uvicorn app.main:app --reload
   ```
5. In a second terminal, start the Celery worker and (optionally) Flower for task monitoring:
   ```bash
   celery -A app.worker.tasks worker -E
   celery -A app.worker.tasks flower
   ```

## Configuration
Environment variables are loaded via Pydantic settings (`app/config.py`). Key variables:

```ini
# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fastship

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
JWT_SECRET=
JWT_ALGORITHM=HS256

# Email (FastMail/SMTP)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_FROM_NAME=
MAIL_SERVER=
MAIL_PORT=
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true

# Twilio
TWILIO_SID=
TWILIO_AUTH_TOKEN=
TWILIO_NUMBER=
```

Store secrets in your local `.env` file; never commit them to source control.

## Database migrations
- Create a new migration: `alembic revision --autogenerate -m "describe change"`
- Apply migrations: `alembic upgrade head`

## Running tests
Execute the suite with pytest:
```bash
pytest
```

## Repository layout
```
app/
  api/         # FastAPI routers and schemas
  core/        # Exception handlers and auth utilities
  database/    # SQLModel models and session helpers
  services/    # Domain services for shipments, sellers, partners
  worker/      # Celery tasks
  templates/   # Email and web templates
migrations/    # Alembic environment and revisions
scripts/       # Helper scripts
```

## Helpful commands
See `commands.txt` for frequently used runtime commands (Uvicorn, Redis, Celery, Alembic).
