"""Database-backed global state management - replaces file-based globals"""
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session_maker
from db import operations as db_ops
from utils.Logger import logger
import utils.configs as configs


class GlobalState:
    """Manages global application state using database"""

    def __init__(self):
        self._token_list_cache: List[str] = []
        self._error_token_list_cache: List[str] = []
        self._refresh_map_cache: Dict[str, str] = {}
        self._seed_map_cache: Dict[str, str] = {}
        self._conversation_map_cache: Dict[str, Dict] = {}
        self._fp_map_cache: Dict[str, Dict] = {}
        self._wss_map_cache: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize global state from database"""
        if self._initialized:
            return

        async with async_session_maker() as db:
            # Load tokens
            tokens = await db_ops.get_all_tokens(db)
            self._token_list_cache = [t.token_value for t in tokens]

            error_tokens = await db_ops.get_error_tokens(db)
            self._error_token_list_cache = [t.token_value for t in error_tokens]

            # Load maps
            self._refresh_map_cache = await db_ops.get_all_refresh_maps(db)
            self._seed_map_cache = await db_ops.get_all_seed_maps(db)
            self._fp_map_cache = await db_ops.get_all_fingerprints(db)
            self._wss_map_cache = await db_ops.get_all_wss_maps(db)

        self._initialized = True

        if self._token_list_cache:
            logger.info(f"Loaded {len(self._token_list_cache)} tokens from database")
            logger.info(f"Error tokens: {len(self._error_token_list_cache)}")
            logger.info("-" * 60)

    # Token list operations
    @property
    def token_list(self) -> List[str]:
        """Get non-error token list"""
        return self._token_list_cache

    async def add_token(self, token: str, user_id: Optional[int] = None):
        """Add a token to the list"""
        if token not in self._token_list_cache:
            async with async_session_maker() as db:
                await db_ops.add_token(db, token, user_id)
            self._token_list_cache.append(token)
            logger.info(f"Added token, total: {len(self._token_list_cache)}")

    async def remove_token(self, token: str):
        """Remove a token from the list"""
        if token in self._token_list_cache:
            self._token_list_cache.remove(token)

    async def mark_token_error(self, token: str, error_msg: str = None):
        """Mark a token as error"""
        if token not in self._error_token_list_cache:
            async with async_session_maker() as db:
                await db_ops.mark_token_as_error(db, token, error_msg)
            self._error_token_list_cache.append(token)
            if token in self._token_list_cache:
                self._token_list_cache.remove(token)

    async def clear_tokens(self):
        """Clear all tokens"""
        async with async_session_maker() as db:
            await db_ops.clear_all_tokens(db)
        self._token_list_cache.clear()
        self._error_token_list_cache.clear()

    # Error token operations
    @property
    def error_token_list(self) -> List[str]:
        """Get error token list"""
        return self._error_token_list_cache

    # Refresh map operations
    @property
    def refresh_map(self) -> Dict[str, str]:
        """Get refresh token map"""
        return self._refresh_map_cache

    async def set_refresh_token(self, access_token: str, refresh_token: str):
        """Set refresh token mapping"""
        async with async_session_maker() as db:
            await db_ops.set_refresh_token(db, access_token, refresh_token)
        self._refresh_map_cache[access_token] = refresh_token

    def get_refresh_token(self, access_token: str) -> Optional[str]:
        """Get refresh token by access token"""
        return self._refresh_map_cache.get(access_token)

    # Seed map operations
    @property
    def seed_map(self) -> Dict[str, str]:
        """Get seed token map"""
        return self._seed_map_cache

    async def set_seed_token(self, seed: str, access_token: str):
        """Set seed token mapping"""
        async with async_session_maker() as db:
            await db_ops.set_seed_token(db, seed, access_token)
        self._seed_map_cache[seed] = access_token

    def get_seed_token(self, seed: str) -> Optional[str]:
        """Get access token by seed"""
        return self._seed_map_cache.get(seed)

    async def clear_seed_maps(self):
        """Clear all seed maps"""
        async with async_session_maker() as db:
            await db_ops.clear_seed_maps(db)
        self._seed_map_cache.clear()

    # Conversation map operations
    @property
    def conversation_map(self) -> Dict[str, Dict]:
        """Get conversation map"""
        return self._conversation_map_cache

    async def set_conversation_data(self, seed_token: str, conversation_id: str, data: Dict):
        """Set conversation data"""
        key = f"{seed_token}:{conversation_id}"
        async with async_session_maker() as db:
            await db_ops.set_conversation_data(db, seed_token, conversation_id, data)
        self._conversation_map_cache[key] = data

    def get_conversation_data(self, seed_token: str, conversation_id: str) -> Optional[Dict]:
        """Get conversation data"""
        key = f"{seed_token}:{conversation_id}"
        return self._conversation_map_cache.get(key)

    async def clear_conversation_maps(self):
        """Clear all conversation maps"""
        async with async_session_maker() as db:
            await db_ops.clear_conversation_maps(db)
        self._conversation_map_cache.clear()

    # Fingerprint map operations
    @property
    def fp_map(self) -> Dict[str, Dict]:
        """Get fingerprint map"""
        return self._fp_map_cache

    async def set_fingerprint(self, token_hash: str, fp_data: Dict):
        """Set fingerprint data"""
        async with async_session_maker() as db:
            await db_ops.set_fingerprint(db, token_hash, fp_data)
        self._fp_map_cache[token_hash] = fp_data

    def get_fingerprint(self, token_hash: str) -> Optional[Dict]:
        """Get fingerprint data"""
        return self._fp_map_cache.get(token_hash)

    # WebSocket map operations
    @property
    def wss_map(self) -> Dict[str, str]:
        """Get WebSocket map"""
        return self._wss_map_cache

    async def set_wss_url(self, access_token: str, wss_url: str):
        """Set WebSocket URL"""
        async with async_session_maker() as db:
            await db_ops.set_wss_url(db, access_token, wss_url)
        self._wss_map_cache[access_token] = wss_url

    def get_wss_url(self, access_token: str) -> Optional[str]:
        """Get WebSocket URL"""
        return self._wss_map_cache.get(access_token)

    # Config operations (for runtime config access)
    async def get_config(self, key: str, default: any = None) -> any:
        """Get config value from database"""
        async with async_session_maker() as db:
            return await db_ops.get_config_value(db, key, default)


# Global instance
global_state = GlobalState()

# For backward compatibility with old code
token_list = []
error_token_list = []
refresh_map = {}
seed_map = {}
conversation_map = {}
fp_map = {}
wss_map = {}
impersonate_list = configs.impersonate_list

count = 0

# Initialize on import (will be called from app startup)
async def init_global_state():
    """Initialize global state - should be called from app startup"""
    await global_state.initialize()

    # Update backward compatibility variables
    global token_list, error_token_list, refresh_map, seed_map, conversation_map, fp_map, wss_map
    token_list = global_state.token_list
    error_token_list = global_state.error_token_list
    refresh_map = global_state.refresh_map
    seed_map = global_state.seed_map
    conversation_map = global_state.conversation_map
    fp_map = global_state.fp_map
    wss_map = global_state.wss_map
