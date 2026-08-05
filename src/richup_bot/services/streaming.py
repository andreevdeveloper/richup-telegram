"""Deterministic rich-draft streaming service."""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Callable, Sequence

from aiogram import Bot
from aiogram.types import InputRichMessage, Message

DraftIdFactory = Callable[[], int]


async def stream_rich_message(
    bot: Bot,
    *,
    chat_id: int,
    frames: Sequence[InputRichMessage],
    result: InputRichMessage,
    delay_seconds: float,
    message_thread_id: int | None = None,
    draft_id_factory: DraftIdFactory | None = None,
) -> Message:
    """Stream ephemeral frames and persist the final rich message."""
    if not frames:
        raise ValueError("at least one draft frame is required")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must not be negative")

    factory = draft_id_factory or _new_draft_id
    draft_id = factory()
    if draft_id == 0:
        raise ValueError("draft_id_factory returned zero")

    for index, frame in enumerate(frames):
        await bot.send_rich_message_draft(
            chat_id=chat_id,
            draft_id=draft_id,
            rich_message=frame,
            message_thread_id=message_thread_id,
        )
        if index < len(frames) - 1 and delay_seconds:
            await asyncio.sleep(delay_seconds)

    return await bot.send_rich_message(
        chat_id=chat_id,
        rich_message=result,
        message_thread_id=message_thread_id,
    )


def _new_draft_id() -> int:
    return secrets.randbelow(2**31 - 1) + 1
