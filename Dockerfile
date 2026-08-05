# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip wheel --wheel-dir /wheels .


FROM python:${PYTHON_VERSION}-slim AS runtime

ARG APP_VERSION=0.1.0

LABEL org.opencontainers.image.title="Rich Messages Demo" \
      org.opencontainers.image.description="aiogram 3.29.1 and Telegram Bot API 10.1 demo" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /wheels /wheels

RUN python -m pip install /wheels/* \
    && rm -rf /wheels

WORKDIR /app
USER 10001:10001

ENTRYPOINT ["richup-bot"]

