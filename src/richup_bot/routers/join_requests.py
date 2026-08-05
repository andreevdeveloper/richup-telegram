"""Bot API 10.1 chat join-request query handling."""

import logging

from aiogram import Router
from aiogram.types import ChatJoinRequest

from richup_bot.config import JoinRequestMode, Settings

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.chat_join_request()
async def handle_join_request(request: ChatJoinRequest, settings: Settings) -> None:
    """Resolve query-enabled join requests according to an explicit policy."""
    if request.query_id is None:
        logger.info(
            "Classic join request received; query API is unavailable",
            extra={"chat_id": request.chat.id, "user_id": request.from_user.id},
        )
        return

    if settings.join_request_mode is JoinRequestMode.WEBAPP:
        if settings.join_request_web_app_url is None:
            raise RuntimeError("validated web app URL is unexpectedly missing")
        await request.send_webapp(web_app_url=settings.join_request_web_app_url)
        return

    await request.answer_query(result=settings.join_request_mode.value)
