#!/bin/sh
set -e

echo "[entrypoint] Applying database migrations..."
if alembic upgrade head; then
    echo "[entrypoint] Migrations up to date."
else
    echo "[entrypoint] Migration chain not applicable to this database"
    echo "[entrypoint] (base tables are normally created by the app)."
    echo "[entrypoint] Creating schema from models and stamping head..."
    python -c "from app.db.base import Base; from app.db.database import engine; import app.db.models; Base.metadata.create_all(bind=engine)"
    alembic stamp head
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
