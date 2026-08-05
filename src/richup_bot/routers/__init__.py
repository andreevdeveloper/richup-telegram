"""Feature routers."""

from aiogram import Router

from richup_bot.routers import common, inline, join_requests, rich


def build_root_router() -> Router:
    """Compose feature routers in deterministic dispatch order."""
    router = Router(name="root")
    router.include_routers(
        common.router,
        rich.router,
        inline.router,
        join_requests.router,
    )
    return router
