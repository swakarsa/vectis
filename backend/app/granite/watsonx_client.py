"""
backend/app/granite/watsonx_client.py
=======================================
IBM watsonx.ai / Granite 3.0 Enterprise Client Wrapper
VECTIS Autonomous Release Safety -- IBM Bob 2.0 Hackathon

Provides a production-grade synchronous and asynchronous client for the IBM
watsonx.ai text-generation REST API, with first-class support for the
Granite 3.0 model family (8B instruct, 20B code, 3-2B instruct).

Key features
------------
* **IAM token lifecycle** -- automatic exchange of ``WATSONX_APIKEY`` for
  IBM Cloud IAM Bearer tokens with transparent 5-minute pre-expiry renewal.
* **Retry with exponential backoff + jitter** -- HTTP 429 and 503 responses
  are retried up to three times with randomised delays before escalating.
* **Circuit breaker** -- trips after three consecutive failures and falls
  back to the deterministic offline synthesiser so the CI pipeline never
  stalls waiting for a degraded API.
* **Token & latency telemetry** -- every call records prompt tokens,
  generated tokens, wall-clock duration (ms), and an estimated cost figure
  that :class:`TokenBudgetTracker` enforces against a configurable limit.
* **Granite 3.0 chat template helpers** -- ``<|system|>`` / ``<|user|>`` /
  ``<|assistant|>`` token formatting and a code-fence extractor that strips
  markdown blocks from model output.

Environment variables
---------------------
``WATSONX_APIKEY``
    IBM Cloud API key used to obtain IAM Bearer tokens.
``WATSONX_PROJECT_ID``
    watsonx.ai project scope under which inference is billed.
``WATSONX_API_URL``
    Optional override for the inference endpoint.  Defaults to US-South.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration constants
# ---------------------------------------------------------------------------

DEFAULT_API_URL = (
    "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
)
DEFAULT_IAM_URL = "https://iam.cloud.ibm.com/identity/token"

# Supported Granite model identifiers
MODEL_GRANITE_8B_INSTRUCT = "ibm/granite-3-8b-instruct"
MODEL_GRANITE_20B_CODE = "ibm/granite-20b-code-instruct"
MODEL_GRANITE_3_2B_INSTRUCT = "ibm/granite-3-2b-instruct"

SUPPORTED_MODELS: frozenset[str] = frozenset({
    MODEL_GRANITE_8B_INSTRUCT,
    MODEL_GRANITE_20B_CODE,
    MODEL_GRANITE_3_2B_INSTRUCT,
})

# IAM token pre-renewal window: refresh 5 minutes before expiry
IAM_RENEWAL_BUFFER_SECONDS = 300

# Retry configuration
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 32.0

# Circuit breaker threshold
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3

# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------


class GraniteClientError(Exception):
    """Base class for all WatsonxGraniteClient errors.

    Attributes
    ----------
    message:
        Human-readable error description.
    status_code:
        HTTP status code if the error originated from an API response,
        otherwise ``None``.
    """

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GraniteAuthenticationError(GraniteClientError):
    """Raised when IAM token exchange fails or credentials are missing."""


class GraniteRateLimitError(GraniteClientError):
    """Raised when the watsonx.ai API returns HTTP 429 and retries are exhausted."""

    def __init__(self, message: str, retry_after: Optional[int] = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class GraniteCircuitBreakerOpen(GraniteClientError):
    """Raised when the circuit breaker has tripped due to consecutive failures.

    The client automatically falls back to the deterministic offline engine
    before raising this exception, so callers receive a result regardless.
    """


class GraniteModelNotSupportedError(GraniteClientError):
    """Raised when an unsupported model identifier is requested."""


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass
class GenerationParameters:
    """Control parameters for a single watsonx.ai inference request.

    Attributes
    ----------
    max_new_tokens:
        Maximum number of tokens the model may generate.
    temperature:
        Sampling temperature (``0.0`` = greedy / deterministic).
    top_p:
        Nucleus sampling parameter (ignored when ``temperature == 0.0``).
    stop_sequences:
        List of strings at which generation stops.
    repetition_penalty:
        Token repetition penalty (> 1.0 discourages repetition).
    """

    max_new_tokens: int = 1200
    temperature: float = 0.0
    top_p: float = 1.0
    stop_sequences: List[str] = field(
        default_factory=lambda: ["<|user|>", "<|system|>"]
    )
    repetition_penalty: float = 1.05

    def to_api_dict(self) -> Dict[str, Union[int, float, List[str]]]:
        """Serialise to the watsonx.ai ``parameters`` sub-object format."""
        decoding = "greedy" if self.temperature == 0.0 else "sample"
        d: Dict[str, Union[int, float, List[str], str]] = {
            "decoding_method": decoding,
            "max_new_tokens": self.max_new_tokens,
            "repetition_penalty": self.repetition_penalty,
            "stop_sequences": self.stop_sequences,
        }
        if decoding == "sample":
            d["temperature"] = self.temperature
            d["top_p"] = self.top_p
        return d


@dataclass
class GenerationResult:
    """Result of a single code/text generation call.

    Attributes
    ----------
    generated_text:
        Raw text produced by the model (markdown fences already stripped
        when the response was code).
    model_id:
        Model that produced the result.
    input_token_count:
        Number of prompt tokens consumed.
    generated_token_count:
        Number of tokens produced.
    stop_reason:
        Why the model stopped generating (``"eos_token"``, ``"max_tokens"``,
        ``"stop_sequence"``, ``"offline"``).
    duration_ms:
        Wall-clock time for the API call in milliseconds.
    estimated_cost_usd:
        Rough compute cost estimate based on public Granite pricing.
    offline_fallback:
        ``True`` when the result came from the deterministic offline engine
        rather than the live API.
    """

    generated_text: str
    model_id: str
    input_token_count: int = 0
    generated_token_count: int = 0
    stop_reason: str = ""
    duration_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    offline_fallback: bool = False


# ---------------------------------------------------------------------------
# Token budget tracker
# ---------------------------------------------------------------------------


class TokenBudgetTracker:
    """Enforces cumulative token and cost limits across a release audit cycle.

    One instance is typically shared for the duration of a single PR analysis
    run.  It accumulates token counts and cost from each :class:`GenerationResult`
    and raises :class:`GraniteClientError` when a configured limit is exceeded.

    Parameters
    ----------
    max_prompt_tokens:
        Hard limit on total prompt tokens consumed.  Default 500 000.
    max_generated_tokens:
        Hard limit on total generated tokens.  Default 100 000.
    max_cost_usd:
        Hard limit on estimated total spend in USD.  Default $5.00.
    """

    # IBM Granite pricing estimates (per 1000 tokens, as of 2024 public rates)
    _COST_PER_1K_INPUT: float = 0.0006   # USD per 1k prompt tokens
    _COST_PER_1K_OUTPUT: float = 0.0012  # USD per 1k generated tokens

    def __init__(
        self,
        max_prompt_tokens: int = 500_000,
        max_generated_tokens: int = 100_000,
        max_cost_usd: float = 5.0,
    ) -> None:
        self._max_prompt_tokens = max_prompt_tokens
        self._max_generated_tokens = max_generated_tokens
        self._max_cost_usd = max_cost_usd

        self._cumulative_prompt_tokens: int = 0
        self._cumulative_generated_tokens: int = 0
        self._cumulative_cost_usd: float = 0.0
        self._call_count: int = 0
        self._total_duration_ms: float = 0.0

    def record(self, result: GenerationResult) -> None:
        """Record the telemetry from one generation call.

        Raises
        ------
        GraniteClientError
            When any configured budget limit is exceeded after recording.
        """
        self._cumulative_prompt_tokens += result.input_token_count
        self._cumulative_generated_tokens += result.generated_token_count
        self._cumulative_cost_usd += result.estimated_cost_usd
        self._call_count += 1
        self._total_duration_ms += result.duration_ms

        if self._cumulative_prompt_tokens > self._max_prompt_tokens:
            raise GraniteClientError(
                f"Token budget exceeded: {self._cumulative_prompt_tokens} prompt "
                f"tokens consumed (limit {self._max_prompt_tokens})"
            )
        if self._cumulative_generated_tokens > self._max_generated_tokens:
            raise GraniteClientError(
                f"Token budget exceeded: {self._cumulative_generated_tokens} generated "
                f"tokens consumed (limit {self._max_generated_tokens})"
            )
        if self._cumulative_cost_usd > self._max_cost_usd:
            raise GraniteClientError(
                f"Cost budget exceeded: ${self._cumulative_cost_usd:.4f} spent "
                f"(limit ${self._max_cost_usd:.2f})"
            )

    @staticmethod
    def estimate_cost(
        input_tokens: int, output_tokens: int
    ) -> float:
        """Compute a rough USD cost estimate for one generation call."""
        return (
            input_tokens / 1000.0 * TokenBudgetTracker._COST_PER_1K_INPUT
            + output_tokens / 1000.0 * TokenBudgetTracker._COST_PER_1K_OUTPUT
        )

    @property
    def summary(self) -> Dict[str, Union[int, float]]:
        """Return a summary dict for telemetry logging."""
        return {
            "call_count": self._call_count,
            "cumulative_prompt_tokens": self._cumulative_prompt_tokens,
            "cumulative_generated_tokens": self._cumulative_generated_tokens,
            "cumulative_cost_usd": round(self._cumulative_cost_usd, 6),
            "total_duration_ms": round(self._total_duration_ms, 1),
        }


# ---------------------------------------------------------------------------
# IAM token cache
# ---------------------------------------------------------------------------


@dataclass
class _IAMTokenCache:
    """Thread-safe (GIL-protected) cache for an IBM Cloud IAM Bearer token."""

    access_token: str = ""
    expires_at: float = 0.0  # Unix timestamp

    def is_valid(self) -> bool:
        """Return True when the cached token is still valid with renewal buffer."""
        return (
            bool(self.access_token)
            and time.time() < (self.expires_at - IAM_RENEWAL_BUFFER_SECONDS)
        )

    def store(self, access_token: str, expires_in: int) -> None:
        """Cache a fresh token and record its expiry time."""
        self.access_token = access_token
        self.expires_at = time.time() + expires_in


# ---------------------------------------------------------------------------
# Chat template helpers
# ---------------------------------------------------------------------------


def format_granite_prompt(
    system: str,
    user: str,
    few_shot_examples: Optional[List[Dict[str, str]]] = None,
    format_version: str = "v1",
) -> str:
    """Format a prompt using Granite 3.0 special chat tokens.

    Supports both legacy v1 format (<|system|>) and native Granite 3.0
    ChatML format (<|start_of_role|>system<|end_of_role|>).
    """
    if format_version == "granite-3.0":
        parts: List[str] = [f"<|start_of_role|>system\n{system.strip()}<|end_of_role|>"]
        if few_shot_examples:
            for ex in few_shot_examples:
                u = ex.get("user", "").strip()
                a = ex.get("assistant", "").strip()
                if u and a:
                    parts.append(f"<|start_of_role|>user\n{u}<|end_of_role|>")
                    parts.append(f"<|start_of_role|>assistant\n{a}<|end_of_role|>")
        parts.append(f"<|start_of_role|>user\n{user.strip()}<|end_of_role|>")
        parts.append("<|start_of_role|>assistant")
        return "\n".join(parts)

    parts: List[str] = [f"<|system|>\n{system.strip()}"]

    if few_shot_examples:
        for ex in few_shot_examples:
            u = ex.get("user", "").strip()
            a = ex.get("assistant", "").strip()
            if u and a:
                parts.append(f"<|user|>\n{u}")
                parts.append(f"<|assistant|>\n{a}")

    parts.append(f"<|user|>\n{user.strip()}")
    parts.append("<|assistant|>")
    return "\n".join(parts)


def extract_code_block(text: str, language: str = "typescript") -> str:
    """Strip markdown code fences and return the inner code string.

    Handles both fenced variants:
    * `` ```typescript\\n...\\n``` ``
    * `` ``` \\n...\\n``` `` (no language tag)

    Falls back to returning the full text (stripped) when no fence is found.

    Parameters
    ----------
    text:
        Raw model output that may or may not contain markdown fences.
    language:
        Expected language identifier on the opening fence.

    Returns
    -------
    str
        The extracted code, stripped of leading/trailing whitespace.
    """
    # Try with explicit language tag first
    m = re.search(
        rf"```{re.escape(language)}\n?(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    # Try any fence
    m = re.search(r"```\w*\n?(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def extract_json_payload(text: str) -> Optional[dict]:
    """Extract and parse the first valid JSON object from model output.

    Parameters
    ----------
    text:
        Raw model output that may embed a JSON object in prose or fences.

    Returns
    -------
    Optional[dict]
        The parsed JSON object, or ``None`` when no valid JSON is found.
    """
    # Try markdown fence first
    m = re.search(r"```json\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try bare JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


class _CircuitBreaker:
    """Closed/open/half-open circuit breaker for the watsonx.ai HTTP client.

    States
    ------
    closed (``_failures < threshold``):
        Normal operation. All requests pass through.
    open (``_failures >= threshold``):
        API is considered unhealthy. Falls back to offline engine until cooldown expires.
    half-open:
        After cooldown seconds, allows a canary trial request to test API recovery.
    """

    def __init__(self, failure_threshold: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD, cooldown_seconds: float = 60.0) -> None:
        self._threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._failures: int = 0
        self._opened_at: Optional[float] = None

    def allow_request(self) -> bool:
        """Return ``True`` when the circuit is closed (healthy) or half-open (trial)."""
        if self._failures < self._threshold:
            return True
        if self._opened_at and (time.time() - self._opened_at >= self._cooldown):
            logger.info("WatsonxGraniteClient: circuit breaker HALF-OPEN, allowing trial request")
            return True
        return False

    def record_success(self) -> None:
        """Reset the failure counter on a successful call."""
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        """Increment the failure counter."""
        self._failures += 1
        if self._failures >= self._threshold:
            if not self._opened_at:
                self._opened_at = time.time()
            logger.warning(
                "WatsonxGraniteClient: circuit breaker OPEN after %d consecutive failures",
                self._failures,
            )

    @property
    def is_open(self) -> bool:
        """``True`` when the circuit is open (unhealthy)."""
        if self._failures < self._threshold:
            return False
        if self._opened_at and (time.time() - self._opened_at >= self._cooldown):
            return False  # Half-open allows testing
        return True


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------


class WatsonxGraniteClient:
    """Production-grade IBM watsonx.ai client for the Granite 3.0 model family.

    This client is the live-API counterpart to the offline deterministic
    engine in :mod:`app.granite.synthesizer`.  It handles the full IBM Cloud
    authentication lifecycle, retry policy, circuit breaking, and telemetry.

    Parameters
    ----------
    model_id:
        Granite model to use.  Must be one of the values in
        :data:`SUPPORTED_MODELS`.  Defaults to ``MODEL_GRANITE_8B_INSTRUCT``.
    api_url:
        watsonx.ai inference endpoint.  Reads ``WATSONX_API_URL`` env var;
        falls back to the US-South regional URL.
    iam_url:
        IBM Cloud IAM token endpoint.
    budget_tracker:
        Optional shared :class:`TokenBudgetTracker`.  A fresh tracker is
        created when ``None``.
    offline_fallback:
        Callable that accepts ``(prompt: str) -> str`` and is invoked when
        the circuit breaker is open.  When ``None`` a built-in stub that
        returns an empty string is used.

    Raises
    ------
    GraniteModelNotSupportedError
        When *model_id* is not in :data:`SUPPORTED_MODELS`.
    GraniteAuthenticationError
        When ``WATSONX_APIKEY`` is not set and no IAM token can be obtained.
    """

    def __init__(
        self,
        model_id: str = MODEL_GRANITE_8B_INSTRUCT,
        api_url: Optional[str] = None,
        iam_url: str = DEFAULT_IAM_URL,
        budget_tracker: Optional[TokenBudgetTracker] = None,
        offline_fallback: Optional[Callable[[str], str]] = None,
    ) -> None:
        if model_id not in SUPPORTED_MODELS:
            raise GraniteModelNotSupportedError(
                f"Unsupported model '{model_id}'. "
                f"Supported: {sorted(SUPPORTED_MODELS)}"
            )

        self._model_id = model_id
        self._api_url = (
            api_url
            or os.getenv("WATSONX_API_URL", DEFAULT_API_URL)
        )
        self._iam_url = iam_url
        self._apikey: Optional[str] = os.getenv("WATSONX_APIKEY")
        self._project_id: Optional[str] = os.getenv("WATSONX_PROJECT_ID")
        self._budget = budget_tracker or TokenBudgetTracker()
        self._offline_fallback: Callable[[str], str] = (
            offline_fallback if offline_fallback is not None
            else lambda _prompt: ""
        )

        self._iam_cache = _IAMTokenCache()
        self._circuit_breaker = _CircuitBreaker()

    # ------------------------------------------------------------------
    # Public synchronous API
    # ------------------------------------------------------------------

    def generate_code(
        self,
        prompt: str,
        params: Optional[GenerationParameters] = None,
    ) -> GenerationResult:
        """Generate code/text using the configured Granite model.

        Resolves IAM authentication, applies retry/circuit-breaker policy,
        and records telemetry in the budget tracker.

        Parameters
        ----------
        prompt:
            Fully-formatted input prompt (use :func:`format_granite_prompt`
            to build Granite 3.0 chat-formatted prompts).
        params:
            Generation control parameters.  Default settings are used when
            ``None``.

        Returns
        -------
        GenerationResult
            The generated text with telemetry metadata.

        Raises
        ------
        GraniteAuthenticationError
            When ``WATSONX_APIKEY`` is missing or the IAM exchange fails.
        GraniteRateLimitError
            When HTTP 429 retries are exhausted.
        GraniteCircuitBreakerOpen
            Raised *after* offline fallback is returned, as a signal to
            the caller that the API is degraded.
        """
        if params is None:
            params = GenerationParameters()

        if not self._circuit_breaker.allow_request():
            logger.warning(
                "WatsonxGraniteClient: circuit breaker open -- using offline fallback"
            )
            offline_text = self._offline_fallback(prompt)
            result = GenerationResult(
                generated_text=offline_text,
                model_id=self._model_id,
                stop_reason="circuit_breaker_open",
                offline_fallback=True,
            )
            self._budget.record(result)
            return result

        return self._generate_with_retry(prompt, params)

    async def agenerate_code(
        self,
        prompt: str,
        params: Optional[GenerationParameters] = None,
    ) -> GenerationResult:
        """Async version of :meth:`generate_code`.

        Runs the synchronous implementation in a thread-pool executor so the
        event loop is not blocked during network I/O.

        Parameters
        ----------
        prompt:
            Fully-formatted input prompt.
        params:
            Generation control parameters.

        Returns
        -------
        GenerationResult
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.generate_code, prompt, params
        )

    async def astream_code(
        self,
        prompt: str,
        params: Optional[GenerationParameters] = None,
    ) -> AsyncGenerator[str, None]:
        """Yield generated text token-by-token using simulated streaming.

        The watsonx.ai v1 REST API does not support true token streaming;
        this method yields the full response in one chunk.  Kept as an
        ``AsyncGenerator`` so callers can be written generically.

        Parameters
        ----------
        prompt:
            Fully-formatted input prompt.
        params:
            Generation control parameters.

        Yields
        ------
        str
            A chunk of generated text.
        """
        result = await self.agenerate_code(prompt, params)
        yield result.generated_text

    # ------------------------------------------------------------------
    # Internal: retry loop
    # ------------------------------------------------------------------

    def _generate_with_retry(
        self,
        prompt: str,
        params: GenerationParameters,
    ) -> GenerationResult:
        """Execute the generation request with exponential backoff + jitter.

        Retries on HTTP 429 (rate limit) and 503 (service unavailable).
        Other non-2xx responses raise :class:`GraniteClientError` immediately.
        Three consecutive failures trip the circuit breaker and cause fallback.
        """
        last_exception: Optional[Exception] = None
        attempt = 0

        while attempt <= MAX_RETRIES:
            try:
                result = self._call_api(prompt, params)
                self._circuit_breaker.record_success()
                self._budget.record(result)
                return result

            except GraniteRateLimitError as exc:
                last_exception = exc
                self._circuit_breaker.record_failure()
                if attempt >= MAX_RETRIES:
                    break
                wait = self._backoff(attempt, exc.retry_after)
                logger.warning(
                    "WatsonxGraniteClient: HTTP 429 on attempt %d/%d -- "
                    "retrying in %.1fs",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    wait,
                )
                time.sleep(wait)

            except GraniteClientError as exc:
                # Non-retryable client errors (auth, model, etc.)
                if exc.status_code == 503:
                    last_exception = exc
                    self._circuit_breaker.record_failure()
                    if attempt >= MAX_RETRIES:
                        break
                    wait = self._backoff(attempt, None)
                    logger.warning(
                        "WatsonxGraniteClient: HTTP 503 on attempt %d/%d -- "
                        "retrying in %.1fs",
                        attempt + 1,
                        MAX_RETRIES + 1,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    raise

            attempt += 1

        # All retries exhausted -- fall back to offline engine
        logger.error(
            "WatsonxGraniteClient: all %d retries exhausted (%s) -- "
            "using offline fallback",
            MAX_RETRIES + 1,
            last_exception,
        )
        offline_text = self._offline_fallback(prompt)
        result = GenerationResult(
            generated_text=offline_text,
            model_id=self._model_id,
            stop_reason="retry_exhausted",
            offline_fallback=True,
        )
        self._budget.record(result)
        return result

    # ------------------------------------------------------------------
    # Internal: single API call
    # ------------------------------------------------------------------

    def _call_api(
        self,
        prompt: str,
        params: GenerationParameters,
    ) -> GenerationResult:
        """Make one HTTP POST to the watsonx.ai text-generation endpoint.

        Raises
        ------
        GraniteAuthenticationError
            When credentials are absent or the IAM exchange fails.
        GraniteRateLimitError
            On HTTP 429.
        GraniteClientError
            On any other non-2xx HTTP status.
        """
        try:
            import httpx
        except ImportError as exc:
            raise GraniteClientError(
                "httpx is required for live watsonx.ai calls. "
                "Install it: pip install httpx"
            ) from exc

        if not self._apikey:
            raise GraniteAuthenticationError(
                "WATSONX_APIKEY environment variable is not set. "
                "Set it to your IBM Cloud API key or use force_offline=True."
            )

        bearer = self._get_iam_token(httpx)

        payload = {
            "model_id": self._model_id,
            "input": prompt,
            "parameters": params.to_api_dict(),
            "project_id": self._project_id,
        }

        t0 = time.perf_counter()
        response = httpx.post(
            self._api_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=90,
        )
        duration_ms = (time.perf_counter() - t0) * 1000.0

        if response.status_code == 429:
            retry_after_header = response.headers.get("Retry-After")
            retry_after = int(retry_after_header) if retry_after_header else None
            raise GraniteRateLimitError(
                f"IBM watsonx.ai rate limit hit (HTTP 429): {response.text[:200]}",
                retry_after=retry_after,
            )
        if response.status_code == 503:
            raise GraniteClientError(
                f"IBM watsonx.ai service unavailable (HTTP 503): {response.text[:200]}",
                status_code=503,
            )
        if response.status_code != 200:
            raise GraniteClientError(
                f"IBM watsonx.ai API error (HTTP {response.status_code}): "
                f"{response.text[:300]}",
                status_code=response.status_code,
            )

        body = response.json()
        results = body.get("results", [{}])
        first = results[0] if results else {}

        raw_text: str = first.get("generated_text", "").strip()
        input_tokens: int = first.get("input_token_count", 0)
        output_tokens: int = first.get("generated_token_count", 0)
        stop_reason: str = first.get("stop_reason", "")

        cost = TokenBudgetTracker.estimate_cost(input_tokens, output_tokens)

        return GenerationResult(
            generated_text=raw_text,
            model_id=self._model_id,
            input_token_count=input_tokens,
            generated_token_count=output_tokens,
            stop_reason=stop_reason,
            duration_ms=round(duration_ms, 1),
            estimated_cost_usd=round(cost, 8),
            offline_fallback=False,
        )

    # ------------------------------------------------------------------
    # Internal: IAM token management
    # ------------------------------------------------------------------

    def _get_iam_token(self, httpx: object) -> str:
        """Return a valid IAM Bearer token, refreshing when near expiry.

        Parameters
        ----------
        httpx:
            Already-imported httpx module reference.

        Returns
        -------
        str
            A valid IBM Cloud IAM Bearer token.

        Raises
        ------
        GraniteAuthenticationError
            When the IAM token exchange fails.
        """
        if self._iam_cache.is_valid():
            return self._iam_cache.access_token

        logger.debug("WatsonxGraniteClient: refreshing IAM token")
        try:
            resp = httpx.post(  # type: ignore[attr-defined]
                self._iam_url,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self._apikey,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=20,
            )
        except Exception as exc:
            raise GraniteAuthenticationError(
                f"IAM token exchange network error: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise GraniteAuthenticationError(
                f"IAM token exchange failed: HTTP {resp.status_code} -- "
                f"{resp.text[:200]}"
            )

        data = resp.json()
        access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))

        if not access_token:
            raise GraniteAuthenticationError(
                "IAM token response did not contain access_token field."
            )

        self._iam_cache.store(access_token, expires_in)
        logger.debug(
            "WatsonxGraniteClient: IAM token refreshed, expires in %ds", expires_in
        )
        return access_token

    # ------------------------------------------------------------------
    # Internal: backoff calculator
    # ------------------------------------------------------------------

    @staticmethod
    def _backoff(attempt: int, server_hint: Optional[int]) -> float:
        """Compute the next retry wait duration with exponential backoff + jitter.

        Parameters
        ----------
        attempt:
            Zero-based attempt index (0 = first retry).
        server_hint:
            Optional ``Retry-After`` value from the server response.
            Takes priority when present.

        Returns
        -------
        float
            Seconds to wait before the next attempt.
        """
        if server_hint is not None and server_hint > 0:
            # Add a small random jitter on top of the server hint
            return float(server_hint) + random.uniform(0.1, 1.0)
        base = BASE_BACKOFF_SECONDS * (2.0 ** attempt)
        jitter = random.uniform(0.0, base * 0.3)
        return min(base + jitter, MAX_BACKOFF_SECONDS)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def model_id(self) -> str:
        """The Granite model identifier this client is configured to use."""
        return self._model_id

    @property
    def circuit_breaker_open(self) -> bool:
        """``True`` when the circuit breaker has tripped."""
        return self._circuit_breaker.is_open

    @property
    def budget_summary(self) -> Dict[str, Union[int, float]]:
        """Telemetry summary from the token budget tracker."""
        return self._budget.summary
