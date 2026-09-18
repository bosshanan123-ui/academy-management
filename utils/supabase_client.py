"""
utils/supabase_client.py
Single shared Supabase client instance.
"""
from supabase import create_client, Client

from config import Config

_client: Client | None = None


def get_client() -> Client:
    """Return a lazily-initialized Supabase client."""
    global _client
    if _client is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment."
            )
        _client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    return _client


def table(name: str):
    """Shortcut: get a table query builder."""
    return get_client().table(name)