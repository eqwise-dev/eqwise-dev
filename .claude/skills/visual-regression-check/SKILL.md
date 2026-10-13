---
name: visual-regression-check
description: Pixel-level visual regression testing for client websites, like Percy but run by Claude. Keeps an approved screenshot baseline per client (several widths), re-captures after a change, diffs pixel by pixel with noise filtering (anti-aliasing, layout shift, cookie banners, animations, video) and hands Claude cropped before/after images of every changed region to triage. Use BEFORE and AFTER plugin, theme or WordPress core updates, global style changes (Divi presets, Elementor globals, design tokens, Bricks classes, custom CSS), page builder migrations, and before approving a draft duplicate from the website AI-agent. Also triggers on "visual regression", "visuele check", "is er iets kapot gegaan", "screenshot vergelijken", "check the site after the update", "compare live with staging", "Percy".
---

# Visual regression check

This skill gives the agent swarm a visual memory. Before a risky change it records how every key page looks at 375, 768 and 1440px. Afterwards it proves, pixel by pixel, what changed on **every** page, not only the page that was edited. Claude then judges only the changed regions, not whole pages.

The engine is `scripts/vrc.py` (Python + Playwright). All commands print JSON to stdout and progress to stderr. Exit code 0 means no visual change, 1 means changes found and 2 means capture errors.

## Setup (once per machine)

```bash
pip install -r <skill-dir>/scripts/requirements.txt
python -m playwright install chromium   # skip in Claude Code cloud: Chromium is preinstalled
```

Storage defaults to `./visual-tests/<client>/`. Set it with `--root DIR` (before the command) or `$VRC_ROOT`. Keep baselines somewhere that survives the session: a git repo (the `runs/` folders are git-ignored), or a synced folder on the Mac. In an ephemeral cloud session, commit `visual-tests/<client>/baseline/` or it is lost.

## Commands

```bash
V=<skill-dir>/scripts/vrc.py
python $V init     <client> --site https://example.nl [--limit 15]  # config from the sitemap
python $V status   <client>                     # baseline age, missing shots, last run
python $V baseline <client> [--pages home,contact]
python $V check    <client> [--pages ...] [--label after-plugin-update]
python $V approve  <client> [--run latest|<run-id>] [--pages home]   # ONLY after a person says yes
python $V compare  --a <url> --b <url> [--name x] [--widths 375,1440] [--client <client>]
```

`compare` needs no baseline. Use it for: the live page against a draft duplicate made by the website AI-agent (share preview link), production against staging, or the old site against the migrated site. `--client` reuses that client's hide and mask settings.

## Workflows

### A. Safe update (plugins, theme, core, global styles)
1. `status <client>`. If there is no baseline, or it is older than about 7 days, or a page is missing, run `baseline` first. The site must be in a known good state at that moment; if unsure, ask.
2. Do the change (for example the website AI-agent's `guarded_plugin_update`, `run_updates`, `update_elementor_global_colors`, `upsert_divi_presets`, `apply_design_direction`). Purge the cache if the site has one (`purge_cache`).
3. `check <client> --label <what-changed>`.
4. Triage (below). If there is a regression, roll back (the website AI-agent's `restore_snapshot`, `restore_quarantined_plugin`, or the update tool's own rollback) and run `check` again to confirm the site is back to baseline.

### B. Before approving a draft duplicate
`compare --a <live url> --b <share preview url> --client <client>`. Show the person what will change visually before they approve the duplicate. Unexpected differences outside the edited section are the important finding.

### C. Migration parity (Divi to Gutenberg, Elementor to Bricks, and so on)
`compare --a <old url> --b <new url>` per page. Differences are expected; the goal is to list where the new build deviates and fix those, until only accepted differences remain.

### D. Monitoring
Run `check` on a schedule (a Routine or `/loop`). Report only when the summary is not all pass.

## Triage protocol (this is the "visual review agent" part)

1. Read the JSON from stdout. `changed[]` lists each page and width with `diff_pct`, `height_delta`, `regions` and up to 6 `crops`.
2. **Look at the crop images with the Read tool**, not the full screenshots. Each crop shows BASELINE | CURRENT | DIFF side by side for one region. Changed pixels are red, regions have blue boxes. More regions are listed in `report.json`.
3. Classify each region:
   - **Regression**: broken layout, overlapping or missing elements, a wrong font (fallback), a wrong colour, a missing image, text cut off, a button that moved off-canvas, a mobile menu that broke.
   - **Intended**: matches the requested change.
   - **Noise**: dynamic content (dates, counters, sliders, review widgets, random posts, ads). Fix it with a `mask` or `hide` selector in `config.yaml` (see `references/config.md`), not by approving it repeatedly.
4. Look across widths and pages: the same change on many pages points to a global cause (theme, preset, plugin CSS). Say so.
5. Report to the person in their language (Dutch for EQwise clients unless they write English):
   - one line per finding: page, width, what changed in plain words, and the verdict;
   - regressions first, then intended changes, then noise with the proposed mask;
   - the path to `report.html` for their own review.
6. **Never run `approve` on your own judgment.** Ask: "Shall I approve these N changes as the new baseline?" Approve only the pages they confirm, with `--pages`. Never approve a run that contains regressions.

## Rules
- Capture the baseline and the check under the same conditions: same browser, logged out, cache purged, the same environment (do not compare a staging baseline against production).
- `error` items, such as a timeout or an HTTP error page, are findings too. A page that now returns 500 or 404 is the worst regression. Check `http_status`.
- `new` means there is no baseline for that shot yet. It is not a pass.
- A page that is 100% changed with a large `height_delta` usually means a wrong page, a login wall, a maintenance mode page or a consent wall. Open the current screenshot to confirm before you report a regression.
- If a site blocks headless browsers (Cloudflare challenge), say so; ask for a staging URL or an allowlist rule instead of retrying.

## Limits compared with Percy
- Chromium by default. `browsers: [chromium, webkit, firefox]` is possible after `playwright install webkit firefox`. WebKit approximates Safari but is not real Safari, and there are no real devices.
- No hosted dashboard or merge gate: the approval step is the conversation with the person, and the HTML report.
- Capture is sequential. Expect about 3 to 6 seconds per shot, so 15 pages × 3 widths takes about 3 minutes.
