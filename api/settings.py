from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from db.database import get_db
from db.models import User, Config
from db.auth import get_current_user, get_current_active_admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class ConfigCreate(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    config_type: str = "string"
    category: Optional[str] = None
    is_secret: bool = False


class ConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    id: int
    key: str
    value: Optional[str]
    description: Optional[str]
    config_type: str
    category: Optional[str]
    is_secret: bool

    class Config:
        from_attributes = True


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_active_admin)
):
    """Render settings page (admin only)"""
    return FileResponse("templates/settings.html")


@router.get("/api/settings/configs", response_model=List[ConfigResponse])
async def get_all_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all configuration items"""
    result = await db.execute(select(Config))
    configs = result.scalars().all()
    return configs


@router.get("/api/settings/configs/category/{category}", response_model=List[ConfigResponse])
async def get_configs_by_category(
    category: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get configs by category"""
    result = await db.execute(select(Config).where(Config.category == category))
    configs = result.scalars().all()
    return configs


@router.post("/api/settings/configs", response_model=ConfigResponse)
async def create_config(
    config: ConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Create new config (admin only)"""
    # Check if key already exists
    result = await db.execute(select(Config).where(Config.key == config.key))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Config key already exists")

    db_config = Config(**config.dict())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.put("/api/settings/configs/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: int,
    config: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Update config (admin only)"""
    result = await db.execute(select(Config).where(Config.id == config_id))
    db_config = result.scalar_one_or_none()
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")

    if config.value is not None:
        db_config.value = config.value
    if config.description is not None:
        db_config.description = config.description

    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.delete("/api/settings/configs/{config_id}")
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Delete config (admin only)"""
    result = await db.execute(select(Config).where(Config.id == config_id))
    db_config = result.scalar_one_or_none()
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")

    await db.delete(db_config)
    await db.commit()
    return {"message": "Config deleted successfully"}


@router.post("/api/settings/init-default-configs")
async def init_default_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Initialize default configuration items"""
    default_configs = [
        # Security
        {"key": "API_PREFIX", "value": "", "description": "API prefix for security", "category": "security", "config_type": "string"},
        {"key": "AUTHORIZATION", "value": "", "description": "Authorization codes (comma separated)", "category": "security", "config_type": "string", "is_secret": True},
        {"key": "AUTH_KEY", "value": "", "description": "Auth key for private gateway", "category": "security", "config_type": "string", "is_secret": True},

        # Request
        {"key": "CHATGPT_BASE_URL", "value": "https://chatgpt.com", "description": "ChatGPT base URL", "category": "request", "config_type": "string"},
        {"key": "PROXY_URL", "value": "", "description": "Global proxy URLs (comma separated)", "category": "request", "config_type": "string"},
        {"key": "EXPORT_PROXY_URL", "value": "", "description": "Export proxy URL", "category": "request", "config_type": "string"},
        {"key": "FILE_HOST", "value": "", "description": "File host URL", "category": "request", "config_type": "string"},
        {"key": "VOICE_HOST", "value": "", "description": "Voice host URL", "category": "request", "config_type": "string"},

        # Functionality
        {"key": "HISTORY_DISABLED", "value": "true", "description": "Disable chat history", "category": "functionality", "config_type": "bool"},
        {"key": "POW_DIFFICULTY", "value": "00003a", "description": "Proof of work difficulty", "category": "functionality", "config_type": "string"},
        {"key": "RETRY_TIMES", "value": "3", "description": "Number of retries on error", "category": "functionality", "config_type": "int"},
        {"key": "CONVERSATION_ONLY", "value": "false", "description": "Use conversation endpoint only", "category": "functionality", "config_type": "bool"},
        {"key": "ENABLE_LIMIT", "value": "true", "description": "Enable rate limiting", "category": "functionality", "config_type": "bool"},
        {"key": "UPLOAD_BY_URL", "value": "false", "description": "Enable URL upload", "category": "functionality", "config_type": "bool"},
        {"key": "SCHEDULED_REFRESH", "value": "false", "description": "Enable scheduled token refresh", "category": "functionality", "config_type": "bool"},
        {"key": "RANDOM_TOKEN", "value": "true", "description": "Random token selection", "category": "functionality", "config_type": "bool"},
        {"key": "OAI_LANGUAGE", "value": "zh-CN", "description": "OpenAI language setting", "category": "functionality", "config_type": "string"},

        # Gateway
        {"key": "ENABLE_GATEWAY", "value": "false", "description": "Enable gateway mode", "category": "gateway", "config_type": "bool"},
        {"key": "AUTO_SEED", "value": "true", "description": "Enable auto seed mode", "category": "gateway", "config_type": "bool"},
        {"key": "FORCE_NO_HISTORY", "value": "false", "description": "Force disable history", "category": "gateway", "config_type": "bool"},
    ]

    created_count = 0
    for config_data in default_configs:
        result = await db.execute(select(Config).where(Config.key == config_data["key"]))
        existing = result.scalar_one_or_none()
        if not existing:
            db_config = Config(**config_data)
            db.add(db_config)
            created_count += 1

    await db.commit()
    return {"message": f"Initialized {created_count} default configs"}
