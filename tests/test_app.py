from collections.abc import Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from richup_bot import __main__
from richup_bot.app import BOT_COMMANDS, create_dispatcher, run_polling
from richup_bot.config import Settings, SettingsError


def test_dispatcher_registers_only_used_update_types() -> None:
    dispatcher = create_dispatcher()

    assert dispatcher.resolve_used_update_types() == [
        "callback_query",
        "chat_join_request",
        "inline_query",
        "message",
    ]


@pytest.mark.asyncio
async def test_run_polling_configures_bot_and_dispatcher(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bot = MagicMock()
    fake_bot.__aenter__ = AsyncMock(return_value=fake_bot)
    fake_bot.__aexit__ = AsyncMock(return_value=None)
    fake_bot.delete_webhook = AsyncMock()
    fake_bot.set_my_commands = AsyncMock()
    fake_bot.get_me = AsyncMock(return_value=MagicMock(username="rich_demo_bot"))
    fake_dispatcher = MagicMock()
    fake_dispatcher.resolve_used_update_types.return_value = ["message"]
    fake_dispatcher.start_polling = AsyncMock()
    bot_factory = MagicMock(return_value=fake_bot)
    monkeypatch.setattr("richup_bot.app.Bot", bot_factory)
    monkeypatch.setattr("richup_bot.app.create_dispatcher", lambda: fake_dispatcher)
    settings = Settings(bot_token="123:token", drop_pending_updates=True)

    await run_polling(settings)

    bot_factory.assert_called_once_with(token="123:token")
    fake_bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=True)
    fake_bot.set_my_commands.assert_awaited_once_with(list(BOT_COMMANDS))
    fake_dispatcher.start_polling.assert_awaited_once_with(
        fake_bot,
        settings=settings,
        allowed_updates=["message"],
    )


def test_cli_reports_invalid_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        __main__.Settings,
        "from_env",
        MagicMock(side_effect=SettingsError("bad token")),
    )

    with pytest.raises(SystemExit, match="Configuration error: bad token"):
        __main__.run()


def test_cli_runs_async_application(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(bot_token="123:token")
    monkeypatch.setattr(__main__.Settings, "from_env", MagicMock(return_value=settings))
    runner = MagicMock()

    def close_coroutine(coroutine: Coroutine[Any, Any, None]) -> None:
        coroutine.close()
        runner(coroutine)

    monkeypatch.setattr(__main__.asyncio, "run", close_coroutine)

    __main__.run()

    runner.assert_called_once()
