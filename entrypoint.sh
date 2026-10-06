#!/bin/sh

set -e

echo "Ожидание PostgreSQL..."

until pg_isready -h db -p 5432 -U user; do
  sleep 2
done

echo "PostgreSQL готов."

echo "Применение миграций..."
alembic upgrade head

echo "Запуск приложения..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000