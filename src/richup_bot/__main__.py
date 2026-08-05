"""CLI entry point."""

import asyncio
import logging
import sys

from richup_bot.app import run_polling
from richup_bot.config import Settings, SettingsError


def run() -> None:
    """Load configuration and start the bot."""
    try:
        settings = Settings.from_env()
    except SettingsError as error:
        raise SystemExit(f"Configuration error: {error}") from error

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    asyncio.run(run_polling(settings))


if __name__ == "__main__":
    run()
