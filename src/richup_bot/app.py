"""Application assembly and long-polling lifecycle."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from richup_bot.config import Settings
from richup_bot.routers import build_root_router

logger = logging.getLogger(__name__)

BOT_COMMANDS = (
    BotCommand(command="start", description="Открыть демонстрацию Rich Messages"),
    BotCommand(command="rich", description="Открыть интерактивное rich-меню"),
    BotCommand(command="markdown", description="Показать Rich Markdown"),
    BotCommand(command="stream", description="Запустить потоковый rich draft"),
    BotCommand(command="edit", description="Отредактировать rich-сообщение"),
    BotCommand(command="poll_links", description="Показать ссылки в опросе"),
    BotCommand(command="inspect", description="Исследовать входящий RichMessage AST"),
    BotCommand(command="help", description="Показать команды и требования"),
)


def create_dispatcher() -> Dispatcher:
    """Create an isolated dispatcher suitable for production and tests."""
    dispatcher = Dispatcher()
    dispatcher.include_router(build_root_router())
    return dispatcher


async def run_polling(settings: Settings) -> None:
    """Configure the bot and run long polling until shutdown."""
    dispatcher = create_dispatcher()
    async with Bot(token=settings.bot_token) as bot:
        await bot.delete_webhook(drop_pending_updates=settings.drop_pending_updates)
        await bot.set_my_commands(list(BOT_COMMANDS))
        me = await bot.get_me()
        logger.info("Starting @%s with long polling", me.username)
        await dispatcher.start_polling(
            bot,
            settings=settings,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
