from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import json
import asyncio
import os
from datetime import datetime, timedelta

from services.ai_chat_service import AIChatService
from services.watchlist_service import WatchlistService
from api.watchlist import get_user_id_from_token

router = APIRouter(prefix="/api/ai", tags=["ai"]) 
ai_service = AIChatService()
watchlist_service = WatchlistService()

# In-memory rate limiting (replace with Redis in production)
user_request_counts = {}

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    context: Optional[Dict] = Field(default_factory=dict)
    stream: bool = Field(default=False)
    provider: Optional[str] = Field(default=None, description="Force provider: 'claude' or 'perplexity'")

class ChatResponse(BaseModel):
    content: str
    sources: Optional[List[Dict]] = None
    actions: Optional[List[Dict]] = None
    provider: str
    timestamp: datetime = Field(default_factory=datetime.now)

async def rate_limit_check(user_id: str) -> bool:
    """Check if user has exceeded rate limit"""
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Clean old entries
    user_request_counts[user_id] = [
        timestamp for timestamp in user_request_counts.get(user_id, [])
        if timestamp > hour_ago
    ]
    
    # Check limit
    request_count = len(user_request_counts.get(user_id, []))
    limit = int(os.getenv("AI_RATE_LIMIT_PER_HOUR", "20"))
    
    if request_count >= limit:
        return False
    
    # Add current request
    if user_id not in user_request_counts:
        user_request_counts[user_id] = []
    user_request_counts[user_id].append(now)
    
    return True

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: str = Depends(get_user_id_from_token)
):
    """Process AI chat query with smart routing"""
    
    # Rate limiting
    if not await rate_limit_check(current_user):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more queries."
        )
    
    # Validate query
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Get user's watchlist for context
    try:
        user_watchlist = await watchlist_service.get_user_watchlist(current_user)
        watchlist_symbols = [item["symbol"] for item in user_watchlist]
    except Exception:
        watchlist_symbols = []
    
    # Enhance context with user data
    enhanced_context = {
        **request.context,
        "watchlist": watchlist_symbols,
        "user_id": current_user,
        "timestamp": datetime.now().isoformat()
    }
    
    # Provider override if requested
    provider_override = request.provider.lower() if request.provider else None
    if provider_override not in (None, 'claude', 'perplexity'):
        raise HTTPException(status_code=400, detail="Invalid provider. Use 'claude' or 'perplexity'.")

    # Decide routing (streaming only supported for Claude path)
    route_to_perplexity = (
        provider_override == 'perplexity' if provider_override is not None else ai_service._needs_realtime_data(request.query)
    )

    # Handle streaming for Claude queries
    if request.stream and not route_to_perplexity:
        async def generate():
            try:
                async for chunk in ai_service.stream_claude_response(request.query, enhanced_context):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': True, 'content': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    # Non-streaming response
    try:
        # If forced provider, bypass smart routing
        if provider_override == 'claude':
            response = await ai_service._claude_analysis(request.query, enhanced_context)
        elif provider_override == 'perplexity':
            response = await ai_service._perplexity_search(request.query, enhanced_context)
        else:
            response = await asyncio.wait_for(
                ai_service.process_query(request.query, enhanced_context),
                timeout=ai_service.request_timeout
            )
        
        # Check if there was an error
        if response.get("error"):
            raise HTTPException(
                status_code=500,
                detail=response.get("content", "AI service error")
            )
        
        # Ensure sources is always a list, even if empty
        sources = response.get("sources", [])
        if not isinstance(sources, list):
            sources = []
            
        return ChatResponse(
            content=response.get("content", ""),
            sources=sources,
            actions=response.get("actions"),
            provider=response.get("provider", "unknown")
        )
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query processing timed out. Please try a simpler query."
        )
    except Exception as e:
        import traceback
        print(f"ERROR in AI chat endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Check health status of AI services"""
    health = await ai_service.check_health()
    
    return {
        "status": "healthy" if any(health.values()) else "unhealthy",
        "services": health,
        "rate_limit": int(os.getenv("AI_RATE_LIMIT_PER_HOUR", "20"))
    }

@router.get("/usage")
async def get_usage(current_user: str = Depends(get_user_id_from_token)):
    """Get user's AI usage statistics"""
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Get request count in last hour
    user_requests = user_request_counts.get(current_user, [])
    recent_requests = [t for t in user_requests if t > hour_ago]
    
    return {
        "requests_last_hour": len(recent_requests),
        "limit_per_hour": int(os.getenv("AI_RATE_LIMIT_PER_HOUR", "20")),
        "remaining": max(0, int(os.getenv("AI_RATE_LIMIT_PER_HOUR", "20")) - len(recent_requests))
    }
