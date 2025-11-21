"""Database operations to replace file-based storage"""
import json
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from db.models import Token, Config, RefreshMap, SeedMap, ConversationMap, FPMap, WSSMap


# Token Operations
async def get_all_tokens(db: AsyncSession, user_id: Optional[int] = None) -> List[Token]:
    """Get all non-error tokens"""
    query = select(Token).where(Token.is_error == False)
    if user_id:
        query = query.where(Token.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_error_tokens(db: AsyncSession) -> List[Token]:
    """Get all error tokens"""
    result = await db.execute(select(Token).where(Token.is_error == True))
    return result.scalars().all()


async def add_token(db: AsyncSession, token_value: str, user_id: Optional[int] = None) -> Token:
    """Add a new token"""
    token = Token(
        token_value=token_value,
        user_id=user_id,
        is_error=False
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def mark_token_as_error(db: AsyncSession, token_value: str, error_message: str = None):
    """Mark a token as error"""
    result = await db.execute(select(Token).where(Token.token_value == token_value))
    token = result.scalar_one_or_none()
    if token:
        token.is_error = True
        token.error_message = error_message
        token.updated_at = datetime.utcnow()
        await db.commit()


async def clear_all_tokens(db: AsyncSession):
    """Clear all tokens"""
    await db.execute(delete(Token))
    await db.commit()


async def clear_error_tokens(db: AsyncSession):
    """Clear all error tokens"""
    await db.execute(delete(Token).where(Token.is_error == True))
    await db.commit()


# Config Operations
async def get_config(db: AsyncSession, key: str) -> Optional[Config]:
    """Get a single config by key"""
    result = await db.execute(select(Config).where(Config.key == key))
    return result.scalar_one_or_none()


async def get_config_value(db: AsyncSession, key: str, default: any = None) -> any:
    """Get config value, return default if not found"""
    config = await get_config(db, key)
    if not config:
        return default

    value = config.value
    if config.config_type == "bool":
        return value.lower() in ['true', '1', 't', 'y', 'yes'] if isinstance(value, str) else bool(value)
    elif config.config_type == "int":
        return int(value) if value else default
    elif config.config_type == "json":
        return json.loads(value) if value else default
    return value


async def set_config(db: AsyncSession, key: str, value: str):
    """Set or update a config value"""
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()

    if config:
        config.value = value
        config.updated_at = datetime.utcnow()
    else:
        config = Config(key=key, value=value)
        db.add(config)

    await db.commit()
    return config


async def get_all_configs(db: AsyncSession) -> List[Config]:
    """Get all configs"""
    result = await db.execute(select(Config))
    return result.scalars().all()


async def get_configs_by_category(db: AsyncSession, category: str) -> List[Config]:
    """Get configs by category"""
    result = await db.execute(select(Config).where(Config.category == category))
    return result.scalars().all()


# RefreshMap Operations
async def get_refresh_token(db: AsyncSession, access_token: str) -> Optional[str]:
    """Get refresh token by access token"""
    result = await db.execute(select(RefreshMap).where(RefreshMap.access_token == access_token))
    refresh_map = result.scalar_one_or_none()
    return refresh_map.refresh_token if refresh_map else None


async def set_refresh_token(db: AsyncSession, access_token: str, refresh_token: str):
    """Set or update refresh token mapping"""
    result = await db.execute(select(RefreshMap).where(RefreshMap.access_token == access_token))
    refresh_map = result.scalar_one_or_none()

    if refresh_map:
        refresh_map.refresh_token = refresh_token
        refresh_map.updated_at = datetime.utcnow()
    else:
        refresh_map = RefreshMap(access_token=access_token, refresh_token=refresh_token)
        db.add(refresh_map)

    await db.commit()


async def get_all_refresh_maps(db: AsyncSession) -> Dict[str, str]:
    """Get all refresh token mappings as dict"""
    result = await db.execute(select(RefreshMap))
    maps = result.scalars().all()
    return {m.access_token: m.refresh_token for m in maps}


# SeedMap Operations
async def get_seed_token(db: AsyncSession, seed: str) -> Optional[str]:
    """Get access token by seed"""
    result = await db.execute(select(SeedMap).where(SeedMap.seed_token == seed))
    seed_map = result.scalar_one_or_none()
    return seed_map.access_token if seed_map else None


async def set_seed_token(db: AsyncSession, seed: str, access_token: str):
    """Set or update seed token mapping"""
    result = await db.execute(select(SeedMap).where(SeedMap.seed_token == seed))
    seed_map = result.scalar_one_or_none()

    if seed_map:
        seed_map.access_token = access_token
        seed_map.updated_at = datetime.utcnow()
    else:
        seed_map = SeedMap(seed_token=seed, access_token=access_token)
        db.add(seed_map)

    await db.commit()


async def get_all_seed_maps(db: AsyncSession) -> Dict[str, str]:
    """Get all seed token mappings as dict"""
    result = await db.execute(select(SeedMap))
    maps = result.scalars().all()
    return {m.seed_token: m.access_token for m in maps}


async def clear_seed_maps(db: AsyncSession):
    """Clear all seed maps"""
    await db.execute(delete(SeedMap))
    await db.commit()


# ConversationMap Operations
async def get_conversation_data(db: AsyncSession, seed_token: str, conversation_id: str) -> Optional[Dict]:
    """Get conversation data"""
    result = await db.execute(
        select(ConversationMap).where(
            ConversationMap.seed_token == seed_token,
            ConversationMap.conversation_id == conversation_id
        )
    )
    conv_map = result.scalar_one_or_none()
    return conv_map.data if conv_map else None


async def set_conversation_data(db: AsyncSession, seed_token: str, conversation_id: str, data: Dict):
    """Set or update conversation data"""
    result = await db.execute(
        select(ConversationMap).where(
            ConversationMap.seed_token == seed_token,
            ConversationMap.conversation_id == conversation_id
        )
    )
    conv_map = result.scalar_one_or_none()

    if conv_map:
        conv_map.data = data
        conv_map.updated_at = datetime.utcnow()
    else:
        conv_map = ConversationMap(
            seed_token=seed_token,
            conversation_id=conversation_id,
            data=data
        )
        db.add(conv_map)

    await db.commit()


async def clear_conversation_maps(db: AsyncSession):
    """Clear all conversation maps"""
    await db.execute(delete(ConversationMap))
    await db.commit()


# FPMap Operations
async def get_fingerprint(db: AsyncSession, token_hash: str) -> Optional[Dict]:
    """Get fingerprint data by token hash"""
    result = await db.execute(select(FPMap).where(FPMap.token_hash == token_hash))
    fp_map = result.scalar_one_or_none()
    return fp_map.fingerprint_data if fp_map else None


async def set_fingerprint(db: AsyncSession, token_hash: str, fingerprint_data: Dict):
    """Set or update fingerprint data"""
    result = await db.execute(select(FPMap).where(FPMap.token_hash == token_hash))
    fp_map = result.scalar_one_or_none()

    if fp_map:
        fp_map.fingerprint_data = fingerprint_data
        fp_map.updated_at = datetime.utcnow()
    else:
        fp_map = FPMap(token_hash=token_hash, fingerprint_data=fingerprint_data)
        db.add(fp_map)

    await db.commit()


async def get_all_fingerprints(db: AsyncSession) -> Dict[str, Dict]:
    """Get all fingerprints as dict"""
    result = await db.execute(select(FPMap))
    maps = result.scalars().all()
    return {m.token_hash: m.fingerprint_data for m in maps}


# WSSMap Operations
async def get_wss_url(db: AsyncSession, access_token: str) -> Optional[str]:
    """Get WebSocket URL by access token"""
    result = await db.execute(select(WSSMap).where(WSSMap.access_token == access_token))
    wss_map = result.scalar_one_or_none()
    return wss_map.wss_url if wss_map else None


async def set_wss_url(db: AsyncSession, access_token: str, wss_url: str):
    """Set or update WebSocket URL"""
    result = await db.execute(select(WSSMap).where(WSSMap.access_token == access_token))
    wss_map = result.scalar_one_or_none()

    if wss_map:
        wss_map.wss_url = wss_url
        wss_map.updated_at = datetime.utcnow()
    else:
        wss_map = WSSMap(access_token=access_token, wss_url=wss_url)
        db.add(wss_map)

    await db.commit()


async def get_all_wss_maps(db: AsyncSession) -> Dict[str, str]:
    """Get all WebSocket mappings as dict"""
    result = await db.execute(select(WSSMap))
    maps = result.scalars().all()
    return {m.access_token: m.wss_url for m in maps}
