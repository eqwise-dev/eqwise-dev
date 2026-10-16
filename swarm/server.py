#!/usr/bin/env python3
"""EQwise models: MCP server that lets an agent swarm call several AI models.

Tools:
  list_models   which models are configured, their role, privacy level and price
  ask_model     send a question (plus optional files) to one model
  review_diff   have several models review the same code change in parallel
  cost_report   spending per model per day, against the daily budget

Models come from swarm/litellm_config.yaml, API keys from swarm/models.env.
"""
import asyncio
import json
import os
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# MCP over stdio uses stdout for the protocol; LiteLLM must not print there.
os.environ.setdefault("LITELLM_LOG", "ERROR")

import litellm
import yaml
from dotenv import load_dotenv
from litellm import Router
from mcp.server.mcpserver import MCPServer

HERE = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("EQWISE_MODELS_CONFIG", HERE / "litellm_config.yaml"))
USAGE_LOG = Path(os.environ.get("EQWISE_MODELS_USAGE_LOG", HERE / "usage" / "usage.jsonl"))

load_dotenv(HERE / "models.env")
litellm.suppress_debug_info = True

DAILY_BUDGET_USD = float(os.environ.get("EQWISE_DAILY_BUDGET_USD", "5"))
DEFAULT_REVIEW_MODELS = [
    m.strip()
    for m in os.environ.get("EQWISE_REVIEW_MODELS", "claude-sonnet,muse-spark").split(",")
    if m.strip()
]
# Inputs above this size are refused instead of silently cut off.
MAX_INPUT_CHARS = int(os.environ.get("EQWISE_MAX_INPUT_CHARS", "400000"))
SAFE_PRIVACY = {"trusted", "local"}

REVIEW_SYSTEM_PROMPT = """You are a senior code reviewer. Review the diff for real defects:
bugs, security problems, data loss, broken edge cases and performance traps.
For every finding give: file and line, severity (high / medium / low), what goes
wrong in a concrete scenario, and a suggested fix. Skip style nitpicks unless
asked. If you find nothing serious, say so plainly. Be concise."""


def _resolve_env(value):
    """Replace 'os.environ/NAME' with the variable's value. Returns (value, missing_name)."""
    if isinstance(value, str) and value.startswith("os.environ/"):
        name = value.split("/", 1)[1]
        resolved = os.environ.get(name, "").strip()
        return (resolved, None) if resolved else (None, name)
    return value, None


def load_models():
    """Read the config. Returns (available, unavailable) dicts keyed by model alias."""
    config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    available, unavailable = {}, {}
    for entry in config.get("model_list") or []:
        alias = entry["model_name"]
        info = entry.get("model_info") or {}
        params, missing = {}, []
        for key, raw in (entry.get("litellm_params") or {}).items():
            value, missing_name = _resolve_env(raw)
            if missing_name:
                missing.append(missing_name)
            else:
                params[key] = value
        model = {
            "alias": alias,
            "params": params,
            "privacy": info.get("eqwise_privacy", "external"),
            "role": info.get("eqwise_role", ""),
            "input_cost": float(info.get("input_cost_per_token", 0) or 0),
            "output_cost": float(info.get("output_cost_per_token", 0) or 0),
        }
        if missing:
            model["missing_env"] = missing
            unavailable[alias] = model
        else:
            available[alias] = model
    return available, unavailable


MODELS, UNAVAILABLE = load_models()
ROUTER = (
    Router(
        model_list=[{"model_name": m["alias"], "litellm_params": m["params"]} for m in MODELS.values()],
        timeout=600,
        num_retries=2,
    )
    if MODELS
    else None
)


# ---------------------------------------------------------------- usage & budget

def _read_usage():
    if not USAGE_LOG.exists():
        return []
    rows = []
    for line in USAGE_LOG.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def spent_today() -> float:
    today = date.today().isoformat()
    return sum(r.get("cost_usd", 0) for r in _read_usage() if r.get("day") == today)


def _log_usage(alias: str, tool: str, prompt_tokens: int, completion_tokens: int, cost: float):
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "day": date.today().isoformat(),
        "model": alias,
        "tool": tool,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost, 6),
    }
    with USAGE_LOG.open("a") as f:
        f.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------- model calls

class ToolError(Exception):
    """A problem the orchestrator should see as a plain message."""


def _check_model(alias: str, confidential: bool):
    if alias in UNAVAILABLE:
        missing = ", ".join(UNAVAILABLE[alias]["missing_env"])
        raise ToolError(f"Model '{alias}' is not configured: set {missing} in swarm/models.env.")
    if alias not in MODELS:
        raise ToolError(f"Unknown model '{alias}'. Available: {', '.join(MODELS) or 'none'}.")
    if confidential and MODELS[alias]["privacy"] not in SAFE_PRIVACY:
        safe = [a for a, m in MODELS.items() if m["privacy"] in SAFE_PRIVACY]
        raise ToolError(
            f"Model '{alias}' is marked '{MODELS[alias]['privacy']}' and may not receive "
            f"confidential data. Use one of: {', '.join(safe) or 'none configured'}."
        )


def _check_budget():
    spent = spent_today()
    if spent >= DAILY_BUDGET_USD:
        raise ToolError(
            f"Daily budget reached: ${spent:.2f} of ${DAILY_BUDGET_USD:.2f} spent today. "
            "Raise EQWISE_DAILY_BUDGET_USD in swarm/models.env to continue."
        )


async def _call(alias: str, system: str | None, prompt: str, max_tokens: int, tool: str) -> str:
    text, _cost = await _call_with_cost(alias, system, prompt, max_tokens, tool)
    return text


async def _call_with_cost(
    alias: str, system: str | None, prompt: str, max_tokens: int, tool: str
) -> tuple[str, float]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = await ROUTER.acompletion(model=alias, messages=messages, max_tokens=max_tokens)

    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    model = MODELS[alias]
    cost = prompt_tokens * model["input_cost"] + completion_tokens * model["output_cost"]
    _log_usage(alias, tool, prompt_tokens, completion_tokens, cost)

    choice = response.choices[0]
    text = choice.message.content or ""
    if choice.finish_reason == "length":
        text += f"\n\n[Note: answer cut off at max_tokens={max_tokens}. Ask again with a higher limit.]"
    return text, cost


def _read_files(paths: list[str]) -> str:
    parts = []
    for raw in paths:
        path = Path(raw).expanduser()
        if not path.is_file():
            raise ToolError(f"File not found: {raw}")
        parts.append(f"<file path=\"{raw}\">\n{path.read_text(errors='replace')}\n</file>")
    return "\n\n".join(parts)


def _ensure_size(text: str, what: str):
    if len(text) > MAX_INPUT_CHARS:
        raise ToolError(
            f"{what} is {len(text):,} characters, above the limit of {MAX_INPUT_CHARS:,}. "
            "Split it into smaller parts or raise EQWISE_MAX_INPUT_CHARS."
        )


# ---------------------------------------------------------------- MCP tools

server = MCPServer(
    name="eqwise-models",
    instructions=(
        "Gives access to several AI models (Claude, Meta Muse Spark, optional others) "
        "through one gateway. Call list_models first to see what is configured. "
        "Set confidential=true whenever the input contains client data, credentials or "
        "personal data; the server then refuses models that are not trusted. "
        "Every call counts against a daily budget; check cost_report when in doubt."
    ),
)


@server.tool()
def list_models() -> str:
    """List the configured models with their role, privacy level and price per 1M tokens."""
    lines = [f"Daily budget: ${spent_today():.2f} of ${DAILY_BUDGET_USD:.2f} spent today.", ""]
    for m in MODELS.values():
        lines.append(
            f"- {m['alias']}: {m['role']} | privacy={m['privacy']} | "
            f"${m['input_cost'] * 1e6:.2f} in / ${m['output_cost'] * 1e6:.2f} out per 1M tokens"
        )
    for m in UNAVAILABLE.values():
        lines.append(f"- {m['alias']}: NOT CONFIGURED (set {', '.join(m['missing_env'])})")
    return "\n".join(lines)


@server.tool()
async def ask_model(
    model: str,
    prompt: str,
    files: list[str] | None = None,
    system: str | None = None,
    confidential: bool = False,
    max_tokens: int = 16000,
) -> str:
    """Ask one model a question.

    Args:
        model: model alias from list_models, e.g. "claude-sonnet" or "muse-spark".
        prompt: the question or task.
        files: optional local file paths whose contents are added to the prompt.
        system: optional system prompt.
        confidential: true when the input contains client or personal data.
        max_tokens: maximum length of the answer.
    """
    try:
        _check_model(model, confidential)
        _check_budget()
        full_prompt = prompt if not files else f"{_read_files(files)}\n\n{prompt}"
        _ensure_size(full_prompt, "The prompt with files")
        return await _call(model, system, full_prompt, max_tokens, "ask_model")
    except ToolError as e:
        return f"Error: {e}"
    except Exception as e:  # provider errors: show the reason, keep the server alive
        return f"Error from '{model}': {type(e).__name__}: {e}"


@server.tool()
async def review_diff(
    diff: str | None = None,
    repo_path: str | None = None,
    models: list[str] | None = None,
    focus: str | None = None,
    confidential: bool = False,
    max_tokens: int = 8000,
) -> str:
    """Have several models review the same code change in parallel.

    Different models catch different mistakes. Each model's findings are returned
    in its own section; the caller compares and merges them.

    Args:
        diff: the unified diff to review. When empty, uses `git diff HEAD` in repo_path.
        repo_path: git repository to read the diff from (default: current directory).
        models: model aliases to use (default: EQWISE_REVIEW_MODELS, e.g. claude-sonnet,muse-spark).
        focus: optional extra instruction, e.g. "security" or "WordPress hooks".
        confidential: true when the code contains client secrets or personal data.
        max_tokens: maximum length of each review.
    """
    try:
        if not diff:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=repo_path or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise ToolError(f"git diff failed: {result.stderr.strip()}")
            diff = result.stdout
        if not diff.strip():
            return "Nothing to review: the diff is empty."
        _ensure_size(diff, "The diff")

        chosen = models or [m for m in DEFAULT_REVIEW_MODELS if m in MODELS]
        if not chosen:
            raise ToolError("No review models available. Configure at least one in models.env.")
        for alias in chosen:
            _check_model(alias, confidential)
        _check_budget()
    except ToolError as e:
        return f"Error: {e}"

    prompt = (f"Extra focus: {focus}\n\n" if focus else "") + f"```diff\n{diff}\n```"
    results = await asyncio.gather(
        *(_call(alias, REVIEW_SYSTEM_PROMPT, prompt, max_tokens, "review_diff") for alias in chosen),
        return_exceptions=True,
    )
    sections = []
    for alias, result in zip(chosen, results):
        body = f"Error: {type(result).__name__}: {result}" if isinstance(result, Exception) else result
        sections.append(f"## Review by {alias}\n\n{body}")
    return "\n\n".join(sections)


@server.tool()
def cost_report(days: int = 7) -> str:
    """Show spending per model per day for the last N days."""
    since = (date.today() - timedelta(days=max(days, 1) - 1)).isoformat()
    totals: dict[str, dict[str, float]] = {}
    for row in _read_usage():
        if row.get("day", "") < since:
            continue
        per_day = totals.setdefault(row["day"], {})
        per_day[row["model"]] = per_day.get(row["model"], 0) + row.get("cost_usd", 0)
    if not totals:
        return f"No usage in the last {days} day(s)."
    lines = [f"Daily budget: ${DAILY_BUDGET_USD:.2f}", ""]
    for day in sorted(totals, reverse=True):
        per_model = ", ".join(f"{m} ${c:.4f}" for m, c in sorted(totals[day].items()))
        lines.append(f"{day}: ${sum(totals[day].values()):.4f} ({per_model})")
    return "\n".join(lines)


if __name__ == "__main__":
    server.run("stdio")
