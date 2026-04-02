"""Thin helpers around the shared user-profile watchlist storage."""

from __future__ import annotations

from app.models.user_profile import UserProfileResponse
from app.services.user_profile_service import get_user_profile_store


def get_user_watchlist(user_id: str) -> tuple[list[str], bool, UserProfileResponse]:
    """Return a user's watchlist and whether the system default is being used."""
    return get_user_profile_store().get_effective_watchlist(user_id=user_id)


def add_user_watchlist_ticker(
    user_id: str,
    ticker: str,
    display_name: str | None = None,
    last_active_source: str | None = None,
) -> UserProfileResponse:
    """Add one ticker to the shared user watchlist."""
    return get_user_profile_store().add_watchlist_ticker(
        user_id=user_id,
        ticker=ticker,
        display_name=display_name,
        last_active_source=last_active_source,
    )


def remove_user_watchlist_ticker(
    user_id: str,
    ticker: str,
    display_name: str | None = None,
    last_active_source: str | None = None,
) -> UserProfileResponse:
    """Remove one ticker from the shared user watchlist."""
    return get_user_profile_store().remove_watchlist_ticker(
        user_id=user_id,
        ticker=ticker,
        display_name=display_name,
        last_active_source=last_active_source,
    )
