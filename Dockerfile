FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Нужны для PostgreSQL и ожидания БД
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY entrypoint.sh .

RUN chmod +x /app/entrypoint.sh

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir .

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]