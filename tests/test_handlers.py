from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, ChatJoinRequest, InaccessibleMessage, InlineQuery, Message

from richup_bot.callbacks import DemoAction, DemoCallback
from richup_bot.config import JoinRequestMode, Settings
from richup_bot.routers import common, inline, join_requests, rich


def make_message(*, chat_type: ChatType = ChatType.PRIVATE) -> Message:
    message = AsyncMock(spec=Message)
    message.chat = SimpleNamespace(id=42, type=chat_type)
    message.message_thread_id = 5
    message.message_id = 9
    message.from_user = SimpleNamespace(id=7, first_name="Ada")
    message.rich_message = None
    message.answer = AsyncMock()
    return cast(Message, message)


def make_callback(message: Message | InaccessibleMessage | None) -> CallbackQuery:
    callback = AsyncMock(spec=CallbackQuery)
    callback.message = message
    callback.data = None
    callback.from_user = SimpleNamespace(id=8, first_name="Grace")
    callback.answer = AsyncMock()
    return cast(CallbackQuery, callback)


def make_bot() -> Bot:
    bot = AsyncMock(spec=Bot)
    bot.send_rich_message.return_value = MagicMock(spec=Message)
    return cast(Bot, bot)


@pytest.mark.asyncio
async def test_common_handlers_answer_with_navigation() -> None:
    message = make_message()

    await common.handle_start(message)
    await common.handle_help(message)
    await common.handle_menu(message)

    assert message.answer.await_count == 3
    assert all(call.kwargs.get("reply_markup") for call in message.answer.await_args_list)


@pytest.mark.asyncio
async def test_rich_command_handlers_send_every_scenario() -> None:
    message = make_message()
    bot = make_bot()
    settings = Settings(bot_token="123:token", stream_delay_seconds=0)

    await rich.handle_rich_html(message, bot)
    await rich.handle_rich_markdown(message, bot)
    await rich.handle_stream(message, bot, settings)
    await rich.handle_edit(message, bot)
    await rich.handle_poll_links(message, bot)
    await rich.handle_inspect_help(message)

    assert bot.send_rich_message.await_count == 4
    bot.send_rich_message_draft.assert_awaited()
    bot.send_poll.assert_awaited_once()
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_stream_command_rejects_non_private_chat() -> None:
    message = make_message(chat_type=ChatType.GROUP)

    await rich.handle_stream(
        message,
        make_bot(),
        Settings(bot_token="123:token"),
    )

    message.answer.assert_awaited_once_with("Rich drafts are available only in private chats.")


@pytest.mark.asyncio
async def test_demo_callback_rejects_missing_message() -> None:
    callback = make_callback(None)

    await rich.handle_demo_callback(
        callback,
        DemoCallback(action=DemoAction.RICH_HTML),
        make_bot(),
        Settings(bot_token="123:token"),
    )

    callback.answer.assert_awaited_once_with("The source message is unavailable.", show_alert=True)


@pytest.mark.asyncio
async def test_demo_callback_rejects_inaccessible_message() -> None:
    inaccessible = cast(InaccessibleMessage, MagicMock(spec=InaccessibleMessage))
    callback = make_callback(inaccessible)

    await rich.handle_demo_callback(
        callback,
        DemoCallback(action=DemoAction.RICH_HTML),
        make_bot(),
        Settings(bot_token="123:token"),
    )

    callback.answer.assert_awaited_once_with("The source message is unavailable.", show_alert=True)


@pytest.mark.asyncio
async def test_demo_callback_rejects_group_stream() -> None:
    callback = make_callback(make_message(chat_type=ChatType.SUPERGROUP))

    await rich.handle_demo_callback(
        callback,
        DemoCallback(action=DemoAction.STREAM),
        make_bot(),
        Settings(bot_token="123:token"),
    )

    callback.answer.assert_awaited_once_with(
        "Draft streaming works only in a private chat.", show_alert=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("action", list(DemoAction))
async def test_demo_callback_dispatches_each_action(action: DemoAction) -> None:
    callback = make_callback(make_message())
    bot = make_bot()

    await rich.handle_demo_callback(
        callback,
        DemoCallback(action=action),
        bot,
        Settings(bot_token="123:token", stream_delay_seconds=0),
    )

    callback.answer.assert_awaited_once_with()
    if action is DemoAction.POLL_LINKS:
        bot.send_poll.assert_awaited_once()
    elif action is DemoAction.INSPECT_HELP:
        bot.send_message.assert_awaited_once()
    else:
        bot.send_rich_message.assert_awaited()


@pytest.mark.asyncio
async def test_edit_callback_handles_missing_and_available_message() -> None:
    missing = make_callback(None)
    await rich.handle_edit_callback(missing, make_bot())
    missing.answer.assert_awaited_once_with("The source message is unavailable.", show_alert=True)

    callback = make_callback(make_message())
    callback.data = "edit:2"
    bot = make_bot()
    await rich.handle_edit_callback(callback, bot)

    bot.edit_message_text.assert_awaited_once()
    assert bot.edit_message_text.await_args.kwargs["message_id"] == 9
    callback.answer.assert_awaited_once_with("Revision 2")


@pytest.mark.asyncio
async def test_incoming_rich_message_serializes_and_truncates_ast() -> None:
    empty = make_message()
    await rich.handle_incoming_rich_message(empty)
    empty.answer.assert_not_awaited()

    message = make_message()
    rich_message = MagicMock()
    rich_message.model_dump.return_value = {"blocks": ["x" * 5000]}
    message.rich_message = rich_message
    await rich.handle_incoming_rich_message(message)

    response = message.answer.await_args.args[0]
    assert len(response) < 3900
    assert response.endswith("... truncated")


@pytest.mark.asyncio
async def test_inline_query_returns_rich_input_content() -> None:
    query = cast(InlineQuery, AsyncMock(spec=InlineQuery))
    query.answer = AsyncMock()

    await inline.handle_inline_query(query)

    query.answer.assert_awaited_once()
    result = query.answer.await_args.args[0][0]
    assert result.input_message_content.rich_message.html is not None


def make_join_request(query_id: str | None) -> ChatJoinRequest:
    request = AsyncMock(spec=ChatJoinRequest)
    request.query_id = query_id
    request.chat = SimpleNamespace(id=-1001)
    request.from_user = SimpleNamespace(id=7)
    request.answer_query = AsyncMock()
    request.send_webapp = AsyncMock()
    return cast(ChatJoinRequest, request)


@pytest.mark.asyncio
async def test_classic_join_request_is_left_untouched() -> None:
    request = make_join_request(None)

    await join_requests.handle_join_request(request, Settings(bot_token="123:token"))

    request.answer_query.assert_not_awaited()
    request.send_webapp.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode",
    [JoinRequestMode.QUEUE, JoinRequestMode.APPROVE, JoinRequestMode.DECLINE],
)
async def test_join_request_answers_with_configured_policy(mode: JoinRequestMode) -> None:
    request = make_join_request("query-1")

    await join_requests.handle_join_request(
        request,
        Settings(bot_token="123:token", join_request_mode=mode),
    )

    request.answer_query.assert_awaited_once_with(result=mode.value)


@pytest.mark.asyncio
async def test_join_request_can_open_webapp() -> None:
    request = make_join_request("query-1")

    await join_requests.handle_join_request(
        request,
        Settings(
            bot_token="123:token",
            join_request_mode=JoinRequestMode.WEBAPP,
            join_request_web_app_url="https://example.com/join",
        ),
    )

    request.send_webapp.assert_awaited_once_with(web_app_url="https://example.com/join")


@pytest.mark.asyncio
async def test_join_request_rejects_invalid_webapp_state() -> None:
    request = make_join_request("query-1")

    with pytest.raises(RuntimeError, match="unexpectedly missing"):
        await join_requests.handle_join_request(
            request,
            Settings(bot_token="123:token", join_request_mode=JoinRequestMode.WEBAPP),
        )
