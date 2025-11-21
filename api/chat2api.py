import asyncio
import types

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Request, HTTPException, Form, Security, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from starlette.background import BackgroundTask

import utils.globals as globals
from utils.db_globals import global_state
from app import app, templates, security_scheme
from chatgpt.ChatService import ChatService
from chatgpt.authorization import refresh_all_tokens
from utils.Logger import logger
from utils.configs import api_prefix, scheduled_refresh
from utils.retry import async_retry
from db.auth import get_current_user, optional_auth
from db.models import User

scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def app_start():
    if scheduled_refresh:
        scheduler.add_job(id='refresh', func=refresh_all_tokens, trigger='cron', hour=3, minute=0, day='*/2',
                          kwargs={'force_refresh': True})
        scheduler.start()
        asyncio.get_event_loop().call_later(0, lambda: asyncio.create_task(refresh_all_tokens(force_refresh=False)))


async def to_send_conversation(request_data, req_token):
    chat_service = ChatService(req_token)
    try:
        await chat_service.set_dynamic_data(request_data)
        await chat_service.get_chat_requirements()
        return chat_service
    except HTTPException as e:
        await chat_service.close_client()
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        await chat_service.close_client()
        logger.error(f"Server error, {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


async def process(request_data, req_token):
    chat_service = await to_send_conversation(request_data, req_token)
    await chat_service.prepare_send_conversation()
    res = await chat_service.send_conversation()
    return chat_service, res


@app.post(f"/{api_prefix}/v1/chat/completions" if api_prefix else "/v1/chat/completions")
async def send_conversation(request: Request, credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    req_token = credentials.credentials
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "Invalid JSON body"})
    chat_service, res = await async_retry(process, request_data, req_token)
    try:
        if isinstance(res, types.AsyncGeneratorType):
            background = BackgroundTask(chat_service.close_client)
            return StreamingResponse(res, media_type="text/event-stream", background=background)
        else:
            background = BackgroundTask(chat_service.close_client)
            return JSONResponse(res, media_type="application/json", background=background)
    except HTTPException as e:
        await chat_service.close_client()
        if e.status_code == 500:
            logger.error(f"Server error, {str(e)}")
            raise HTTPException(status_code=500, detail="Server error")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        await chat_service.close_client()
        logger.error(f"Server error, {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@app.get(f"/{api_prefix}/tokens" if api_prefix else "/tokens", response_class=HTMLResponse)
async def upload_html(request: Request, current_user: User = Depends(get_current_user)):
    """Token management page - requires authentication"""
    tokens_count = len(global_state.token_list)
    return templates.TemplateResponse("tokens.html",
                                      {"request": request, "api_prefix": api_prefix, "tokens_count": tokens_count})


@app.post(f"/{api_prefix}/tokens/upload" if api_prefix else "/tokens/upload")
async def upload_post(text: str = Form(...), current_user: User = Depends(get_current_user)):
    """Upload tokens - requires authentication"""
    lines = text.split("\n")
    added_count = 0
    for line in lines:
        if line.strip() and not line.startswith("#"):
            await global_state.add_token(line.strip(), current_user.id if not current_user.is_admin else None)
            added_count += 1

    logger.info(f"Added {added_count} tokens. Total: {len(global_state.token_list)}, Error: {len(global_state.error_token_list)}")
    tokens_count = len(global_state.token_list)
    return {"status": "success", "tokens_count": tokens_count, "added": added_count}


@app.post(f"/{api_prefix}/tokens/clear" if api_prefix else "/tokens/clear")
async def clear_tokens(current_user: User = Depends(get_current_user)):
    """Clear all tokens - requires authentication"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can clear all tokens")

    await global_state.clear_tokens()
    logger.info(f"Cleared all tokens")
    return {"status": "success", "tokens_count": 0}


@app.post(f"/{api_prefix}/tokens/error" if api_prefix else "/tokens/error")
async def error_tokens(current_user: User = Depends(get_current_user)):
    """Get error tokens list - requires authentication"""
    error_tokens_list = list(set(global_state.error_token_list))
    return {"status": "success", "error_tokens": error_tokens_list}


@app.get(f"/{api_prefix}/tokens/add/{{token}}" if api_prefix else "/tokens/add/{token}")
async def add_token(token: str, current_user: User = Depends(get_current_user)):
    """Add a single token - requires authentication"""
    if token.strip() and not token.startswith("#"):
        await global_state.add_token(token.strip(), current_user.id if not current_user.is_admin else None)

    logger.info(f"Token count: {len(global_state.token_list)}, Error token count: {len(global_state.error_token_list)}")
    tokens_count = len(global_state.token_list)
    return {"status": "success", "tokens_count": tokens_count}


@app.post(f"/{api_prefix}/seed_tokens/clear" if api_prefix else "/seed_tokens/clear")
async def clear_seed_tokens(current_user: User = Depends(get_current_user)):
    """Clear seed tokens - requires authentication"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can clear seed tokens")

    await global_state.clear_seed_maps()
    await global_state.clear_conversation_maps()
    logger.info(f"Cleared seed tokens")
    return {"status": "success", "seed_tokens_count": 0}