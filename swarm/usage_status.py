#!/usr/bin/env python3
"""Keep track of your Claude subscription usage and say when to offload work.

Claude Code passes your 5-hour and weekly usage to the status line. This
script has two modes:

  statusline  Reads that JSON on stdin, saves it to ~/.claude/eqwise-usage.json
              and prints a short status line, e.g. "Week 41% (pace 35%) | 5h 23%".
  hook        For a UserPromptSubmit hook: reads the saved file and, only when
              usage runs ahead of pace or past a threshold, adds one short
              factual line to Claude's context. Prints nothing otherwise.

The MCP server (server.py) imports this module for its usage_status tool.

Thresholds (environment variables, optional):
  EQWISE_OFFLOAD_AT   weekly % from which bulk work is offloaded, unless usage
                      is still behind an even pace (default 70)
  EQWISE_CRITICAL_AT  weekly % from which only planning/review stays on Claude (default 90)
  EQWISE_PACE_MARGIN  points ahead of an even pace that count as "too fast" (default 10)
"""
import json
import os
import sys
import time
from pathlib import Path

USAGE_FILE = Path(os.environ.get("EQWISE_USAGE_FILE", Path.home() / ".claude" / "eqwise-usage.json"))
WEEK_SECONDS = 7 * 24 * 3600
STALE_SECONDS = 6 * 3600

OFFLOAD_AT = float(os.environ.get("EQWISE_OFFLOAD_AT", "70"))
CRITICAL_AT = float(os.environ.get("EQWISE_CRITICAL_AT", "90"))
PACE_MARGIN = float(os.environ.get("EQWISE_PACE_MARGIN", "10"))


def save(statusline_input: dict) -> dict | None:
    limits = statusline_input.get("rate_limits") or {}
    if not limits.get("seven_day") and not limits.get("five_hour"):
        return None  # not on a subscription, or no API response yet
    record = {"saved_at": int(time.time()), "rate_limits": limits}
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = USAGE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(record))
    tmp.replace(USAGE_FILE)  # atomic, several sessions may write
    return record


def load() -> dict | None:
    try:
        record = json.loads(USAGE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - record.get("saved_at", 0) > STALE_SECONDS:
        return None
    return record


def assess(record: dict | None, now: float | None = None) -> dict:
    """Turn saved usage into a level: unknown, normal, ahead, offload or critical."""
    now = now or time.time()
    if not record:
        return {"level": "unknown"}
    limits = record["rate_limits"]
    week = limits.get("seven_day") or {}
    five = limits.get("five_hour") or {}
    if week.get("used_percentage") is None and five.get("used_percentage") is None:
        return {"level": "unknown"}
    result = {"level": "normal", "five_hour_pct": five.get("used_percentage")}

    if week.get("used_percentage") is not None and week.get("resets_at"):
        used = float(week["used_percentage"])
        resets_at = float(week["resets_at"])
        elapsed = min(max((now - (resets_at - WEEK_SECONDS)) / WEEK_SECONDS, 0), 1) * 100
        result.update(
            week_pct=used,
            pace_pct=round(elapsed, 1),
            resets_in_hours=round(max(resets_at - now, 0) / 3600, 1),
        )
        if used >= CRITICAL_AT:
            result["level"] = "critical"
        elif used >= OFFLOAD_AT and used >= elapsed:  # high and not behind pace
            result["level"] = "offload"
        elif used > elapsed + PACE_MARGIN:
            result["level"] = "ahead"
    return result


POLICY = {
    "ahead": "Usage runs ahead of an even weekly pace. EQwise policy: bulk generation goes to gpt-luna through the eqwise-models tools (bulk_task, ask_model with output_file); planning, building and review stay on Claude.",
    "offload": "Weekly usage is past the offload threshold. EQwise policy: bulk generation goes to gpt-luna and routine drafting to gpt-terra through eqwise-models; Claude keeps planning, page building with Respira and final review.",
    "critical": "Weekly usage is near the limit. EQwise policy: only planning and final review stay on Claude; drafting, bulk work and second opinions go to the GPT models through eqwise-models.",
}


def describe(a: dict) -> str:
    if a["level"] == "unknown":
        return "Claude usage: unknown (no recent status line data)."
    parts = []
    if "week_pct" in a:
        parts.append(
            f"Claude weekly usage {a['week_pct']:.0f}% with {a['pace_pct']:.0f}% of the week elapsed, "
            f"resets in {a['resets_in_hours']:.0f} h."
        )
    if a.get("five_hour_pct") is not None:
        parts.append(f"5-hour window {a['five_hour_pct']:.0f}%.")
    if a["level"] in POLICY:
        parts.append(POLICY[a["level"]])
        parts.append("Client data that is not public stays on Claude.")
    return " ".join(parts)


def statusline_text(a: dict) -> str:
    if a["level"] == "unknown":
        return "EQwise usage: n/a"
    text = []
    if "week_pct" in a:
        text.append(f"Week {a['week_pct']:.0f}% (pace {a['pace_pct']:.0f}%)")
    if a.get("five_hour_pct") is not None:
        text.append(f"5h {a['five_hour_pct']:.0f}%")
    marker = {"ahead": " | ahead of pace", "offload": " | OFFLOAD", "critical": " | CRITICAL"}.get(a["level"], "")
    return " | ".join(text) + marker


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "statusline"
    if mode == "statusline":
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError:
            data = {}
        record = save(data) or load()
        print(statusline_text(assess(record)))
    elif mode == "hook":
        a = assess(load())
        if a["level"] in POLICY:
            print(json.dumps({
                "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": describe(a)}
            }))
    else:
        raise SystemExit("usage: usage_status.py [statusline|hook]")


if __name__ == "__main__":
    main()
