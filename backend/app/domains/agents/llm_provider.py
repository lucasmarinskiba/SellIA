"""LLM Provider Abstraction with Fallback Support.

Provides a unified interface for OpenAI and Anthropic Claude,
with automatic fallback when the primary provider fails.
"""

import uuid
from typing import Optional, Dict, Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from app.domains.businesses.models import Business
from app.domains.subscriptions.models import UserAPIKey
from app.core.encryption import decrypt_value
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMResponse:
    """Standardized response from any LLM provider."""
    def __init__(self, content: str, model: str, provider: str, tokens_used: Optional[int] = None):
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens_used = tokens_used


class BaseLLMProvider:
    """Abstract base for LLM providers."""
    provider_name: str = "base"

    async def generate(
        self,
        messages: List[BaseMessage],
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        raise NotImplementedError


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    async def generate(
        self,
        messages: List[BaseMessage],
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = await llm.ainvoke(messages)
            return LLMResponse(
                content=response.content,
                model=model,
                provider=self.provider_name,
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return None


class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider. Free, runs on your own hardware."""
    provider_name = "ollama"

    async def generate(
        self,
        messages: List[BaseMessage],
        api_key: str,  # Not used, but kept for interface compatibility
        model: str = "llama3.1",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        from app.core.config import get_settings
        settings = get_settings()
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")

        try:
            import aiohttp

            # Convert LangChain messages to Ollama format
            ollama_messages = []
            for msg in messages:
                role = "user"
                if isinstance(msg, SystemMessage):
                    role = "system"
                elif isinstance(msg, AIMessage):
                    role = "assistant"
                ollama_messages.append({"role": role, "content": msg.content})

            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Ollama returned {resp.status}: {text}")
                        return None
                    data = await resp.json()

            content = data.get("message", {}).get("content", "")
            if not content:
                logger.error("Ollama returned empty content")
                return None

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
            )

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return None


class KimiProvider(BaseLLMProvider):
    """Moonshot AI (Kimi) provider. Uses OpenAI-compatible API."""
    provider_name = "kimi"

    async def generate(
        self,
        messages: List[BaseMessage],
        api_key: str,
        model: str = "kimi-k2-5",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = await llm.ainvoke(messages)
            return LLMResponse(
                content=response.content,
                model=model,
                provider=self.provider_name,
            )
        except Exception as e:
            logger.error(f"Kimi generation failed: {e}")
            return None


class GroqProvider(BaseLLMProvider):
    """Groq provider — free/ultra-fast Llama/Mixtral. OpenAI-compatible API."""
    provider_name = "groq"

    async def generate(
        self,
        messages: List[BaseMessage],
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        try:
            from langchain_openai import ChatOpenAI
            from app.core.config import get_settings
            base_url = get_settings().GROQ_BASE_URL.rstrip("/")
            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = await llm.ainvoke(messages)
            return LLMResponse(
                content=response.content,
                model=model,
                provider=self.provider_name,
            )
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return None


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    async def generate(
        self,
        messages: List[BaseMessage],
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = await llm.ainvoke(messages)
            return LLMResponse(
                content=response.content,
                model=model,
                provider=self.provider_name,
            )
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            return None


class FallbackProvider(BaseLLMProvider):
    """Tries Ollama first (free/local), then Groq (free/fast), then Kimi, then OpenAI, then Anthropic."""
    provider_name = "fallback"

    def __init__(self):
        self.ollama = OllamaProvider()
        self.groq = GroqProvider()
        self.kimi = KimiProvider()
        self.openai = OpenAIProvider()
        self.anthropic = AnthropicProvider()

    async def generate(
        self,
        messages: List[BaseMessage],
        ollama_available: bool = False,
        groq_key: Optional[str] = None,
        kimi_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        model: str = "llama3.1",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[LLMResponse]:
        # Try Ollama first (free, local)
        if ollama_available:
            result = await self.ollama.generate(messages, "", model, temperature, max_tokens)
            if result:
                return result
            logger.warning("Ollama failed, trying Groq fallback...")

        # Fallback to Groq (free, ultra-fast cloud)
        if groq_key:
            groq_model = model if model.startswith("llama") or model.startswith("mixtral") else "llama-3.3-70b-versatile"
            result = await self.groq.generate(messages, groq_key, groq_model, temperature, max_tokens)
            if result:
                return result
            logger.warning("Groq failed, trying Kimi fallback...")

        # Fallback to Kimi (cheapest cloud provider)
        if kimi_key:
            kimi_model = model if not model.startswith("llama") else "kimi-k2-5"
            result = await self.kimi.generate(messages, kimi_key, kimi_model, temperature, max_tokens)
            if result:
                return result
            logger.warning("Kimi failed, trying OpenAI fallback...")

        # Fallback to OpenAI
        if openai_key:
            openai_model = "gpt-4o-mini" if model.startswith("kimi") or model.startswith("llama") else model
            result = await self.openai.generate(messages, openai_key, openai_model, temperature, max_tokens)
            if result:
                return result
            logger.warning("OpenAI failed, trying Anthropic fallback...")

        # Fallback to Anthropic
        if anthropic_key:
            result = await self.anthropic.generate(messages, anthropic_key, temperature=temperature, max_tokens=max_tokens)
            if result:
                return result

        logger.error("All LLM providers (Ollama, Kimi, OpenAI, Anthropic) failed")
        return None


async def _is_ollama_available() -> bool:
    """Check if Ollama server is reachable."""
    from app.core.config import get_settings
    settings = get_settings()
    base_url = settings.OLLAMA_BASE_URL.rstrip("/")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                return resp.status == 200
    except Exception:
        return False


async def resolve_api_keys(
    db: AsyncSession,
    business_id: uuid.UUID,
) -> Dict[str, Any]:
    """Resolve API keys for a business. Returns {"kimi": key, "openai": key, "anthropic": key, "ollama": bool}."""
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()
    from app.core.config import get_settings
    env_groq = get_settings().GROQ_API_KEY
    if not business:
        return {"kimi": None, "openai": None, "anthropic": None, "groq": env_groq, "ollama": False}

    keys: Dict[str, Any] = {
        "kimi": None, "openai": None, "anthropic": None,
        "groq": env_groq,  # env fallback; per-business key overrides below
        "ollama": await _is_ollama_available(),
    }

    for provider in ["kimi", "openai", "anthropic", "groq"]:
        result = await db.execute(
            select(UserAPIKey).where(
                UserAPIKey.user_id == business.user_id,
                UserAPIKey.provider == provider,
                UserAPIKey.is_active == True,
            )
        )
        key_record = result.scalar_one_or_none()
        if key_record and key_record.api_key_fernet:
            try:
                keys[provider] = decrypt_value(key_record.api_key_fernet)
            except Exception as e:
                logger.error(f"Failed to decrypt {provider} key: {e}")

    return keys


def _inject_business_context_into_messages(
    messages: List[BaseMessage],
    business_context: Dict[str, Any],
) -> None:
    """Inject business context into the first SystemMessage, or prepend one."""
    from app.domains.agents.prompts.composer import _finalize_prompt

    # Find existing system message
    system_idx = None
    for i, msg in enumerate(messages):
        if isinstance(msg, SystemMessage):
            system_idx = i
            break

    # Build context block
    ctx_parts = []
    if business_context.get("name"):
        ctx_parts.append(f"Business Name: {business_context['name']}")
    if business_context.get("type"):
        ctx_parts.append(f"Business Type: {business_context['type']}")
    if business_context.get("enriched"):
        ctx_parts.append(f"Business Profile: {business_context['enriched']}")
    if business_context.get("prompt_adaptation"):
        ctx_parts.append(f"Adaptation: {business_context['prompt_adaptation']}")

    if not ctx_parts:
        return

    context_block = "\n\nBUSINESS CONTEXT:\n" + "\n".join(ctx_parts)

    if system_idx is not None:
        messages[system_idx] = SystemMessage(
            content=messages[system_idx].content + context_block
        )
    else:
        messages.insert(0, SystemMessage(content=context_block))


async def generate_with_fallback(
    db: AsyncSession,
    business_id: uuid.UUID,
    messages: List[BaseMessage],
    model: str = "llama3.1",
    temperature: float = 0.7,
    max_tokens: int = 1500,
    use_semantic_cache: bool = True,
    use_smart_router: bool = True,
    business_context: Optional[Dict[str, Any]] = None,
) -> Optional[LLMResponse]:
    """Generate a response using smart routing, semantic cache, and fallback.

    If business_context is not provided but business_id is given,
    automatically loads enriched BusinessContext and injects it into the system prompt.
    """
    from app.core.semantic_cache import semantic_cache
    from app.domains.agents.llm_router import route_model

    # Auto-load business context if not provided
    if business_context is None and business_id:
        try:
            from app.domains.agents.context_builder import BusinessContextBuilder
            builder = BusinessContextBuilder(db)
            business_context = await builder.build_system_prompt_context(business_id)
        except Exception as exc:
            logger.debug(f"Auto-load business_context failed: {exc}")

    # Inject business context into system prompt if available
    if business_context:
        _inject_business_context_into_messages(messages, business_context)

    # Build prompt text for cache/router
    prompt_text = "\n".join(
        f"{msg.type}: {msg.content}" if hasattr(msg, "type") else str(msg.content)
        for msg in messages
    )

    # 1. Try semantic cache
    if use_semantic_cache:
        try:
            cached = await semantic_cache.get(prompt_text)
            if cached:
                return LLMResponse(
                    content=cached,
                    model="semantic-cache",
                    provider="cache",
                    tokens_used=0,
                )
        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {e}")

    # 2. Resolve keys
    keys = await resolve_api_keys(db, business_id)

    if not keys["ollama"] and not keys["kimi"] and not keys["openai"] and not keys["anthropic"] and not keys.get("groq"):
        logger.warning("No LLM providers available (Ollama offline and no API keys configured)")
        return None

    # 3. Smart router: pick cheapest adequate model
    selected_model = model
    if use_smart_router:
        provider_name, selected_model, complexity = route_model(
            prompt_text,
            ollama_available=keys["ollama"],
            groq_available=bool(keys.get("groq")),
        )
        # Override model if router picked a different one
        if provider_name in ("ollama", "openai", "anthropic", "kimi", "groq"):
            model = selected_model

    # 4. Generate
    provider = FallbackProvider()
    response = await provider.generate(
        messages=messages,
        ollama_available=keys["ollama"],
        groq_key=keys.get("groq"),
        kimi_key=keys["kimi"],
        openai_key=keys["openai"],
        anthropic_key=keys["anthropic"],
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # 5. Cache the response
    if response and use_semantic_cache:
        try:
            await semantic_cache.set(prompt_text, response.content)
        except Exception as e:
            logger.warning(f"Semantic cache store failed: {e}")

    return response
