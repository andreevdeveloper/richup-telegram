import logging

import pytest

from richup_bot.config import JoinRequestMode, Settings, SettingsError


def test_settings_load_valid_environment() -> None:
    environ = {
        "BOT_TOKEN": "123456789:secret",
        "STREAM_DELAY_MS": "125",
        "LOG_LEVEL": "debug",
        "JOIN_REQUEST_MODE": "webapp",
        "JOIN_REQUEST_WEB_APP_URL": "https://example.com/join",
        "DROP_PENDING_UPDATES": "yes",
    }

    settings = Settings.from_env(environ)

    assert settings.bot_token == "123456789:secret"
    assert settings.stream_delay_seconds == 0.125
    assert settings.log_level == logging.DEBUG
    assert settings.join_request_mode is JoinRequestMode.WEBAPP
    assert settings.join_request_web_app_url == "https://example.com/join"
    assert settings.drop_pending_updates is True


def test_settings_use_safe_defaults() -> None:
    settings = Settings.from_env({"BOT_TOKEN": "123456789:secret"})

    assert settings.stream_delay_seconds == 0.35
    assert settings.join_request_mode is JoinRequestMode.QUEUE
    assert settings.drop_pending_updates is False


@pytest.mark.parametrize(
    ("environ", "error_fragment"),
    [
        ({}, "BOT_TOKEN"),
        ({"BOT_TOKEN": "123:replace-with-real-token"}, "BOT_TOKEN"),
        ({"BOT_TOKEN": "123:x", "STREAM_DELAY_MS": "slow"}, "integer"),
        ({"BOT_TOKEN": "123:x", "STREAM_DELAY_MS": "5001"}, "between"),
        ({"BOT_TOKEN": "123:x", "LOG_LEVEL": "TRACE"}, "LOG_LEVEL"),
        ({"BOT_TOKEN": "123:x", "JOIN_REQUEST_MODE": "random"}, "JOIN_REQUEST_MODE"),
        ({"BOT_TOKEN": "123:x", "DROP_PENDING_UPDATES": "sometimes"}, "boolean"),
        (
            {"BOT_TOKEN": "123:x", "JOIN_REQUEST_MODE": "webapp"},
            "JOIN_REQUEST_WEB_APP_URL",
        ),
        (
            {
                "BOT_TOKEN": "123:x",
                "JOIN_REQUEST_MODE": "webapp",
                "JOIN_REQUEST_WEB_APP_URL": "http://example.com",
            },
            "HTTPS",
        ),
    ],
)
def test_settings_reject_invalid_environment(environ: dict[str, str], error_fragment: str) -> None:
    with pytest.raises(SettingsError, match=error_fragment):
        Settings.from_env(environ)
