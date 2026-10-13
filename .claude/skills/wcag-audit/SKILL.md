---
name: wcag-audit
description: Complete WCAG 2.2 AA accessibility process for (WordPress) websites, from audit to fix to statement. Runs axe-core plus real browser tests that automated scanners skip (keyboard traps, visible focus, focus on hidden menus, focus hidden behind sticky headers, skip link, reflow at 320px, text spacing, target size, auto-moving sliders, autoplay media, form labels and autocomplete), then has Claude review the evidence (alt text quality, focus order map, contrast on images, ARIA snapshot), works through the manual checklist, writes a prioritised Dutch report, fixes issues through Respira and re-tests, and drafts the toegankelijkheidsverklaring (accessibility statement) / European Accessibility Act (EAA) information. Use for "WCAG", "toegankelijkheid", "toegankelijkheidsaudit", "accessibility audit", "a11y", "EAA", "European Accessibility Act", "toegankelijkheidsverklaring", "digitoegankelijk", "EN 301 549", "is mijn site toegankelijk", "screen reader", "contrast check", "keyboard navigation".
---

# WCAG audit, fix and statement

The standard is **WCAG 2.2 level AA** (55 success criteria). That covers EN 301 549 / the EAA (which reference WCAG 2.1 AA) plus the 2.2 additions. The goal is a site that real people can use with a keyboard, a screen reader, zoom or low vision, with evidence for every claim.

Be honest about limits: automated tooling finds roughly a third of all WCAG problems. Never call a site "compliant" or "100% toegankelijk" on the basis of the script alone. The manual checklist and Claude's review are part of the audit, not optional extras.

## Setup (once per machine)

```bash
pip install -r <skill-dir>/scripts/requirements.txt
python -m playwright install chromium     # skip in Claude Code cloud: Chromium is preinstalled
```

axe-core 4.13 is bundled in `scripts/vendor/` (MPL-2.0), so no CDN or npm is needed.

## Step 1 – Scope

- Which site and which pages. Default: `--site` samples up to 10 pages from the sitemap across content types. Always make sure the sample includes the home page, a content page, a blog post, a page with a form (contact), search results, the 404 page and, for a shop, a product page, the cart and checkout (WCAG-EM style). Add missing ones with `--urls`.
- Audit staging when possible. Never submit forms on a live site.
- If the person did not say otherwise: Dutch report, level AA.

## Step 2 – Automated audit

```bash
W=<skill-dir>/scripts/wcag.py
python $W audit --site https://example.nl --limit 10 [--urls extra1,extra2] [--name client]
python $W audit --urls https://example.nl/,https://example.nl/contact/      # exact pages
```

Expect about 30 to 60 seconds per page (6s of that is the motion check; `--no-motion` skips it). Output goes to `wcag-audits/<name>/<timestamp>/`:
- `findings.json`: every finding with WCAG criteria, impact, status (`fail` or `review`), affected pages and elements, a `template_wide` flag (the same element on almost every page, so it is fixed once in the header, footer or theme), and evidence paths.
- `report.md`: a technical report plus the manual checklist.
- `evidence/<nn-page>/`: `desktop.png`, `focus-order.png`, `reflow-320.png`, `motion.png`, `aria-snapshot.yaml`, contrast and target-size crops, and `img-NN.png` image crops.

The stdout JSON gives the summary, the top findings and where the review evidence is. If `summary.pages_http_error` lists URLs, those pages returned 4xx/5xx: replace them with working URLs and re-run, because an audit of an error page says nothing about the real page.

What the script tests itself, beyond axe:

| Test | WCAG |
|---|---|
| Real Tab presses: keyboard trap | 2.1.2 |
| Focus indicator: pixel comparison of each element focused vs unfocused | 2.4.7 |
| Focus lands on invisible elements (closed mobile menu, off-canvas panel) | 2.4.3 / 2.4.7 |
| Focused element fully covered by a sticky header, cookie bar or chat widget | 2.4.11 |
| Skip link present and its target exists | 2.4.1 |
| Focus order map | 2.4.3 |
| Horizontal scroll at 320px, and the elements that cause it | 1.4.10 |
| Text clipped with WCAG text spacing applied | 1.4.12 |
| Target size on mobile and desktop (axe) | 2.5.8 |
| Content that moves by itself (sliders, tickers, video) | 2.2.2 |
| Autoplay sound | 1.4.2 |
| Video without captions track, embedded YouTube/Vimeo | 1.2.x |
| Placeholder-only fields | 3.3.2 |
| Missing autocomplete on personal data fields | 1.3.5 |
| Vague link texts going to different pages ("Lees meer") | 2.4.4 |
| Heading outline, missing h1, missing `<main>` | 1.3.1 |
| Alt texts that look like file names | 1.1.1 |

axe runs first with the cookie banner still open, so the banner is audited too. The script then tries to accept it before the keyboard tests.

## Step 3 – Claude's review (the part tools cannot do)

Use the Read tool on the evidence images and files. Be specific and keep it short.

1. **Alt text quality (1.1.1):** look at each `img-NN.png` next to its alt text (in `findings.json` under `pages[].image_review`). Is the alt accurate, concise and purposeful? For a linked image, does it describe the destination? Is a decorative image given alt=""? Is text inside the image (1.4.5) repeated in the alt?
2. **Focus order (2.4.3):** look at `focus-order.png` (numbered boxes, red = problem). Is the order logical? Do menu, content and footer follow the visual order? Check `keyboard.backward_jumps`.
3. **Contrast needing review:** `color-contrast` crops with status `review` are text on images or gradients. Judge them visually: is the text at least 4.5:1 everywhere, or 3:1 for large text?
4. **Motion (2.2.2):** look at `motion.png`. What moves, does it run longer than 5 seconds, and is there a pause control?
5. **Screen reader view (1.3.1, 2.4.6, 4.1.2):** read `aria-snapshot.yaml`. Do buttons and links have meaningful names? Are there unnamed buttons ("button" with no name)? Do the hamburger toggle, submenus, accordions and tabs expose their state? Do headings make sense on their own? Is there one main navigation with a label?
6. **Reflow:** look at `reflow-320.png`: anything cut off or overlapping?
7. **Interaction checks the script does not do.** Run them yourself with Playwright (a short ad-hoc script) or the browser skills:
   - Open the mobile menu with the keyboard (Enter/Space on the toggle): does focus move into it, does Esc close it, does `aria-expanded` change? (2.1.1, 4.1.2)
   - Desktop submenus: reachable by keyboard; can a hover or focus flyout be dismissed with Esc? (2.1.1, 1.4.13)
   - Popups and modals: focus moves into them, Esc closes them, focus returns to where it was. (2.1.2, 2.4.3)
   - Forms **on staging only**: submit empty. Are errors shown in text, linked to the field, with a suggestion? (3.3.1, 3.3.3, 4.1.3)
   - 200% zoom: run at viewport 640 with the same checks. (1.4.4)
8. **Remaining manual checklist** (bottom of `report.md`): mark each item pass, fail, not applicable, or "needs a person". Things like caption accuracy, cognitive clarity and whether instructions rely on colour need a human. Say so instead of guessing.

## Step 4 – Report to the person

Write in Dutch unless they write English, in plain language a business owner understands. The structure:

1. **Conclusion in 3 lines:** how far the site is from WCAG 2.2 AA, the biggest blockers, and which groups of users are affected.
2. **Priority list:**
   - P1: blockers (keyboard trap, unusable menu or form, missing names on controls, contrast on main content)
   - P2: serious
   - P3: moderate and minor

   Put template-wide issues first: one fix in the header, footer or theme solves them on every page. For each issue: what it is, the WCAG criterion (number and Dutch name), where (page and element, with a screenshot crop if useful), who is affected, how to fix it in their builder, and the effort (S/M/L).
3. **What has been checked and what has not:** the automated tests, Claude's review and the manual items still open.
4. **Next step:** offer to fix (step 5).

For a client-facing deliverable, offer to publish it as an Artifact or a Claude Doc. Never put credentials or internal URLs in it.

## Step 5 – Fix (with permission) and re-test

Follow `references/wordpress-fixes.md` for builder-specific fixes. Rules:
- Ask before changing anything. Fix through Respira in the site's own builder format, on a draft duplicate for live pages (Respira's rules apply: snapshot first, never raw SQL or theme PHP).
- Fix global causes first: global colours or presets for contrast, one site-wide `:focus-visible` style, the skip link in the theme, the form plugin's field settings, and alt texts in bulk via `update_media_batch`.
- Do **not** install accessibility overlays (accessiBe, UserWay, EqualWeb and similar). They do not make a site conformant and often make it worse for screen reader users.
- Treat Respira's `apply_accessibility_fixes` as a helper: review its proposed changes before applying them, then verify with this audit.
- After fixing, run the audit again on the same pages and run `python $W diff OLD/findings.json NEW/findings.json` to show what was fixed, what remains and whether anything is new. Report that diff.

## Step 6 – Statement and legal context

See `references/wetgeving-en-verklaring.md`. Determine whether the EAA applies to the client (e-commerce, banking, transport, telecom, e-books; micro-enterprises are exempt for services), or the Dutch government rules (Besluit digitale toegankelijkheid overheid). Then draft:
- for EAA-covered services: the accessibility information the law requires (how the service meets the requirements), for the terms and conditions or an accessibility page;
- for others: a voluntary toegankelijkheidsverklaring page, using the template.

Base every claim on the audit results, list known issues honestly with a planned fix date, and give a contact route for reporting barriers. Make no legal claims beyond what the evidence supports. Recommend an independent expert audit when a formal status or legal certainty is needed.
