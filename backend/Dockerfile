ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH="/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

FROM base AS builder

WORKDIR /

COPY requirements.txt .

RUN set -ex && \
    python -m venv .venv && \
    pip install --upgrade pip && \
    pip install -r ./requirements.txt

FROM base

WORKDIR /app

COPY --from=builder /.venv /.venv
ADD ./ ./

# Runtime configuration is supplied via docker-compose env_file (variables.env).

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
