"""Rich messages, drafts, edits, polls and incoming AST inspection."""

from __future__ import annotations

import json
from typing import cast

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InputMediaLink,
    InputPollOption,
    InputRichMessage,
    Message,
)

from richup_bot.callbacks import DemoAction, DemoCallback
from richup_bot.config import Settings
from richup_bot.content import (
    AIROGRAM_DOCS_URL,
    BOT_API_DOCS_URL,
    build_details_showcase,
    build_draft_frames,
    build_edit_revision,
    build_formatting_showcase,
    build_links_showcase,
    build_lists_showcase,
    build_markdown_showcase,
    build_menu_document,
    build_stream_info,
    build_stream_result,
    build_structure_showcase,
    build_table_showcase,
)
from richup_bot.keyboards import (
    build_back_keyboard,
    build_demo_menu,
    build_edit_keyboard,
    build_stream_keyboard,
)
from richup_bot.services.streaming import stream_rich_message

router = Router(name=__name__)
MAX_AST_PREVIEW_LENGTH = 3800


@router.message(Command("rich"))
async def handle_rich_html(message: Message, bot: Bot) -> None:
    """Send the full Rich HTML showcase."""
    await _send_rich_menu(bot, message)


@router.message(Command("markdown"))
async def handle_rich_markdown(message: Message, bot: Bot) -> None:
    """Send the Rich Markdown showcase."""
    await bot.send_rich_message(
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        rich_message=build_markdown_showcase(),
        reply_markup=build_back_keyboard(),
    )


@router.message(Command("stream"))
async def handle_stream(message: Message, bot: Bot, settings: Settings) -> None:
    """Run a deterministic AI-style rich draft stream."""
    if message.chat.type != ChatType.PRIVATE:
        await message.answer("Streaming Draft работает только в обычном личном чате с ботом.")
        return
    await _stream(bot, message, settings)


@router.message(Command("edit"))
async def handle_edit(message: Message, bot: Bot) -> None:
    """Send a rich message that can be edited in place."""
    await _send_editable(bot, message.chat.id, message.message_thread_id)


@router.message(Command("poll_links"))
async def handle_poll_links(message: Message, bot: Bot) -> None:
    """Send a poll whose options contain Bot API 10.1 link media."""
    await _send_poll_links(bot, message.chat.id, message.message_thread_id)


@router.message(Command("inspect"))
async def handle_inspect_help(message: Message) -> None:
    """Explain how the incoming RichMessage AST handler is triggered."""
    await message.answer(
        "Перешлите боту rich-сообщение. Обработчик F.rich_message сериализует "
        "типизированное дерево RichMessage.blocks в JSON. Доставка пересланных сообщений "
        "зависит от настроек Telegram."
    )


@router.callback_query(DemoCallback.filter())
async def handle_demo_callback(
    callback: CallbackQuery,
    callback_data: DemoCallback,
    bot: Bot,
    settings: Settings,
) -> None:
    """Dispatch menu callbacks through typed CallbackData."""
    if not isinstance(callback.message, Message):
        await callback.answer("Исходное сообщение недоступно.", show_alert=True)
        return

    message = callback.message
    action = callback_data.action
    if action is DemoAction.STREAM_RUN and message.chat.type != ChatType.PRIVATE:
        await callback.answer(
            "Streaming Draft работает только в личном чате с ботом.",
            show_alert=True,
        )
        return

    await callback.answer()
    if action is DemoAction.MENU:
        await _edit_rich(
            bot,
            message,
            build_menu_document(first_name=callback.from_user.first_name),
            reply_markup=build_demo_menu(),
        )
    elif action is DemoAction.FORMATTING:
        await _edit_rich(bot, message, build_formatting_showcase())
    elif action is DemoAction.LINKS:
        await _edit_rich(
            bot,
            message,
            build_links_showcase(user_id=callback.from_user.id),
        )
    elif action is DemoAction.STRUCTURE:
        await _edit_rich(bot, message, build_structure_showcase())
    elif action is DemoAction.LISTS:
        await _edit_rich(bot, message, build_lists_showcase())
    elif action is DemoAction.TABLE:
        await _edit_rich(bot, message, build_table_showcase())
    elif action is DemoAction.DETAILS:
        await _edit_rich(bot, message, build_details_showcase())
    elif action is DemoAction.RICH_MARKDOWN:
        await _edit_rich(bot, message, build_markdown_showcase())
    elif action is DemoAction.STREAM_INFO:
        await _edit_rich(
            bot,
            message,
            build_stream_info(),
            reply_markup=build_stream_keyboard(),
        )
    elif action is DemoAction.STREAM_RUN:
        await _stream(bot, message, settings)
    elif action is DemoAction.EDIT:
        await _send_editable(bot, message.chat.id, message.message_thread_id)
    elif action is DemoAction.POLL_LINKS:
        await _send_poll_links(bot, message.chat.id, message.message_thread_id)
    elif action is DemoAction.INSPECT_HELP:
        await bot.send_message(
            chat_id=message.chat.id,
            message_thread_id=message.message_thread_id,
            text=(
                "Перешлите сюда rich-сообщение. Бот покажет типизированное дерево "
                "RichMessage.blocks в компактном JSON."
            ),
        )


@router.callback_query(F.data.regexp(r"^edit:[12]$"))
async def handle_edit_callback(callback: CallbackQuery, bot: Bot) -> None:
    """Replace an existing rich document atomically."""
    if callback.message is None or callback.data is None:
        await callback.answer("Исходное сообщение недоступно.", show_alert=True)
        return

    message = cast(Message, callback.message)
    revision = int(callback.data.removeprefix("edit:"))
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        rich_message=build_edit_revision(revision),
        reply_markup=build_edit_keyboard(revision=revision),
    )
    await callback.answer(f"Ревизия {revision}")


@router.message(F.rich_message)
async def handle_incoming_rich_message(message: Message) -> None:
    """Expose aiogram's typed response tree for protocol exploration."""
    if message.rich_message is None:
        return
    payload = message.rich_message.model_dump(mode="json", exclude_none=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(serialized) > MAX_AST_PREVIEW_LENGTH:
        serialized = f"{serialized[:MAX_AST_PREVIEW_LENGTH]}\n... обрезано"
    await message.answer(serialized)


async def _send_rich_menu(bot: Bot, message: Message) -> None:
    first_name = message.from_user.first_name if message.from_user else "разработчик"
    await bot.send_rich_message(
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        rich_message=build_menu_document(first_name=first_name),
        reply_markup=build_demo_menu(),
    )


async def _edit_rich(
    bot: Bot,
    message: Message,
    rich_message: InputRichMessage,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        rich_message=rich_message,
        reply_markup=reply_markup or build_back_keyboard(),
    )


async def _stream(bot: Bot, message: Message, settings: Settings) -> None:
    await stream_rich_message(
        bot,
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        frames=build_draft_frames(),
        result=build_stream_result(),
        delay_seconds=settings.stream_delay_seconds,
    )


async def _send_editable(bot: Bot, chat_id: int, message_thread_id: int | None) -> None:
    await bot.send_rich_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        rich_message=build_edit_revision(1),
        reply_markup=build_edit_keyboard(revision=1),
    )


async def _send_poll_links(bot: Bot, chat_id: int, message_thread_id: int | None) -> None:
    await bot.send_poll(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        question="Какую документацию Bot API 10.1 открыть первой?",
        options=[
            InputPollOption(
                text="Документация aiogram 3.29",
                text_parse_mode=None,
                media=InputMediaLink(url=AIROGRAM_DOCS_URL),
            ),
            InputPollOption(
                text="Спецификация Telegram Bot API",
                text_parse_mode=None,
                media=InputMediaLink(url=BOT_API_DOCS_URL),
            ),
        ],
        is_anonymous=False,
    )
