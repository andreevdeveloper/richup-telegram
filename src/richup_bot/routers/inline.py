"""Inline-query Rich Message demo."""

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputRichMessageContent

from richup_bot.content import build_inline_result

router = Router(name=__name__)


@router.inline_query()
async def handle_inline_query(query: InlineQuery) -> None:
    """Return a rich document through InputRichMessageContent."""
    result = InlineQueryResultArticle(
        id="rich-message-10-1",
        title="Демонстрация Rich Messages",
        description="Bot API 10.1 через InputRichMessageContent",
        input_message_content=InputRichMessageContent(rich_message=build_inline_result()),
    )
    await query.answer([result], cache_time=1, is_personal=True)
