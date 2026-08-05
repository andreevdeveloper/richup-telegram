"""Typed callback payloads used by the demo menu."""

from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class DemoAction(StrEnum):
    """Actions exposed through the inline demo menu."""

    MENU = "menu"
    FORMATTING = "formatting"
    LINKS = "links"
    STRUCTURE = "structure"
    LISTS = "lists"
    TABLE = "table"
    DETAILS = "details"
    RICH_MARKDOWN = "rich_markdown"
    STREAM_INFO = "stream_info"
    STREAM_RUN = "stream_run"
    EDIT = "edit"
    POLL_LINKS = "poll_links"
    INSPECT_HELP = "inspect_help"


class DemoCallback(CallbackData, prefix="demo"):
    """Compact and validated callback data."""

    action: DemoAction
