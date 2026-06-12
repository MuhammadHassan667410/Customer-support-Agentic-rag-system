"""Supabase client singleton for shared database access across the project.

This module creates exactly one Supabase client instance and exports it for
reuse by all database-dependent modules.
"""

from __future__ import annotations

import logging
from typing import Final
from urllib.parse import urlparse

from supabase import Client, create_client

from src.config import SUPABASE_SERVICE_KEY, SUPABASE_URL


logger = logging.getLogger(__name__)


def _validate_supabase_url(url: str) -> None:
    """Validate basic URL shape before client initialization.

    Args:
        url: Supabase project URL from configuration.

    Raises:
        ValueError: If URL is not an HTTP(S) URL with a host.
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError(
            "SUPABASE_URL is invalid. Expected a full URL such as "
            "'https://<project-ref>.supabase.co'."
        )


def _validate_supabase_service_key(service_key: str) -> None:
    """Validate basic service key structure before client initialization.

    Args:
        service_key: Supabase service role key from configuration.

    Raises:
        ValueError: If key shape is clearly invalid.
    """
    jwt_parts = service_key.split(".")
    if len(jwt_parts) != 3 or any(not part for part in jwt_parts):
        raise ValueError(
            "SUPABASE_SERVICE_KEY appears invalid. Expected a JWT-like key with "
            "three dot-separated segments."
        )


def _create_supabase_client() -> Client:
    """Create and return a validated Supabase client instance.

    Returns:
        A configured `supabase.Client` instance.

    Raises:
        ValueError: If configuration values are invalid.
    """
    _validate_supabase_url(SUPABASE_URL)
    _validate_supabase_service_key(SUPABASE_SERVICE_KEY)

    logger.info("Initializing Supabase client singleton.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# Module-level singleton used by the full application.
supabase: Final[Client] = _create_supabase_client()


__all__ = ["supabase"]

