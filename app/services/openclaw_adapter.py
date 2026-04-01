"""Placeholder adapter for sending alerts to OpenClaw or other channels."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OpenClawNotifier:
    """
    Notification adapter abstraction for OpenClaw integration.

    This module is intentionally broker-agnostic and does not place trades.
    Extend this class later with:
    - webhook posting
    - chat/discord/slack message delivery
    - OpenClaw API calls
    """

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url

    def send_messages(self, messages: list[str]) -> None:
        """
        Send message payloads to a notification destination.

        Current behavior: log only (safe placeholder).
        """
        if not messages:
            logger.info("OpenClaw adapter: no messages to send.")
            return

        logger.info(
            "OpenClaw adapter placeholder invoked with %d message(s).",
            len(messages),
        )
        for message in messages:
            logger.info("OPENCLAW_MESSAGE: %s", message)

