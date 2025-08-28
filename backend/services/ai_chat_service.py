import os
import asyncio
import json
import hashlib
import logging
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
import httpx
from anthropic import AsyncAnthropic
import redis.asyncio as redis
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AIChatService:
    def __init__(self):
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.redis_client = None
        self.cache_ttl = int(os.getenv("AI_CACHE_TTL_SECONDS", "300"))
        self.request_timeout = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
        
        # AI Model Configuration
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.perplexity_model = os.getenv("PERPLEXITY_MODEL", "sonar")
        
        # Initialize Anthropic client
        if self.anthropic_api_key and self.anthropic_api_key != "your_claude_api_key_here":
            self.claude = AsyncAnthropic(api_key=self.anthropic_api_key)
        else:
            self.claude = None
            
        # Initialize Redis
        self._init_redis()
        
    def _init_redis(self):
        """Initialize Redis connection"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def process_query(self, query: str, user_context: dict) -> Dict:
        """Process user query with smart routing"""
        # Check cache first
        cache_key = self._generate_cache_key(query, user_context)
        if self.redis_client:
            try:
                cached_response = await self.redis_client.get(cache_key)
                if cached_response:
                    return json.loads(cached_response)
            except Exception:
                pass
        
        # Route query to appropriate service
        if self._needs_realtime_data(query):
            response = await self._perplexity_search(query, user_context)
        else:
            response = await self._claude_analysis(query, user_context)
        
        # Cache response
        if self.redis_client and response:
            try:
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(response)
                )
            except Exception:
                pass
        
        return response
    
    def _needs_realtime_data(self, query: str) -> bool:
        """Detect if query needs current market information"""
        query_lower = query.lower()
        
        # Real-time keywords
        realtime_keywords = [
            "today", "now", "current", "latest", "breaking",
            "why did", "what happened", "news", "just",
            "jumped", "fell", "dropped", "surged", "moved",
            "yesterday", "this week", "recent", "happening"
        ]
        
        # Analysis keywords (use Claude)
        analysis_keywords = [
            "analyze", "compare", "strategy", "portfolio",
            "fundamental", "technical analysis", "valuation",
            "should i", "would you", "recommend", "advice",
            "evaluate", "assessment", "review", "explain"
        ]
        
        # Check for analysis keywords first (higher priority)
        if any(keyword in query_lower for keyword in analysis_keywords):
            logger.debug("AI routing: matched analysis keywords -> Claude")
            return False
            
        # Check for real-time keywords
        if any(keyword in query_lower for keyword in realtime_keywords):
            logger.debug("AI routing: matched real-time keywords -> Perplexity")
            return True
            
        # Default to Perplexity for general queries
        logger.debug("AI routing: default -> Perplexity")
        return True
    
    async def _perplexity_search(self, query: str, context: dict) -> Dict:
        """Use Perplexity API for real-time market data"""
        if not self.perplexity_api_key or self.perplexity_api_key == "your_perplexity_api_key_here":
            return {
                "content": "Perplexity API key not configured. Please add your API key to use real-time market search.",
                "error": True
            }
        
        # Enhance query with financial context
        symbols = context.get("watchlist", [])
        enhanced_query = f"{query}"
        if symbols:
            enhanced_query += f" (Context: User is tracking {', '.join(symbols[:5])})"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.perplexity_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial market analyst. Provide accurate, real-time market information with sources. Focus on facts and cite sources."
                            },
                            {
                                "role": "user",
                                "content": enhanced_query
                            }
                        ],
                        "temperature": 0.1
                    },
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Debug: Log the response structure
                    try:
                        logger.debug(f"Perplexity response keys: {list(data.keys())}")
                        if "choices" in data and len(data["choices"]) > 0:
                            logger.debug(f"Perplexity choice keys: {list(data['choices'][0].keys())}")
                    except Exception:
                        pass
                    
                    message = data["choices"][0]["message"]["content"]
                    
                    # Extract actions from response
                    actions = self._extract_actions_from_content(message, context)
                    
                    # Extract citations if available
                    citations = []
                    
                    # Perplexity returns citations at the top level
                    raw_citations = data.get("citations", [])
                    
                    # Convert citations to proper format
                    import re
                    for citation in raw_citations:
                        if isinstance(citation, str):
                            # Extract domain name for title
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', citation)
                            title = domain_match.group(1) if domain_match else "Source"
                            
                            citations.append({
                                "title": title,
                                "url": citation
                            })
                        elif isinstance(citation, dict):
                            citations.append(citation)
                    
                    return {
                        "content": message,
                        "sources": citations,
                        "actions": actions,
                        "provider": "perplexity"
                    }
                else:
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = f" - {error_data.get('error', {}).get('message', response.text)}"
                    except:
                        error_detail = f" - {response.text}"
                    
                    return {
                        "content": f"Error from Perplexity API: {response.status_code}{error_detail}",
                        "error": True
                    }
                    
            except asyncio.TimeoutError:
                return {
                    "content": "Request timed out. Please try again.",
                    "error": True
                }
            except Exception as e:
                return {
                    "content": f"Error connecting to Perplexity: {str(e)}",
                    "error": True
                }
    
    async def _claude_analysis(self, query: str, context: dict) -> Dict:
        """Use Claude for complex analysis"""
        if not self.claude:
            return {
                "content": "Claude API key not configured. Please add your Anthropic API key for advanced analysis.",
                "error": True
            }
        
        # Build context-aware system prompt
        system_prompt = self._build_analysis_prompt(context)
        
        try:
            # Create streaming response
            stream = await self.claude.messages.create(
                model=self.claude_model,
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                stream=True
            )
            
            # Collect full response for action extraction
            full_content = ""
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    full_content += chunk.delta.text
            
            # Extract actions
            actions = self._extract_actions_from_content(full_content, context)
            
            return {
                "content": full_content,
                "actions": actions,
                "provider": "claude"
            }
            
        except Exception as e:
            return {
                "content": f"Error with Claude API: {str(e)}",
                "error": True
            }
    
    async def stream_claude_response(self, query: str, context: dict) -> AsyncGenerator[str, None]:
        """Stream Claude response for real-time display"""
        if not self.claude:
            yield json.dumps({
                "error": True,
                "content": "Claude API not configured"
            })
            return
        
        system_prompt = self._build_analysis_prompt(context)
        
        try:
            stream = await self.claude.messages.create(
                model=self.claude_model,
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": query}],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield json.dumps({
                        "delta": chunk.delta.text,
                        "provider": "claude"
                    })
                    
        except Exception as e:
            yield json.dumps({
                "error": True,
                "content": f"Streaming error: {str(e)}"
            })
    
    def _build_analysis_prompt(self, context: dict) -> str:
        """Build context-aware prompt for Claude"""
        watchlist = context.get("watchlist", [])
        current_view = context.get("current_view", "dashboard")
        
        prompt = """You are an expert financial analyst assistant integrated into a trading dashboard. 
        Provide detailed, actionable analysis based on the user's query.
        
        User Context:"""
        
        if watchlist:
            prompt += f"\n- Watchlist: {', '.join(watchlist)}"
        
        prompt += f"\n- Current view: {current_view}"
        prompt += "\n\nProvide analysis that is:"
        prompt += "\n- Data-driven and specific"
        prompt += "\n- Actionable with clear next steps"
        prompt += "\n- Relevant to the user's portfolio"
        
        return prompt
    
    def _extract_actions_from_content(self, content: str, context: dict) -> List[Dict]:
        """Extract actionable items from AI response"""
        actions = []
        content_lower = content.lower()
        
        # Extract mentioned symbols
        import re
        symbols = re.findall(r'\b[A-Z]{1,5}\b', content)
        watchlist = context.get("watchlist", [])
        
        for symbol in symbols:
            if len(symbol) >= 2 and symbol not in watchlist:
                # Check if it's likely a stock symbol (not a common word)
                if symbol not in ["AI", "CEO", "IPO", "ETF", "NYSE", "NASDAQ", "FDA", "SEC"]:
                    actions.append({
                        "type": "add_to_watchlist",
                        "symbol": symbol,
                        "label": f"Add {symbol} to watchlist"
                    })
        
        # Add view technical analysis action if analysis is mentioned
        if "technical" in content_lower or "rsi" in content_lower or "macd" in content_lower:
            for symbol in symbols[:3]:  # Limit to first 3 symbols
                actions.append({
                    "type": "view_technical",
                    "symbol": symbol,
                    "label": f"View {symbol} technicals"
                })
        
        return actions[:5]  # Limit total actions to 5
    
    def _generate_cache_key(self, query: str, context: dict) -> str:
        """Generate cache key for query"""
        # Include query and basic context in cache key
        cache_data = {
            "query": query,
            "watchlist": sorted(context.get("watchlist", [])),
            "view": context.get("current_view", "")
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"ai_chat:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    async def check_health(self) -> Dict[str, bool]:
        """Check health of AI services"""
        health = {
            "perplexity": bool(self.perplexity_api_key and self.perplexity_api_key != "your_perplexity_api_key_here"),
            "claude": bool(self.claude),
            "redis": False
        }
        
        # Check Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis"] = True
            except Exception:
                pass
        
        return health
