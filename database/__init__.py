"""Database module for managing game data storage."""

from .db import (
    init_database,
    create_account,
    username_exists,
    verify_login,
    get_all_cards,
    get_cards_by_type,
    get_card_by_id,
    get_available_cards,
    get_user_profile,
    update_user_password,
)

__all__ = [
    "init_database",
    "create_account",
    "username_exists",
    "verify_login",
    "get_all_cards",
    "get_cards_by_type",
    "get_card_by_id",
    "get_available_cards",
    "get_user_profile",
    "update_user_password",
]

