import os
import time
from openai import OpenAI
import backend.config as config
import structlog
from prometheus_client import Counter, Histogram, Gauge

logger = structlog.get_logger()

# Prometheus metrics
REQUESTS = Counter("gpt_requests_total", "Total GPT requests", ["status"])
LATENCY = Histogram("gpt_request_latency_seconds", "GPT request latency seconds")

# New: aggregate token & cost metrics
PROMPT_TOKENS_COUNTER = Counter(
    "gpt_prompt_tokens_total", "Total prompt tokens consumed"
)
COMPLETION_TOKENS_COUNTER = Counter(
    "gpt_completion_tokens_total", "Total completion tokens generated"
)
COST_TOTAL = Counter(
    "gpt_cost_total_usd", "Total USD cost of all GPT calls"
)

# Stubbed response when GPT is disabled
_STUB = {"choices": [{"message": {"content": "[ChatGPT not called – debug mode OFF]"}}]}

def call_chat_completion(model: str, messages: list[dict]) -> dict:
    if not config.ENABLE_GPT:
        logger.info("gpt.call.stubbed", model=model)
        REQUESTS.labels(status="stubbed").inc()
        return _STUB

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    start = time.time()
    resp = client.chat.completions.create(model=model, messages=messages)
    duration = time.time() - start

    usage = getattr(resp, "usage", None)
    p = getattr(usage, "prompt_tokens", None)
    c = getattr(usage, "completion_tokens", None)
    t = getattr(usage, "total_tokens", None)

    logger.info(
        "gpt.call.success",
        model=model,
        prompt_tokens=p,
        completion_tokens=c,
        total_tokens=t,
        latency_s=duration,
    )
    REQUESTS.labels(status="success").inc()
    LATENCY.observe(duration)
    
    # update token usage counters
    PROMPT_TOKENS_COUNTER.inc(p or 0)
    COMPLETION_TOKENS_COUNTER.inc(c or 0)

    # compute & record cost:
    # prompt @ $0.0015/1K tokens, completion @ $0.0020/1K tokens
    cost = ((p or 0) / 1000) * 0.0015 + ((c or 0) / 1000) * 0.0020
    COST_TOTAL.inc(cost)


    return resp.model_dump()
