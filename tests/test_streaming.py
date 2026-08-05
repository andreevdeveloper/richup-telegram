from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Bot
from aiogram.types import InputRichMessage, Message

from richup_bot.services.streaming import stream_rich_message


@pytest.mark.asyncio
async def test_stream_reuses_draft_id_then_persists_result() -> None:
    bot = cast(Bot, AsyncMock(spec=Bot))
    final_message = cast(Message, object())
    bot.send_rich_message.return_value = final_message
    frames = [InputRichMessage(html="one"), InputRichMessage(html="two")]
    result = InputRichMessage(html="done")

    returned = await stream_rich_message(
        bot,
        chat_id=42,
        frames=frames,
        result=result,
        delay_seconds=0,
        message_thread_id=5,
        draft_id_factory=lambda: 99,
    )

    assert returned is final_message
    assert bot.send_rich_message_draft.await_count == 2
    assert {call.kwargs["draft_id"] for call in bot.send_rich_message_draft.await_args_list} == {99}
    bot.send_rich_message.assert_awaited_once_with(
        chat_id=42,
        rich_message=result,
        message_thread_id=5,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("frames", "delay", "draft_id", "error_fragment"),
    [
        ([], 0, 1, "at least one"),
        ([InputRichMessage(html="x")], -1, 1, "negative"),
        ([InputRichMessage(html="x")], 0, 0, "zero"),
    ],
)
async def test_stream_rejects_invalid_arguments(
    frames: list[InputRichMessage],
    delay: float,
    draft_id: int,
    error_fragment: str,
) -> None:
    bot = cast(Bot, AsyncMock(spec=Bot))

    with pytest.raises(ValueError, match=error_fragment):
        await stream_rich_message(
            bot,
            chat_id=42,
            frames=frames,
            result=InputRichMessage(html="done"),
            delay_seconds=delay,
            draft_id_factory=lambda: draft_id,
        )


@pytest.mark.asyncio
async def test_stream_generates_nonzero_id_and_waits_between_frames() -> None:
    bot = cast(Bot, AsyncMock(spec=Bot))
    bot.send_rich_message.return_value = cast(Message, object())

    with patch("richup_bot.services.streaming.asyncio.sleep", new_callable=AsyncMock) as sleep:
        await stream_rich_message(
            bot,
            chat_id=42,
            frames=[InputRichMessage(html="one"), InputRichMessage(html="two")],
            result=InputRichMessage(html="done"),
            delay_seconds=0.01,
        )

    draft_ids = {call.kwargs["draft_id"] for call in bot.send_rich_message_draft.await_args_list}
    assert len(draft_ids) == 1
    assert next(iter(draft_ids)) > 0
    sleep.assert_awaited_once_with(0.01)
