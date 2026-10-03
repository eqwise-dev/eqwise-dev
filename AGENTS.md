# AGENTS.md

Status: actief · Versie 1.1 · 2026-10-03
Behavioral guidelines for coding agents working in this repository. These rules apply to any agent - Claude Code, Cursor, Codex, OpenCode, or a local LLM stack. Merge with project-specific instructions as needed.

Master copy: `00_EQwise-Kennisbank/AGENTS-v1.1.md`. In every GitHub repo this file is saved in the root as `AGENTS.md`.

Version 1.0 (2026-07-19) - first version. Rules 1-4 adapted from forrestchang/andrej-karpathy-skills, derived from Andrej Karpathy's observations on LLM coding pitfalls. Rule 5 (separation of concerns) added for EQwise.
Version 1.1 (2026-10-03) - plan template restored in rule 4, rule 6 (plannen en bedrijfsbeslissingen) added. Replaces AGENTS-v1.0.md.

Tradeoff: these guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the request.

## 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan before starting:

```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let the agent loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Separation of Concerns: behavior here, criteria in skills

This file defines generic agent behavior only. Work-type-specific criteria live in the relevant skill in `_Kennisbank/skills`, never here.

- Websites and presentations: huisstijl rules (headings, fonts, weights, colors, bullet styles, spacing, all elements large and small) are defined per client in `00_Huisstijl` and enforced by the `eqwise-klantproject` skill.
- If no huisstijl document exists for a client: report it and propose building one first (derive it from the live site, from client wishes, or from earlier client projects). Never improvise brand rules.
- EQwise orchestration rules (maker/controle loop, max 3 iterations, layered output) live in each agent's own AGENT.md and the orchestrator, not in this file.

## 6. Plannen en bedrijfsbeslissingen

Werk ik aan een plan of een bedrijfsbeslissing, bied dan de skill `eqwise-strategie` aan. Is die skill in deze omgeving niet beschikbaar (de bron staat in Cowork, de kopie voor Claude Code in `~/.claude/skills/eqwise-strategie/`), meld dat dan in één zin in plaats van de regel stil over te slaan.

---

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
