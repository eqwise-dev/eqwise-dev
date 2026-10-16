#!/usr/bin/env python3
"""Benchmark the configured models on typical EQwise tasks: quality, cost, speed.

Every task has an automatic check, so scores are reproducible and no extra
"judge" model has to be paid for. Uses the same models, keys and daily budget
as the MCP server (swarm/litellm_config.yaml + swarm/models.env).

    swarm/.venv/bin/python swarm/bench.py                      # all configured models
    swarm/.venv/bin/python swarm/bench.py --models claude-haiku,claude-sonnet --runs 3

Results are printed and saved to swarm/usage/bench-<date>.md.
"""
import argparse
import asyncio
import json
import re
import time
from datetime import date
from pathlib import Path

import server

GSC_CSV = """query,clicks,impressions,position
seo bureau amsterdam,42,3100,6.2
wordpress website laten maken,8,5200,11.4
geo optimalisatie,15,900,4.1
lokale seo,3,2600,9.8
website onderhoud,21,1400,7.3
seo audit,5,700,12.0"""

PHP_SNIPPET = """add_action('wp_ajax_save_note', function () {
    global $wpdb;
    $id = $_POST['id'];
    $wpdb->query("UPDATE {$wpdb->prefix}notes SET text = '" . $_POST['text'] . "' WHERE id = $id");
    echo 'Saved: ' . $_POST['text'];
    wp_die();
});"""


def check_meta(text: str) -> float:
    text = text.strip().strip('"').strip()
    score = 0.0
    if 140 <= len(text) <= 160:
        score += 0.5
    if "wordpress website laten maken" in text.lower():
        score += 0.5
    return score


def check_schema(text: str) -> float:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return 0.0
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return 0.0
    checks = [
        "schema.org" in str(data.get("@context", "")),
        "Business" in str(data.get("@type", "")) or "Organization" in str(data.get("@type", "")),
        str((data.get("address") or {}).get("postalCode", "")).replace(" ", "") == "1017AB",
        "20 123 4567" in str(data.get("telephone", "")).replace("-", " ") or "201234567" in str(data.get("telephone", "")).replace(" ", ""),
    ]
    return sum(checks) / len(checks)


def check_php_review(text: str) -> float:
    t = text.lower()
    found = [
        "prepare" in t,                                   # SQL injection fix
        "nonce" in t,                                     # CSRF
        "current_user_can" in t or "capabilit" in t,      # authorization
        "esc_html" in t or "xss" in t,                    # output escaping
    ]
    return sum(found) / len(found)


def check_gsc(text: str) -> float:
    t = text.lower()
    score = 0.5 if "wordpress website laten maken" in t else 0.0
    if re.search(r"0[.,]15\s*%", t):
        score += 0.5
    return score


def check_clamp(text: str) -> float:
    t = text.replace(" ", "").lower()
    checks = [
        "clamp(1rem" in t,
        "1.25rem)" in t,
        re.search(r"0\.41[67]\d*vw", t) is not None,
        re.search(r"0\.91[67]\d*rem", t) is not None,
    ]
    return sum(checks) / len(checks)


TASKS = [
    {
        "name": "meta-description",
        "kind": "SEO copy",
        "prompt": (
            "Write one Dutch meta description for the homepage of EQwise, an Amsterdam agency "
            "that builds SEO and GEO optimised WordPress websites. It must contain the exact "
            "phrase 'WordPress website laten maken' and be 140 to 160 characters long. "
            "Reply with the meta description only."
        ),
        "check": check_meta,
    },
    {
        "name": "json-ld-schema",
        "kind": "Structured data",
        "prompt": (
            "Write JSON-LD for a LocalBusiness: EQwise, Herengracht 1, 1017 AB Amsterdam, NL, "
            "telephone +31 20 123 4567, url https://eqwise.nl. Reply with the JSON only."
        ),
        "check": check_schema,
    },
    {
        "name": "php-security-review",
        "kind": "Code review",
        "prompt": (
            "Review this WordPress AJAX handler for security problems and give the fixed code.\n\n"
            f"```php\n{PHP_SNIPPET}\n```"
        ),
        "check": check_php_review,
    },
    {
        "name": "gsc-analysis",
        "kind": "Analytics",
        "prompt": (
            "Search Console data (CSV):\n\n"
            f"{GSC_CSV}\n\n"
            "Of the queries with a CTR below 1%, which has the most impressions, and what is "
            "its CTR? Reply as: QUERY | CTR with two decimals and a % sign."
        ),
        "check": check_gsc,
    },
    {
        "name": "fluid-type-clamp",
        "kind": "CSS",
        "prompt": (
            "Give a CSS clamp() for a font size that grows linearly from 16px at a 320px "
            "viewport to 20px at a 1280px viewport. Use rem (16px = 1rem) for the min, max and "
            "the constant part, vw for the slope, 4 decimals. Reply with the clamp() only."
        ),
        "check": check_clamp,
    },
]


async def run_one(alias: str, task: dict) -> dict:
    start = time.monotonic()
    try:
        answer, cost = await server._call_with_cost(alias, None, task["prompt"], 4000, f"bench:{task['name']}")
        error = None
    except Exception as e:  # keep benchmarking the other models
        answer, cost, error = "", 0.0, f"{type(e).__name__}: {e}"
    return {
        "model": alias,
        "task": task["name"],
        "score": task["check"](answer) if not error else 0.0,
        "cost": cost,
        "seconds": time.monotonic() - start,
        "error": error,
    }


async def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", help="comma separated aliases (default: all configured)")
    parser.add_argument("--runs", type=int, default=1, help="repeat each task N times")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")] if args.models else list(server.MODELS)
    for alias in models:
        server._check_model(alias, confidential=False)
    server._check_budget()

    results = []
    for alias in models:  # models one by one, tasks in parallel per model
        jobs = [run_one(alias, t) for t in TASKS for _ in range(args.runs)]
        results += await asyncio.gather(*jobs)

    lines = [
        f"# Model benchmark {date.today().isoformat()}",
        "",
        f"{len(TASKS)} tasks x {args.runs} run(s). Score 0-100 from automatic checks.",
        "",
        "| Model | Score | Cost (USD) | Cost per score point | Avg seconds | Errors |",
        "|---|---|---|---|---|---|",
    ]
    for alias in models:
        rows = [r for r in results if r["model"] == alias]
        score = 100 * sum(r["score"] for r in rows) / len(rows)
        cost = sum(r["cost"] for r in rows)
        per_point = f"{cost / score:.5f}" if score else "n/a"
        seconds = sum(r["seconds"] for r in rows) / len(rows)
        errors = sum(1 for r in rows if r["error"])
        lines.append(f"| {alias} | {score:.0f} | {cost:.4f} | {per_point} | {seconds:.1f} | {errors} |")

    lines += ["", "| Task | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
    for task in TASKS:
        cells = []
        for alias in models:
            rows = [r for r in results if r["model"] == alias and r["task"] == task["name"]]
            cells.append(f"{100 * sum(r['score'] for r in rows) / len(rows):.0f}")
        lines.append(f"| {task['name']} ({task['kind']}) | " + " | ".join(cells) + " |")

    errors = [r for r in results if r["error"]]
    if errors:
        lines += ["", "Errors:"] + [f"- {r['model']} / {r['task']}: {r['error']}" for r in errors]

    report = "\n".join(lines)
    print(report)
    out = server.USAGE_LOG.parent / f"bench-{date.today().isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except server.ToolError as e:
        raise SystemExit(f"Error: {e}")
