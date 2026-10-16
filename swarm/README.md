# EQwise models: one gateway for the agent swarm

An MCP server that gives Claude Code (and any other MCP client) access to
several AI models through one place: Claude, Meta Muse Spark, and optionally
Gemini, GPT or a local model. Claude stays the orchestrator; other models
are tools it can call.

```
Claude Code (orchestrator)
   ├── subagents / workflows
   └── MCP server "eqwise-models"  (swarm/server.py)
          └── LiteLLM  (swarm/litellm_config.yaml)
                ├── claude-opus / claude-sonnet / claude-haiku
                ├── muse-spark
                └── gemini / gpt / local  (optional)
```

## Tools

| Tool | What it does |
|---|---|
| `list_models` | Configured models with role, privacy level and price |
| `ask_model` | Send a question (plus optional files) to one model |
| `review_diff` | Several models review the same diff in parallel |
| `cost_report` | Spending per model per day |

## Setup (Mac)

```bash
cd eqwise-dev
python3 -m venv swarm/.venv
swarm/.venv/bin/pip install -r swarm/requirements.txt
cp swarm/models.env.example swarm/models.env
open -e swarm/models.env        # fill in your API keys
```

Then start Claude Code in this folder. It finds `.mcp.json` and asks once
whether to allow the `eqwise-models` server. Check with `/mcp`.

To use it from every project, register it globally instead:

```bash
claude mcp add --scope user eqwise-models -- \
  "$PWD/swarm/.venv/bin/python" "$PWD/swarm/server.py"
```

## Safety rules built in

- **Daily budget.** Every call is logged in `swarm/usage/usage.jsonl` with its
  cost. When `EQWISE_DAILY_BUDGET_USD` is reached, calls are refused.
- **Confidential data.** Each model has a privacy level in the config:
  `trusted`, `external` or `local`. A call with `confidential=true` is
  refused for `external` models. Muse Spark is `external` until Meta's data
  terms for your account have been checked.
- **No silent truncation.** Inputs above `EQWISE_MAX_INPUT_CHARS` are refused
  with a message instead of being cut off.
- **Keys stay private.** `swarm/models.env` is in `.gitignore` and Claude Code
  is not allowed to read it (`.claude/settings.json`).

## Muse Spark: check before use

The Muse Spark API is in public preview for US developers, with a waitlist.
Whether the endpoint speaks the OpenAI chat format is not confirmed. Once you
have access, fill `MUSE_API_BASE`, `MUSE_MODEL` and `MUSE_API_KEY` from
Meta's developer docs. Until then `muse-spark` shows as "not configured" and
`review_diff` uses only the models that are available.

## Example prompts for Claude Code

- "Use review_diff on my current changes, focus on security."
- "Ask muse-spark for a second opinion on this function, then compare it with yours."
- "Show the cost_report for this week."

## Benchmark: which model is good enough for which job

`swarm/bench.py` runs five typical EQwise tasks on every configured model and
scores them with automatic checks (no judge model to pay for):

| Task | What is checked |
|---|---|
| Dutch meta description | 140-160 characters, contains the keyword |
| JSON-LD LocalBusiness | valid JSON, schema.org, correct postcode and phone |
| WordPress PHP security review | finds prepare(), nonce, capability check, escaping |
| Search Console analysis | right query and correctly computed CTR |
| Fluid type clamp() | correct min, max, slope and constant |

```bash
swarm/.venv/bin/python swarm/bench.py --models claude-haiku,claude-sonnet,muse-spark --runs 3
```

Claude against OpenAI, tier by tier (needs `OPENAI_API_KEY` and the three
`GPT_*_MODEL` ids in `models.env`):

```bash
swarm/.venv/bin/python swarm/bench.py \
  --models claude-opus,gpt-sol,claude-sonnet,gpt-terra,claude-haiku,gpt-luna --runs 3
```

It prints score, cost, cost per score point and speed per model, and saves
the table to `swarm/usage/bench-<date>.md`. A full run of 3 models x 5 tasks x
3 runs costs a few cents. Use the result to pick the cheapest model that still
scores well per job type, then add your own tasks to `TASKS` in `bench.py`.

## Adding a model

Add an entry to `litellm_config.yaml` (examples for Gemini, GPT and Ollama
are in the file, commented out), set its key in `models.env`, and restart
Claude Code. No code changes needed.
