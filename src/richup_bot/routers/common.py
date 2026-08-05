"""Entry-point commands and navigation."""

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from richup_bot.content import build_menu_document
from richup_bot.keyboards import build_demo_menu

router = Router(name=__name__)

HELP_TEXT = """Доступные сценарии:
/rich — открыть интерактивное rich-меню
/markdown — Rich Markdown, совместимый с GFM
/stream — анимированный draft в обычном личном чате
/edit — редактирование через editMessageText с rich_message
/poll_links — ссылки в вариантах опроса через InputMediaLink
/inspect — инспектор входящего RichMessage AST
/menu — открыть главное меню

Для inline mode включите /setinline у @BotFather, затем введите имя бота в любом чате.
Join-request queries обрабатываются согласно JOIN_REQUEST_MODE."""


@router.message(CommandStart())
async def handle_start(message: Message, bot: Bot) -> None:
    """Show the concise entry point."""
    await _send_menu(message, bot)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Show commands and prerequisites."""
    await message.answer(HELP_TEXT, reply_markup=build_demo_menu())


@router.message(Command("menu"))
async def handle_menu(message: Message, bot: Bot) -> None:
    """Reopen the feature menu."""
    await _send_menu(message, bot)


async def _send_menu(message: Message, bot: Bot) -> None:
    first_name = message.from_user.first_name if message.from_user else "разработчик"
    await bot.send_rich_message(
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        rich_message=build_menu_document(first_name=first_name),
        reply_markup=build_demo_menu(),
    )
