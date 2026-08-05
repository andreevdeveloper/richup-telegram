"""Inline keyboards for navigating demo scenarios."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from richup_bot.callbacks import DemoAction, DemoCallback


def build_demo_menu() -> InlineKeyboardMarkup:
    """Build the primary feature menu."""
    button = _callback_button
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                button("Форматирование", DemoAction.FORMATTING),
                button("Ссылки", DemoAction.LINKS),
            ],
            [
                button("Структура", DemoAction.STRUCTURE),
                button("Списки", DemoAction.LISTS),
            ],
            [
                button("Таблица", DemoAction.TABLE),
                button("Details", DemoAction.DETAILS),
            ],
            [
                button("Rich Markdown", DemoAction.RICH_MARKDOWN),
                button("Ссылки в опросе", DemoAction.POLL_LINKS),
            ],
            [
                button("Редактирование", DemoAction.EDIT),
                button("Инспектор AST", DemoAction.INSPECT_HELP),
            ],
            [
                button("Streaming Draft", DemoAction.STREAM_INFO),
            ],
        ]
    )


def build_back_keyboard() -> InlineKeyboardMarkup:
    """Build navigation back to the rich menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[_callback_button("Назад в меню", DemoAction.MENU)]]
    )


def build_stream_keyboard() -> InlineKeyboardMarkup:
    """Build streaming controls for a regular private chat."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_callback_button("Запустить стриминг", DemoAction.STREAM_RUN)],
            [_callback_button("Назад в меню", DemoAction.MENU)],
        ]
    )


def build_edit_keyboard(*, revision: int) -> InlineKeyboardMarkup:
    """Build a keyboard that toggles an editable rich message revision."""
    next_revision = 2 if revision == 1 else 1
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Переключить на ревизию {next_revision}",
                    callback_data=f"edit:{next_revision}",
                )
            ]
        ]
    )


def _callback_button(text: str, action: DemoAction) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=DemoCallback(action=action).pack())
