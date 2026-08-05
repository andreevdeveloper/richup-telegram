"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class SettingsError(ValueError):
    """Raised when application settings are missing or invalid."""


class JoinRequestMode(StrEnum):
    """Available policies for Bot API 10.1 join-request queries."""

    QUEUE = "queue"
    APPROVE = "approve"
    DECLINE = "decline"
    WEBAPP = "webapp"


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated runtime settings."""

    bot_token: str
    stream_delay_seconds: float = 0.35
    log_level: int = logging.INFO
    join_request_mode: JoinRequestMode = JoinRequestMode.QUEUE
    join_request_web_app_url: str | None = None
    drop_pending_updates: bool = False

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Build settings from a mapping or the current process environment."""
        source = os.environ if environ is None else environ
        token = source.get("BOT_TOKEN", "").strip()
        if not token or "replace-with-real-token" in token:
            raise SettingsError("BOT_TOKEN is required and must contain a real BotFather token")

        delay_ms = _parse_int(source, "STREAM_DELAY_MS", default=350, minimum=0, maximum=5000)
        log_level = _parse_log_level(source.get("LOG_LEVEL", "INFO"))
        mode = _parse_join_request_mode(source.get("JOIN_REQUEST_MODE", "queue"))
        web_app_url = source.get("JOIN_REQUEST_WEB_APP_URL", "").strip() or None
        if mode is JoinRequestMode.WEBAPP and (
            web_app_url is None or not web_app_url.startswith("https://")
        ):
            raise SettingsError(
                "JOIN_REQUEST_WEB_APP_URL must be an HTTPS URL when JOIN_REQUEST_MODE=webapp"
            )

        return cls(
            bot_token=token,
            stream_delay_seconds=delay_ms / 1000,
            log_level=log_level,
            join_request_mode=mode,
            join_request_web_app_url=web_app_url,
            drop_pending_updates=_parse_bool(source.get("DROP_PENDING_UPDATES", "false")),
        )


def _parse_int(
    source: Mapping[str, str],
    key: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw_value = source.get(key, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise SettingsError(f"{key} must be an integer") from error
    if not minimum <= value <= maximum:
        raise SettingsError(f"{key} must be between {minimum} and {maximum}")
    return value


def _parse_bool(raw_value: str) -> bool:
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError("DROP_PENDING_UPDATES must be a boolean")


def _parse_log_level(raw_value: str) -> int:
    normalized = raw_value.strip().upper()
    level = logging.getLevelNamesMapping().get(normalized)
    if level is None:
        raise SettingsError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
    return level


def _parse_join_request_mode(raw_value: str) -> JoinRequestMode:
    try:
        return JoinRequestMode(raw_value.strip().lower())
    except ValueError as error:
        choices = ", ".join(mode.value for mode in JoinRequestMode)
        raise SettingsError(f"JOIN_REQUEST_MODE must be one of: {choices}") from error
