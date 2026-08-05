from aiogram.methods import (
    AnswerChatJoinRequestQuery,
    EditMessageText,
    SendChatJoinRequestWebApp,
    SendRichMessage,
    SendRichMessageDraft,
)
from aiogram.types import (
    InputMediaLink,
    InputPollOption,
    InputRichMessage,
    InputRichMessageContent,
)


def test_aiogram_329_serializes_rich_message_methods() -> None:
    rich_message = InputRichMessage(html="<h1>Demo</h1>")

    send = SendRichMessage(chat_id=42, rich_message=rich_message)
    draft = SendRichMessageDraft(chat_id=42, draft_id=7, rich_message=rich_message)
    edit = EditMessageText(chat_id=42, message_id=9, rich_message=rich_message)

    assert send.__api_method__ == "sendRichMessage"
    assert draft.__api_method__ == "sendRichMessageDraft"
    assert edit.__api_method__ == "editMessageText"
    assert edit.text is None


def test_aiogram_329_serializes_rich_inline_content() -> None:
    content = InputRichMessageContent(
        rich_message=InputRichMessage(markdown="# Inline")
    ).model_dump(mode="json", exclude_none=True, exclude_defaults=True)

    assert content == {"rich_message": {"markdown": "# Inline"}}


def test_aiogram_329_accepts_link_media_in_poll_option() -> None:
    option = InputPollOption(
        text="Specification",
        text_parse_mode=None,
        media=InputMediaLink(url="https://core.telegram.org/bots/api"),
    ).model_dump(mode="json", exclude_none=True)

    assert option["media"] == {
        "type": "link",
        "url": "https://core.telegram.org/bots/api",
    }


def test_aiogram_329_serializes_join_request_query_methods() -> None:
    answer = AnswerChatJoinRequestQuery(
        chat_join_request_query_id="query-1",
        result="queue",
    )
    webapp = SendChatJoinRequestWebApp(
        chat_join_request_query_id="query-1",
        web_app_url="https://example.com/join",
    )

    assert answer.__api_method__ == "answerChatJoinRequestQuery"
    assert webapp.__api_method__ == "sendChatJoinRequestWebApp"
