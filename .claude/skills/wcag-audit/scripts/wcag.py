#!/usr/bin/env python3
"""wcag.py - WCAG 2.2 AA audit engine for websites (built for WordPress sites).

Per page it runs:
  1. axe-core (bundled) for WCAG 2.0/2.1/2.2 A+AA rules, desktop and mobile
  2. keyboard test: real Tab presses; focus visibility (pixel comparison focused vs
     unfocused), keyboard traps, focus on invisible elements, focus hidden behind
     sticky headers/banners, skip link, focus order map
  3. reflow at 320px (1.4.10), text spacing (1.4.12), target size on mobile (2.5.8)
  4. motion: content that moves by itself (2.2.2), autoplay media (1.4.2)
  5. structure: title, lang, headings, landmarks, links, images, forms, media and
     the ARIA snapshot (what a screen reader gets), plus image crops for alt review

Commands
  audit --urls URL[,URL..] | --site URL [--limit N]   run the audit
  diff  OLD/findings.json NEW/findings.json           fixed / remaining / new

Output: <out>/findings.json, report.md, evidence/ (screenshots, crops, aria snapshots).
Exit code: 0 no failures, 1 failures found, 2 pages could not be audited.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcag_criteria import CRITERIA, name as sc_name, sc_from_axe_tag  # noqa: E402

try:
    import numpy as np
    from PIL import Image, ImageDraw
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing dependency: {exc.name}. Install with:\n"
             "  pip install playwright pillow numpy && python -m playwright install chromium")

HERE = Path(__file__).resolve().parent
AXE_PATH = Path(os.environ.get("AXE_PATH") or HERE / "vendor" / "axe.min.js")
UA = "Mozilla/5.0 (EQwise wcag-audit)"
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3, None: 4}

COOKIE_ACCEPT = [
    ".cmplz-accept", ".cky-btn-accept", "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyButtonAccept", "._brlbs-btn-accept-all", "#cookie_action_close_header",
    "#moove_gdpr_cookie_modal .mgbutton", ".rcb-btn-accept-all", "#onetrust-accept-btn-handler",
]
COOKIE_TEXT = r"^(alle[s]? )?(cookies )?(accepteren|accepteer|akkoord|toestaan|accept( all)?|allow all|i agree|ok(é|e)?)( alle[s]?)?( cookies)?$"

AMBIGUOUS_LINKS = {
    "lees meer", "meer", "meer info", "meer informatie", "klik hier", "hier", "bekijk", "bekijk meer",
    "ontdek meer", "ontdek", "verder lezen", "lees verder", "link", "read more", "more", "click here",
    "here", "learn more", "details", "info", "...", "»", ">",
}

# --------------------------------------------------------------------------- JS helpers
JS_HELPERS = r"""
window.__wcag = (() => {
  const cssPath = (el) => {
    if (!(el instanceof Element)) return '';
    if (el.id && document.querySelectorAll('#' + CSS.escape(el.id)).length === 1) return '#' + CSS.escape(el.id);
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 5) {
      let part = el.localName;
      if (el.id && document.querySelectorAll('#' + CSS.escape(el.id)).length === 1) { parts.unshift('#' + CSS.escape(el.id)); break; }
      const cls = [...el.classList].filter(c => !/^(is-|has-|active|focus|hover|elementor-element-[0-9a-f]+$)/.test(c)).slice(0, 2);
      if (cls.length) part += '.' + cls.map(c => CSS.escape(c)).join('.');
      const p = el.parentElement;
      if (p) { const sib = [...p.children].filter(c => c.localName === el.localName); if (sib.length > 1) part += `:nth-of-type(${sib.indexOf(el) + 1})`; }
      parts.unshift(part); el = p;
    }
    return parts.join(' > ');
  };
  const accName = (el) => {
    if (!el) return '';
    const by = el.getAttribute('aria-labelledby');
    if (by) return by.split(/\s+/).map(id => document.getElementById(id)?.innerText || '').join(' ').trim();
    const al = el.getAttribute('aria-label'); if (al) return al.trim();
    if (el.labels && el.labels.length) return [...el.labels].map(l => l.innerText).join(' ').trim();
    const t = (el.innerText || '').trim(); if (t) return t.replace(/\s+/g, ' ');
    const img = el.querySelector && el.querySelector('img[alt]'); if (img && img.alt) return img.alt.trim();
    return (el.getAttribute('title') || el.getAttribute('alt') || el.getAttribute('placeholder') || el.value || '').toString().trim();
  };
  const visibleText = (el) => (el.innerText || '').replace(/\s+/g, ' ').trim();
  const describe = (el) => {
    if (!el || el === document.body || el === document.documentElement) return null;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return { selector: cssPath(el), tag: el.localName, role: el.getAttribute('role') || '', name: accName(el).slice(0, 80),
             href: el.getAttribute('href') || '', x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height,
             vx: r.left, vy: r.top,
             visible: r.width > 1 && r.height > 1 && cs.visibility !== 'hidden' && cs.opacity !== '0'
                      && !/rect\(0(px)?,? 0(px)?,? 0(px)?,? 0(px)?\)/.test(cs.clip) && !/inset\((50|100)%/.test(cs.clipPath)
                      && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth,
             inViewport: r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth };
  };
  const isFixedish = (el) => { for (; el && el !== document.body; el = el.parentElement) { const p = getComputedStyle(el).position; if (p === 'fixed' || p === 'sticky') return el; } return null; };
  const obscured = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return null;
    const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 2, r.top + 2], [r.right - 2, r.top + 2], [r.left + 2, r.bottom - 2], [r.right - 2, r.bottom - 2]];
    let blocked = 0, blocker = null;
    for (const [x, y] of pts) {
      if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) { blocked++; continue; }
      const top = document.elementFromPoint(x, y);
      if (!top || el.contains(top) || top.contains(el)) continue;
      const fx = isFixedish(top);
      if (fx) { blocked++; blocker = fx; }
    }
    return { blocked, total: pts.length, blocker: blocker ? cssPath(blocker) : null };
  };
  return { cssPath, accName, visibleText, describe, obscured, isFixedish };
})();
"""

JS_STRUCTURE = r"""
() => {
  const W = window.__wcag;
  const vis = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const headings = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role=heading]')].filter(vis).map(h => ({
    level: h.getAttribute('aria-level') ? +h.getAttribute('aria-level') : +h.localName[1] || 2, text: W.visibleText(h).slice(0, 120), selector: W.cssPath(h) }));
  const landmarks = {};
  for (const [k, sel] of Object.entries({ banner: 'header:not(article header):not(section header),[role=banner]', navigation: 'nav,[role=navigation]', main: 'main,[role=main]', contentinfo: 'footer:not(article footer):not(section footer),[role=contentinfo]', search: '[role=search],search', complementary: 'aside,[role=complementary]' }))
    landmarks[k] = document.querySelectorAll(sel).length;
  const links = [...document.querySelectorAll('a[href]')].filter(vis).map(a => ({ text: W.visibleText(a).slice(0, 100), name: W.accName(a).slice(0, 100), href: a.href, selector: W.cssPath(a),
    newWindow: a.target === '_blank' }));
  const images = [...document.querySelectorAll('img, svg[role=img], [role=img]')].filter(vis).map(i => { const r = i.getBoundingClientRect();
    return { selector: W.cssPath(i), tag: i.localName, src: i.currentSrc || i.src || '', alt: i.getAttribute('alt'), ariaLabel: i.getAttribute('aria-label'),
             role: i.getAttribute('role'), hidden: i.getAttribute('aria-hidden') === 'true', inLink: !!i.closest('a,button'),
             linkText: i.closest('a,button') ? W.visibleText(i.closest('a,button')).slice(0, 80) : '', w: Math.round(r.width), h: Math.round(r.height),
             x: r.left + scrollX, y: r.top + scrollY }; });
  const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea')].filter(vis).map(f => ({
    selector: W.cssPath(f), type: f.type || f.localName, nameAttr: f.name || '', id: f.id || '', label: W.accName(f).slice(0, 80),
    visibleLabel: !!(f.labels && f.labels.length && [...f.labels].some(vis)), placeholder: f.placeholder || '', autocomplete: f.getAttribute('autocomplete') || '',
    required: f.required || f.getAttribute('aria-required') === 'true' }));
  const media = [...document.querySelectorAll('video,audio')].map(m => ({ tag: m.localName, selector: W.cssPath(m), autoplay: m.autoplay, muted: m.muted, loop: m.loop,
    controls: m.controls, tracks: [...m.querySelectorAll('track')].map(t => t.kind), duration: isFinite(m.duration) ? Math.round(m.duration) : null, paused: m.paused }));
  const iframes = [...document.querySelectorAll('iframe')].filter(vis).map(f => ({ src: f.src, title: f.title || '', selector: W.cssPath(f) }));
  const tables = [...document.querySelectorAll('table')].filter(vis).map(t => ({ selector: W.cssPath(t), th: t.querySelectorAll('th').length, caption: !!t.querySelector('caption'), rows: t.rows.length }));
  const pauseControls = [...document.querySelectorAll('button,[role=button],a')].filter(b => /pau[sz]e|stop|afspelen|play/i.test(W.accName(b))).length;
  return { title: document.title, lang: document.documentElement.getAttribute('lang') || '', headings, landmarks, links, images, fields, media, iframes, tables,
           pauseControls, generator: document.querySelector('meta[name=generator]')?.content || '' };
}
"""

JS_REFLOW = r"""
(maxW) => {
  const W = window.__wcag;
  const docW = document.documentElement.scrollWidth;
  const out = [];
  if (docW > maxW + 2) {
    const scrollable = (el) => { for (; el && el !== document.body; el = el.parentElement) { const o = getComputedStyle(el).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
    for (const el of document.body.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0 || r.right <= maxW + 2) continue;
      if (scrollable(el.parentElement)) continue;
      if ([...el.children].some(c => c.getBoundingClientRect().right > maxW + 2)) continue;  // report the deepest offender
      out.push({ selector: W.cssPath(el), right: Math.round(r.right), width: Math.round(r.width), tag: el.localName });
      if (out.length >= 15) break;
    }
  }
  return { docWidth: docW, offenders: out };
}
"""

JS_CLIPPED = r"""
() => {
  const W = window.__wcag;
  const res = [];
  for (const el of document.body.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (!/hidden|clip/.test(cs.overflowY + cs.overflowX)) continue;
    const txt = W.visibleText(el);
    if (!txt || txt.length > 300 || el.clientHeight === 0) continue;
    const clipY = /hidden|clip/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2;
    const clipX = /hidden|clip/.test(cs.overflowX) && el.scrollWidth > el.clientWidth + 2;
    const lc = parseInt(cs.webkitLineClamp) > 0;
    if ((clipY || clipX) && !lc) res.push({ selector: W.cssPath(el), text: txt.slice(0, 80) });
  }
  return res;
}
"""

TEXT_SPACING_CSS = """
* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }
p { margin-bottom: 2em !important; }
"""


# --------------------------------------------------------------------------- helpers
def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def sitemap_urls(site: str, limit: int) -> tuple[list[str], list[str]]:
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    errors = []
    for cand in ("sitemap_index.xml", "wp-sitemap.xml", "sitemap.xml"):
        try:
            root = ET.fromstring(fetch(urljoin(site.rstrip("/") + "/", cand)))
            break
        except Exception as exc:
            errors.append(f"{cand}: {exc}")
    else:
        return [], errors
    if root.tag.endswith("sitemapindex"):
        maps = [e.text.strip() for e in root.iter(f"{ns}loc")]
        maps = [m for m in maps if not re.search(r"(category|tag|author|taxonom|users|product_cat)", m)]
        groups = []
        for m in maps:
            try:
                groups.append([e.text.strip() for e in ET.fromstring(fetch(m)).iter(f"{ns}loc")])
            except Exception as exc:
                errors.append(f"{m}: {exc}")
        # sample across content types (WCAG-EM style): round-robin over the sitemaps
        urls, i = [], 0
        while len(urls) < limit * 2 and any(i < len(g) for g in groups):
            urls += [g[i] for g in groups if i < len(g)]
            i += 1
    else:
        urls = [e.text.strip() for e in root.iter(f"{ns}loc")]
    urls = [u for u in dict.fromkeys(urls) if not re.search(r"\.(jpe?g|png|webp|gif|pdf|svg)$", u, re.I)]
    home = site.rstrip("/") + "/"
    urls = [home] + [u for u in urls if u.rstrip("/") != site.rstrip("/")]
    return urls[:limit], errors


def slug(url: str) -> str:
    p = urlparse(url)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", p.path.strip("/")).strip("-").lower() or "home"
    return s[:60]


def crop_to(page, box: dict, out: Path, pad: int = 8, max_h: int = 600) -> str | None:
    """Screenshot a page-coordinate box (full-page coordinates)."""
    try:
        x, y = max(0, box["x"] - pad), max(0, box["y"] - pad)
        w, h = box["w"] + pad * 2, min(box["h"] + pad * 2, max_h)
        if w < 2 or h < 2:
            return None
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out), clip={"x": x, "y": y, "width": w, "height": h}, full_page=True, animations="disabled")
        return str(out)
    except Exception:
        return None


def accept_cookies(page) -> str | None:
    for sel in COOKIE_ACCEPT:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=2000)
                page.wait_for_timeout(600)
                return sel
        except Exception:
            continue
    try:
        btn = page.get_by_role("button", name=re.compile(COOKIE_TEXT, re.I)).first
        if btn.count() and btn.is_visible():
            btn.click(timeout=2000)
            page.wait_for_timeout(600)
            return "button[text]"
    except Exception:
        pass
    return None


def settle(page, timeout_ms: int):
    try:
        page.wait_for_load_state("networkidle", timeout=min(10000, timeout_ms))
    except Exception:
        pass
    page.evaluate("""async () => {
        const step = innerHeight * 0.8, max = Math.min(document.documentElement.scrollHeight, 25000);
        for (let y = 0; y < max; y += step) { scrollTo(0, y); await new Promise(r => setTimeout(r, 80)); }
        scrollTo(0, 0); if (document.fonts) await document.fonts.ready; }""")
    page.wait_for_timeout(400)


# --------------------------------------------------------------------------- findings
class Findings:
    def __init__(self):
        self.items: dict[str, dict] = {}

    def add(self, rule: str, url: str, *, sc: list[str], impact: str, status: str, title: str,
            fix: str = "", source: str = "wcag.py", nodes: list[dict] | None = None, help_url: str = "",
            best_practice: bool = False):
        it = self.items.setdefault(rule, {
            "rule": rule, "source": source, "sc": sc, "impact": impact, "status": status, "title": title,
            "fix": fix, "help_url": help_url, "best_practice": best_practice, "pages": {}})
        if IMPACT_ORDER.get(impact, 4) < IMPACT_ORDER.get(it["impact"], 4):
            it["impact"] = impact
        if status == "fail":
            it["status"] = "fail"
        page = it["pages"].setdefault(url, [])
        for n in nodes or [{}]:
            if len(page) < 25:
                page.append(n)

    def finalize(self, n_pages: int) -> list[dict]:
        out = []
        for it in self.items.values():
            it["page_count"] = len(it["pages"])
            it["node_count"] = sum(len(v) for v in it["pages"].values())
            # same selector on (almost) every audited page -> header/footer/template issue
            sel_pages: dict[str, set] = {}
            for url, nodes in it["pages"].items():
                for n in nodes:
                    if n.get("selector"):
                        sel_pages.setdefault(n["selector"], set()).add(url)
            need = max(3, 0.8 * n_pages)
            it["template_wide"] = n_pages >= 3 and (any(len(v) >= need for v in sel_pages.values())
                                                    or (not sel_pages and it["page_count"] >= need))
            it["pages"] = [{"url": u, "nodes": ns} for u, ns in it["pages"].items()]
            out.append(it)
        out.sort(key=lambda i: (i["status"] != "fail", i["best_practice"], IMPACT_ORDER.get(i["impact"], 4),
                                -i["page_count"], -i["node_count"]))
        return out


# --------------------------------------------------------------------------- audit steps
def run_axe(page, axe_src: str, rules: list[str] | None = None) -> dict:
    page.add_script_tag(content=axe_src)
    opts = {"resultTypes": ["violations", "incomplete"]}
    if rules:
        opts["runOnly"] = {"type": "rule", "values": rules}
    else:
        opts["runOnly"] = {"type": "tag", "values": AXE_TAGS + ["best-practice"]}
    return page.evaluate("async (opts) => await axe.run(document, opts)", opts)


def axe_findings(F: Findings, url: str, res: dict, page, ev: Path, viewport: str, crop_budget: list[int]):
    for kind in ("violations", "incomplete"):
        for v in res.get(kind, []):
            scs = sorted({s for s in (sc_from_axe_tag(t) for t in v["tags"]) if s in CRITERIA})
            bp = not scs
            nodes = []
            for n in v["nodes"][:25]:
                target = n["target"][0] if n["target"] else ""
                if isinstance(target, list):
                    target = " >>> ".join(target)
                node = {"selector": target, "html": n.get("html", "")[:300], "viewport": viewport,
                        "summary": (n.get("failureSummary") or "").replace("\n", " ")[:400]}
                data = (n.get("any") or [{}])[0].get("data") if n.get("any") else None
                if isinstance(data, dict) and "contrastRatio" in data:
                    node["contrast"] = {k: data.get(k) for k in ("fgColor", "bgColor", "contrastRatio", "expectedContrastRatio", "fontSize", "fontWeight")}
                wants_crop = (v["id"] == "color-contrast" or
                              (kind == "violations" and v["id"] in ("link-in-text-block", "target-size")))
                if wants_crop and target and crop_budget[0] > 0:
                    try:
                        box = page.locator(target).first.bounding_box(timeout=1500)
                        if box:
                            sy = page.evaluate("scrollY")
                            p = crop_to(page, {"x": box["x"], "y": box["y"] + sy, "w": box["width"], "h": box["height"]},
                                        ev / f"{v['id']}-{viewport}-{crop_budget[0]}.png", pad=12)
                            if p:
                                node["crop"] = p
                                crop_budget[0] -= 1
                    except Exception:
                        pass
                nodes.append(node)
            F.add(f"axe:{v['id']}", url, sc=scs, impact=v.get("impact") or "moderate",
                  status="fail" if kind == "violations" else "review", title=v["help"], fix=v.get("description", ""),
                  source="axe-core", nodes=nodes, help_url=v.get("helpUrl", ""), best_practice=bp)


def keyboard_test(F: Findings, url: str, page, ev: Path, max_tabs: int) -> dict:
    page.evaluate("() => { scrollTo(0, 0); document.activeElement && document.activeElement.blur(); }")
    page.mouse.move(0, 0)
    seq, same_count, last_sel, trap = [], 0, None, None
    no_indicator, invisible, obscured = [], [], []
    first_sel = None
    for i in range(max_tabs):
        page.keyboard.press("Tab")
        page.wait_for_timeout(60)
        d = page.evaluate("() => window.__wcag.describe(document.activeElement)")
        if d is None:
            if seq:
                break  # focus left the document / returned to body: cycle complete
            continue
        if d["selector"] == first_sel and i > 2:
            break
        first_sel = first_sel or d["selector"]
        d["n"] = len(seq) + 1
        if d["selector"] == last_sel:
            same_count += 1
            if same_count >= 3:
                trap = d
                break
        else:
            same_count = 0
        last_sel = d["selector"]
        if not d["visible"]:
            invisible.append(d)
            seq.append(d)
            continue
        ob = page.evaluate("() => window.__wcag.obscured(document.activeElement)")
        if ob and ob["blocked"] == ob["total"]:
            obscured.append({**d, "blocker": ob["blocker"]})
        # focus indicator: compare the element area focused vs unfocused
        clip = {"x": max(0, d["vx"] - 6), "y": max(0, d["vy"] - 6), "width": max(4, min(d["w"] + 12, 1200)), "height": max(4, min(d["h"] + 12, 600))}
        try:
            vp = page.viewport_size
            clip["width"] = min(clip["width"], vp["width"] - clip["x"])
            clip["height"] = min(clip["height"], vp["height"] - clip["y"])
            if clip["width"] > 2 and clip["height"] > 2 and d["inViewport"]:
                a = np.asarray(Image.open(io.BytesIO(page.screenshot(clip=clip, animations="disabled"))).convert("RGB"), dtype=np.int16)
                page.evaluate("() => { window.__wcagLast = document.activeElement; document.activeElement.blur(); }")
                page.wait_for_timeout(40)
                b = np.asarray(Image.open(io.BytesIO(page.screenshot(clip=clip, animations="disabled"))).convert("RGB"), dtype=np.int16)
                page.evaluate("() => window.__wcagLast && window.__wcagLast.focus({ preventScroll: true })")
                changed = int((np.abs(a - b).sum(axis=2) > 30).sum()) if a.shape == b.shape else 999
                d["indicator_px"] = changed
                if changed < 8:
                    no_indicator.append(d)
        except Exception:
            page.evaluate("() => window.__wcagLast && window.__wcagLast.focus({ preventScroll: true })")
        seq.append(d)

    # skip link
    skip = None
    if seq:
        f0 = seq[0]
        if f0["href"].startswith("#") and re.search(r"skip|inhoud|content|hoofdinhoud|naar", f0["name"], re.I):
            target_ok = page.evaluate("(h) => { const id = decodeURIComponent(h.slice(1)); return !!(id && document.getElementById(id)); }", f0["href"])
            skip = {"present": True, "name": f0["name"], "target_exists": target_ok}
        else:
            skip = {"present": False, "first_focus": f0["name"] or f0["selector"]}

    if trap:
        F.add("kbd:keyboard-trap", url, sc=["2.1.2"], impact="critical", status="fail",
              title="Keyboard focus gets stuck (keyboard trap)",
              fix="Make sure Tab and Shift+Tab can leave the component; check embedded widgets, players and modals.",
              nodes=[{"selector": trap["selector"], "name": trap["name"]}])
    if no_indicator:
        F.add("kbd:focus-not-visible", url, sc=["2.4.7"], impact="serious", status="fail",
              title="No visible focus indicator",
              fix="Add a clear :focus-visible style (for example outline: 3px solid <brand colour>; outline-offset: 2px). Never remove outline without a replacement.",
              nodes=[{"selector": d["selector"], "name": d["name"], "tab_index": d["n"]} for d in no_indicator])
    if invisible:
        F.add("kbd:focus-on-hidden", url, sc=["2.4.3", "2.4.7"], impact="serious", status="fail",
              title="Keyboard focus lands on invisible elements",
              fix="Hidden content (closed mobile menu, off-canvas panel, closed accordion, slider clones) must not be focusable: use display:none, visibility:hidden or the inert attribute while closed.",
              nodes=[{"selector": d["selector"], "name": d["name"], "tab_index": d["n"]} for d in invisible])
    if obscured:
        F.add("kbd:focus-obscured", url, sc=["2.4.11"], impact="serious", status="fail",
              title="Focused element completely hidden behind a sticky or fixed element",
              fix="Add scroll-padding-top equal to the sticky header height, and make sure banners or chat widgets do not cover focused elements.",
              nodes=[{"selector": d["selector"], "name": d["name"], "blocker": d["blocker"], "tab_index": d["n"]} for d in obscured])
    if skip and not skip["present"]:
        F.add("kbd:no-skip-link", url, sc=["2.4.1"], impact="moderate", status="review",
              title="No skip link as first focusable element",
              fix="Add a 'Naar de inhoud' skip link as the first focusable element, visible on focus, pointing to <main id=...>. Many themes have this built in.",
              nodes=[{"first_focus": skip["first_focus"]}])
    elif skip and not skip["target_exists"]:
        F.add("kbd:skip-link-broken", url, sc=["2.4.1"], impact="serious", status="fail",
              title="Skip link target does not exist", fix="Point the skip link to an existing id on the main content.",
              nodes=[{"name": skip["name"]}])
    # order heuristic: large backward jumps in reading direction
    jumps = []
    vis_seq = [d for d in seq if d["visible"] and d["w"] > 0]
    for a, b in zip(vis_seq, vis_seq[1:]):
        if b["y"] < a["y"] - 400:
            jumps.append({"from": a["n"], "to": b["n"], "from_name": a["name"][:40], "to_name": b["name"][:40], "dy": round(b["y"] - a["y"])})

    # focus order map
    order_map = None
    try:
        full = ev / "focus-order.png"
        page.evaluate("() => scrollTo(0, 0)")
        page.screenshot(path=str(full), full_page=True, animations="disabled")
        img = Image.open(full).convert("RGB")
        if img.height > 12000:
            img = img.crop((0, 0, img.width, 12000))
        draw = ImageDraw.Draw(img)
        bad = {d["n"] for d in no_indicator} | {d["n"] for d in obscured}
        for d in vis_seq:
            col = (220, 0, 0) if d["n"] in bad else (0, 90, 255)
            draw.rectangle([d["x"], d["y"], d["x"] + d["w"], d["y"] + d["h"]], outline=col, width=2)
            by = d["y"] - 14 if d["y"] >= 14 else d["y"] + d["h"]  # badge below the box at the page top
            draw.rectangle([d["x"], by, d["x"] + 22, by + 14], fill=col)
            draw.text((d["x"] + 2, by + 1), str(d["n"]), fill=(255, 255, 255))
        img.save(full, optimize=True)
        order_map = str(full)
    except Exception:
        pass
    return {"tab_stops": len(seq), "max_tabs_reached": len(seq) >= max_tabs, "skip_link": skip, "backward_jumps": jumps[:15],
            "trap": bool(trap), "no_indicator": len(no_indicator), "invisible_focus": len(invisible), "obscured": len(obscured),
            "focus_order_map": order_map,
            "sequence": [{k: d[k] for k in ("n", "name", "tag", "role", "selector")} for d in seq]}


def structure_checks(F: Findings, url: str, s: dict, page, ev: Path, max_img_crops: int) -> dict:
    # headings
    levels = [h["level"] for h in s["headings"]]
    h1 = levels.count(1)
    skips = [(a, b) for a, b in zip(levels, levels[1:]) if b > a + 1]
    if h1 == 0:
        F.add("struct:no-h1", url, sc=["1.3.1", "2.4.6"], impact="moderate", status="review", title="Page has no h1",
              fix="Give every page exactly one h1 that describes the page (often the page title). Change the heading level in the builder, not only the style.")
    if skips:
        F.add("struct:heading-skip", url, sc=["1.3.1"], impact="minor", status="review", title="Heading levels are skipped",
              fix="Use heading levels in order (h2 after h1, h3 after h2). Choose the level by structure and set the look with CSS or builder typography.",
              nodes=[{"skip": f"h{a} -> h{b}"} for a, b in skips[:10]])
    # landmarks
    if not s["landmarks"].get("main"):
        F.add("struct:no-main", url, sc=["1.3.1", "2.4.1"], impact="moderate", status="review", title="No <main> landmark",
              fix="Wrap the page content in <main id=\"main\"> (theme template) so screen reader users can jump to it.")
    # links
    by_text: dict[str, set] = {}
    for l in s["links"]:
        t = (l["name"] or l["text"]).strip().lower().rstrip(" .›»>→")
        if t in AMBIGUOUS_LINKS:
            by_text.setdefault(t, set()).add(l["href"])
    amb = {t: h for t, h in by_text.items() if len(h) > 1}
    if amb:
        F.add("struct:ambiguous-links", url, sc=["2.4.4"], impact="moderate", status="review",
              title="Several links with the same vague text lead to different pages",
              fix="Make the link text specific (\"Lees meer over knippen\"), or add visually hidden text. If you use aria-label, it must contain the visible words (2.5.3).",
              nodes=[{"text": t, "targets": len(h)} for t, h in amb.items()])
    # forms
    personal = re.compile(r"(e-?mail|naam|name|tel|phone|telefoon|mobiel|adres|address|straat|street|postcode|zip|plaats|city|woonplaats|land|country|bedrijf|company|organization)", re.I)
    missing_ac, no_label = [], []
    for f in s["fields"]:
        key = f"{f['nameAttr']} {f['id']} {f['label']} {f['type']}"
        if (f["type"] in ("email", "tel") or personal.search(key)) and not f["autocomplete"] and f["type"] not in ("checkbox", "radio"):
            missing_ac.append({"selector": f["selector"], "label": f["label"], "type": f["type"]})
        if not f["visibleLabel"] and f["placeholder"] and f["type"] not in ("checkbox", "radio", "search"):
            no_label.append({"selector": f["selector"], "placeholder": f["placeholder"]})
    if missing_ac:
        F.add("form:autocomplete-missing", url, sc=["1.3.5"], impact="moderate", status="fail",
              title="Personal data fields without autocomplete attribute",
              fix="Add autocomplete tokens (name, given-name, family-name, email, tel, street-address, postal-code, address-level2, organization). Most form plugins have an autocomplete setting per field.",
              nodes=missing_ac[:20])
    if no_label:
        F.add("form:placeholder-as-label", url, sc=["3.3.2", "1.3.1"], impact="serious", status="fail",
              title="Form field uses only a placeholder, no visible label",
              fix="Show a visible <label> for every field (most form plugins have a \"show label\" option). A placeholder disappears while typing and often has too little contrast.",
              nodes=no_label[:20])
    # media
    for m in s["media"]:
        if m["autoplay"] and not m["muted"] and m["tag"] in ("audio", "video"):
            F.add("media:autoplay-sound", url, sc=["1.4.2"], impact="serious", status="fail", title="Media plays sound automatically",
                  fix="Do not autoplay sound; or provide an obvious pause/mute control at the start of the page.", nodes=[m])
        if m["tag"] == "video" and m["autoplay"] and (m["loop"] or (m["duration"] or 99) > 5) and not m["controls"] and s["pauseControls"] == 0:
            F.add("media:autoplay-no-pause", url, sc=["2.2.2"], impact="serious", status="fail",
                  title="Auto-playing video (longer than 5s) without pause control",
                  fix="Add a visible pause button (also for muted background video), or stop it after 5 seconds.", nodes=[m])
        if m["tag"] == "video" and not m["muted"] and "captions" not in m["tracks"] and "subtitles" not in m["tracks"]:
            F.add("media:no-captions-track", url, sc=["1.2.2"], impact="serious", status="review", title="Video without captions track",
                  fix="Add captions (WebVTT <track kind=\"captions\">), or check that the video has no speech.", nodes=[m])
    embeds = [f for f in s["iframes"] if re.search(r"youtube|youtu\.be|vimeo|wistia|videopress", f["src"], re.I)]
    if embeds:
        F.add("media:embedded-video", url, sc=["1.2.2", "1.2.3", "1.2.5"], impact="moderate", status="review",
              title="Embedded video: check captions and audio description by hand",
              fix="Check that each video has correct (not only auto-generated) captions; add a transcript or audio description if visuals carry information.",
              nodes=[{"src": f["src"][:150], "title": f["title"]} for f in embeds])
    # images: suspicious alt texts + crops for Claude's alt review
    sus, review = [], []
    fn_like = re.compile(r"(^(img|dsc|image|photo|foto|afbeelding|picture|screenshot|untitled)[-_ ]?\d*|\.(jpe?g|png|webp|gif)$|^[\w-]+-\d{2,}x\d{2,}$|^\d+$)", re.I)
    for im in s["images"]:
        if im["tag"] != "img" or im["hidden"]:
            continue
        alt = im["alt"]
        if alt and (fn_like.search(alt.strip()) or len(alt) > 160 or alt.strip().lower() in ("logo", "image", "afbeelding", "foto", "icon", "banner")):
            sus.append({"selector": im["selector"], "alt": alt[:160], "src": im["src"][-80:]})
        if alt is not None and im["w"] >= 40 and im["h"] >= 40 and len(review) < max_img_crops:
            c = crop_to(page, im, ev / f"img-{len(review) + 1:02d}.png", pad=0, max_h=500)
            review.append({"crop": c, "alt": alt, "in_link": im["inLink"], "link_text": im["linkText"], "selector": im["selector"], "size": f"{im['w']}x{im['h']}"})
    if sus:
        F.add("img:suspicious-alt", url, sc=["1.1.1"], impact="serious", status="fail", title="Alt text looks like a file name or is meaningless",
              fix="Write alt text that conveys the purpose of the image (Respira update_media / update_media_batch for media library alts). Decorative images get alt=\"\".",
              nodes=sus[:20])
    # title / lang
    if s["lang"] and not re.match(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$", s["lang"]):
        F.add("struct:lang-invalid", url, sc=["3.1.1"], impact="serious", status="fail", title=f"Invalid lang attribute: {s['lang']}",
              fix="Use a valid BCP 47 code such as nl or nl-NL (WordPress Settings > General > Site language).")
    return {"image_review": review}


def reflow_and_mobile(F: Findings, url: str, browser, cfg: dict, axe_src: str, ev: Path) -> dict:
    ctx = browser.new_context(viewport={"width": 375, "height": 740}, device_scale_factor=1, is_mobile=True, has_touch=True,
                              user_agent=UA, locale="nl-NL", ignore_https_errors=cfg["ignore_https_errors"])
    page = ctx.new_page()
    out = {}
    try:
        page.goto(url, wait_until="load", timeout=cfg["timeout_ms"])
        settle(page, cfg["timeout_ms"])
        accept_cookies(page)
        page.add_script_tag(content=JS_HELPERS)
        res = run_axe(page, axe_src, rules=["target-size"])
        crop_budget = [6]
        axe_findings(F, url, res, page, ev, "375", crop_budget)
        # reflow at 320
        page.set_viewport_size({"width": 320, "height": 640})
        page.wait_for_timeout(700)
        rf = page.evaluate(JS_REFLOW, 320)
        out["reflow"] = rf
        shot = ev / "reflow-320.png"
        page.screenshot(path=str(shot), full_page=False)
        out["reflow_screenshot"] = str(shot)
        if rf["docWidth"] > 322:
            F.add("reflow:horizontal-scroll", url, sc=["1.4.10"], impact="serious", status="fail",
                  title=f"Horizontal scrolling at 320px width (page is {rf['docWidth']}px wide)",
                  fix="Find the element that is too wide (fixed widths, large images, long words or URLs, tables, iframes) and make it responsive: max-width:100%, flexible widths, overflow-wrap:anywhere.",
                  nodes=rf["offenders"] or [{"docWidth": rf["docWidth"]}])
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
    finally:
        ctx.close()
    return out


def text_spacing(F: Findings, url: str, page, ev: Path) -> dict:
    before = {c["selector"] for c in page.evaluate(JS_CLIPPED)}
    page.add_style_tag(content=TEXT_SPACING_CSS)
    page.wait_for_timeout(300)
    after = page.evaluate(JS_CLIPPED)
    new = [c for c in after if c["selector"] not in before]
    if new:
        F.add("spacing:text-clipped", url, sc=["1.4.12"], impact="serious", status="fail",
              title="Text is clipped when text spacing is increased",
              fix="Avoid fixed heights and overflow:hidden on text containers (buttons, cards, menu items); use min-height and padding instead.",
              nodes=new[:15])
    return {"clipped_with_spacing": len(new)}


def motion_check(F: Findings, url: str, page, ev: Path, s: dict) -> dict:
    """Content that changes on its own within ~6 seconds in the first viewport."""
    page.evaluate("() => scrollTo(0, 0)")
    page.mouse.move(1, 1)
    grab = lambda: np.asarray(Image.open(io.BytesIO(page.screenshot())).convert("L"), dtype=np.int16)  # noqa: E731
    a = grab()
    diff = np.zeros(a.shape, dtype=bool)
    b = a
    for _ in range(5):  # several frames: a slider can be back on the same slide after 6s
        page.wait_for_timeout(1300)
        b = grab()
        if b.shape == a.shape:
            diff |= np.abs(a - b) > 25
    ratio = float(diff.mean())
    if int(diff.sum()) < 150:
        return {"moving": False}
    ys, xs = np.nonzero(diff)
    box = {"x": int(xs.min()), "y": int(ys.min()), "w": int(xs.max() - xs.min()), "h": int(ys.max() - ys.min())}
    shot = ev / "motion.png"
    Image.fromarray(b.astype(np.uint8)).convert("RGB").crop((box["x"], box["y"], box["x"] + box["w"] + 1, box["y"] + box["h"] + 1)).save(shot)
    F.add("motion:auto-moving", url, sc=["2.2.2"], impact="serious" if s["pauseControls"] == 0 else "minor",
          status="review", title="Content moves or changes by itself (slider, carousel, ticker or video)",
          fix="Auto-moving content longer than 5 seconds needs a visible pause/stop button, or turn off autoplay (often the better choice for sliders).",
          nodes=[{"area": box, "changed_pct": round(ratio * 100, 1), "pause_controls_found": s["pauseControls"], "crop": str(shot)}])
    return {"moving": True, "area": box}


def audit_page(url: str, browser, cfg: dict, axe_src: str, out: Path, F: Findings, idx: int) -> dict:
    ev = out / "evidence" / f"{idx:02d}-{slug(url)}"
    ev.mkdir(parents=True, exist_ok=True)
    rec = {"url": url, "evidence_dir": str(ev)}
    t0 = time.time()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=1, user_agent=UA, locale="nl-NL",
                              timezone_id="Europe/Amsterdam", ignore_https_errors=cfg["ignore_https_errors"])
    page = ctx.new_page()
    page.set_default_timeout(cfg["timeout_ms"])
    try:
        resp = page.goto(url, wait_until="load", timeout=cfg["timeout_ms"])
        rec["http_status"] = resp.status if resp else None
        settle(page, cfg["timeout_ms"])
        page.add_script_tag(content=JS_HELPERS)
        page.screenshot(path=str(ev / "desktop.png"), full_page=True, animations="disabled")
        rec["screenshot"] = str(ev / "desktop.png")
        # 1. axe with cookie banner present (the banner must be accessible too)
        crop_budget = [cfg["max_crops"]]
        axe_findings(F, url, run_axe(page, axe_src), page, ev, "1280", crop_budget)
        rec["cookie_banner_closed_with"] = accept_cookies(page)
        page.wait_for_timeout(300)
        # 2. structure + ARIA snapshot
        s = page.evaluate(JS_STRUCTURE)
        rec["structure"] = {k: s[k] for k in ("title", "lang", "landmarks", "generator")}
        rec["structure"]["headings"] = s["headings"][:60]
        rec["structure"]["counts"] = {k: len(s[k]) for k in ("links", "images", "fields", "media", "iframes", "tables")}
        try:
            snap = page.locator("body").aria_snapshot(timeout=15000)
            (ev / "aria-snapshot.yaml").write_text(snap)
            rec["aria_snapshot"] = str(ev / "aria-snapshot.yaml")
        except Exception:
            pass
        rec.update(structure_checks(F, url, s, page, ev, cfg["max_image_crops"]))
        # 3. motion (before keyboard so nothing has focus)
        if cfg["motion"]:
            rec["motion"] = motion_check(F, url, page, ev, s)
        # 4. keyboard
        rec["keyboard"] = keyboard_test(F, url, page, ev, cfg["max_tabs"])
        # 5. text spacing (mutates styles, keep last)
        rec["text_spacing"] = text_spacing(F, url, page, ev)
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
    finally:
        ctx.close()
    if "error" not in rec:
        rec["mobile"] = reflow_and_mobile(F, url, browser, cfg, axe_src, ev)
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


# --------------------------------------------------------------------------- reporting
def write_markdown(out: Path, report: dict, lang: str):
    nl = lang == "nl"
    s = report["summary"]
    L = []
    L.append(f"# {'WCAG 2.2 AA-audit' if nl else 'WCAG 2.2 AA audit'}: {report['site']}")
    L.append("")
    L.append(f"{'Datum' if nl else 'Date'}: {report['created_at'][:10]} · {'Pagina' if nl else 'Pages'}: {len(report['pages'])} · axe-core {report['axe_version']}")
    L.append("")
    L.append(f"**{'Fouten' if nl else 'Failures'}: {s['fail_rules']}** ({'kritiek' if nl else 'critical'} {s['by_impact'].get('critical', 0)}, "
             f"{'ernstig' if nl else 'serious'} {s['by_impact'].get('serious', 0)}, {'matig' if nl else 'moderate'} {s['by_impact'].get('moderate', 0)}, "
             f"{'klein' if nl else 'minor'} {s['by_impact'].get('minor', 0)}) · "
             f"{'Te beoordelen' if nl else 'Needs review'}: {s['review_rules']} · {'Sitebreed (template)' if nl else 'Template-wide'}: {s['template_wide']}")
    L.append("")
    L.append("> " + ("Geautomatiseerde tests vinden een deel van de problemen. Dit rapport is de basis; de handmatige checklist onderaan is nodig voor een volledige WCAG-beoordeling."
                     if nl else "Automated testing finds only part of the issues. The manual checklist below is required for a full WCAG evaluation."))
    L.append("")
    for status, head in (("fail", "Fouten" if nl else "Failures"), ("review", "Te beoordelen" if nl else "Needs review")):
        items = [i for i in report["findings"] if i["status"] == status and not i["best_practice"]]
        if not items:
            continue
        L.append(f"## {head}")
        L.append("")
        for i in items:
            scs = ", ".join(sc_name(x, lang) for x in i["sc"]) or "best practice"
            tw = " · **sitebreed**" if i["template_wide"] and nl else " · **template-wide**" if i["template_wide"] else ""
            L.append(f"### [{i['impact']}] {i['title']}")
            L.append(f"{scs} · {i['page_count']} {'pagina' if nl else 'page(s)'} · {i['node_count']} {'elementen' if nl else 'elements'}{tw} · `{i['rule']}`")
            if i["fix"]:
                L.append(f"\n{'Oplossing' if nl else 'Fix'}: {i['fix']}")
            ex = i["pages"][0]["nodes"][:3]
            for n in ex:
                bits = [f"`{n['selector']}`" if n.get("selector") else ""]
                if n.get("contrast"):
                    c = n["contrast"]
                    bits.append(f"{c['fgColor']} op {c['bgColor']} = {c['contrastRatio']}:1 (nodig {c['expectedContrastRatio']})" if nl else
                                f"{c['fgColor']} on {c['bgColor']} = {c['contrastRatio']}:1 (needs {c['expectedContrastRatio']})")
                for k in ("name", "text", "alt", "label", "placeholder", "skip", "blocker"):
                    if n.get(k):
                        bits.append(f"{k}: {str(n[k])[:80]}")
                L.append("- " + " · ".join(b for b in bits if b))
            L.append(f"- {'Voorbeeldpagina' if nl else 'Example page'}: {i['pages'][0]['url']}")
            L.append("")
    bp = [i for i in report["findings"] if i["best_practice"]]
    if bp:
        L.append(f"## {'Best practices (geen WCAG-eis)' if nl else 'Best practices (not WCAG requirements)'}")
        for i in bp:
            L.append(f"- [{i['impact']}] {i['title']} ({i['page_count']} p.) `{i['rule']}`")
        L.append("")
    L.append(f"## {'Per pagina' if nl else 'Per page'}")
    L.append("")
    L.append("| # | URL | Status | Tab stops | Skip link | Reflow 320 | Motion |")
    L.append("|---|---|---|---|---|---|---|")
    for n, p in enumerate(report["pages"], 1):
        if p.get("error"):
            L.append(f"| {n} | {p['url']} | ERROR {p['error'][:60]} | | | | |")
            continue
        kb = p.get("keyboard", {})
        sk = kb.get("skip_link") or {}
        rf = (p.get("mobile") or {}).get("reflow") or {}
        L.append(f"| {n} | {p['url']} | {p.get('http_status')} | {kb.get('tab_stops')} | {'ja' if sk.get('present') else 'nee'} | "
                 f"{rf.get('docWidth', '?')}px | {'ja' if (p.get('motion') or {}).get('moving') else 'nee'} |")
    L.append("")
    L.append(f"## {'Handmatige checklist' if nl else 'Manual checklist'}")
    L.append("")
    covered = {sc for i in report["findings"] for sc in i["sc"]}
    for sc, (lvl, en, nlname, auto, how) in CRITERIA.items():
        if auto == "auto":
            continue
        flag = " ⚠️" if sc in covered else ""
        L.append(f"- [ ] **{sc} {nlname if nl else en}** ({lvl}, {auto}){flag}: {how}")
    (out / "report.md").write_text("\n".join(L))


def cmd_audit(args):
    if not AXE_PATH.exists():
        sys.exit(f"axe-core not found at {AXE_PATH}")
    axe_src = AXE_PATH.read_text()
    axe_version = re.search(r"axe v([\d.]+)", axe_src[:200])
    urls: list[str] = []
    notes = []
    if args.urls:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]
    if args.site:
        found, errs = sitemap_urls(args.site, args.limit)
        if not found:
            notes.append({"sitemap_errors": errs})
            found = [args.site.rstrip("/") + "/"]
        urls = list(dict.fromkeys(urls + found))
    if not urls:
        sys.exit("Give --urls or --site.")
    host = urlparse(urls[0]).netloc
    name = args.name or host.replace("www.", "")
    out = Path(args.out or os.environ.get("WCAG_ROOT", "wcag-audits")).resolve() / name / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    cfg = {"timeout_ms": args.timeout * 1000, "max_tabs": args.max_tabs, "max_crops": 20, "max_image_crops": args.image_crops,
           "motion": not args.no_motion, "ignore_https_errors": args.insecure}
    F = Findings()
    pages = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for i, u in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] {u}", file=sys.stderr)
                rec = audit_page(u, browser, cfg, axe_src, out, F, i)
                if rec.get("error"):
                    print(f"   ERROR {rec['error']}", file=sys.stderr)
                pages.append(rec)
        finally:
            browser.close()
    findings = F.finalize(len([p for p in pages if not p.get("error")]))
    by_impact: dict[str, int] = {}
    for f in findings:
        if f["status"] == "fail" and not f["best_practice"]:
            by_impact[f["impact"]] = by_impact.get(f["impact"], 0) + 1
    summary = {
        "pages": len(pages), "pages_failed_to_load": sum(1 for p in pages if p.get("error")),
        "pages_http_error": [p["url"] for p in pages if (p.get("http_status") or 200) >= 400],
        "fail_rules": sum(1 for f in findings if f["status"] == "fail" and not f["best_practice"]),
        "review_rules": sum(1 for f in findings if f["status"] == "review" and not f["best_practice"]),
        "template_wide": sum(1 for f in findings if f["template_wide"] and not f["best_practice"]),
        "by_impact": by_impact,
        "failed_sc": sorted({sc for f in findings if f["status"] == "fail" for sc in f["sc"]}, key=lambda x: [int(n) for n in x.split(".")]),
    }
    report = {"site": name, "created_at": dt.datetime.now().isoformat(timespec="seconds"), "standard": "WCAG 2.2 AA",
              "axe_version": axe_version.group(1) if axe_version else "?", "summary": summary, "notes": notes,
              "findings": findings, "pages": pages}
    (out / "findings.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    write_markdown(out, report, args.lang)
    print(json.dumps({
        "out_dir": str(out), "report_md": str(out / "report.md"), "findings_json": str(out / "findings.json"),
        "summary": summary, "notes": notes,
        "top_findings": [{"rule": f["rule"], "status": f["status"], "impact": f["impact"], "sc": f["sc"], "title": f["title"],
                          "pages": f["page_count"], "elements": f["node_count"], "template_wide": f["template_wide"]}
                         for f in findings if not f["best_practice"]][:25],
        "review_evidence": {
            "focus_order_maps": [p["keyboard"]["focus_order_map"] for p in pages if p.get("keyboard", {}).get("focus_order_map")],
            "image_crops_for_alt_review": sum(len(p.get("image_review", [])) for p in pages),
            "aria_snapshots": [p["aria_snapshot"] for p in pages if p.get("aria_snapshot")],
        },
        "page_errors": [{"url": p["url"], "error": p["error"]} for p in pages if p.get("error")],
    }, indent=2, ensure_ascii=False))
    if summary["pages_failed_to_load"] == len(pages):
        return 2
    return 1 if summary["fail_rules"] else 0


def cmd_diff(args):
    old = json.loads(Path(args.old).read_text())
    new = json.loads(Path(args.new).read_text())

    def keys(rep):
        ks = set()
        for f in rep["findings"]:
            if f["status"] != "fail" or f["best_practice"]:
                continue
            for p in f["pages"]:
                for n in p["nodes"]:
                    ks.add((f["rule"], p["url"], n.get("selector") or json.dumps(n, sort_keys=True)[:120]))
        return ks

    a, b = keys(old), keys(new)
    titles = {f["rule"]: f["title"] for f in old["findings"] + new["findings"]}

    def group(ks):
        g: dict[str, int] = {}
        for r, _, _ in ks:
            g[r] = g.get(r, 0) + 1
        return [{"rule": r, "title": titles.get(r, r), "elements": n} for r, n in sorted(g.items(), key=lambda x: -x[1])]

    print(json.dumps({"fixed": group(a - b), "remaining": group(a & b), "new": group(b - a),
                      "counts": {"fixed": len(a - b), "remaining": len(a & b), "new": len(b - a)}}, indent=2, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("audit")
    p.add_argument("--urls", help="comma-separated URLs")
    p.add_argument("--site", help="site root; pages are sampled from the sitemap")
    p.add_argument("--limit", type=int, default=10, help="max pages from the sitemap (default 10)")
    p.add_argument("--name", help="folder name (default: host)")
    p.add_argument("--out", help="output root (default ./wcag-audits or $WCAG_ROOT)")
    p.add_argument("--lang", default="nl", choices=["nl", "en"], help="report language")
    p.add_argument("--max-tabs", type=int, default=120)
    p.add_argument("--image-crops", type=int, default=15, help="image crops per page for alt review")
    p.add_argument("--timeout", type=int, default=45, help="page timeout in seconds")
    p.add_argument("--no-motion", action="store_true", help="skip the 6 second motion check")
    p.add_argument("--insecure", action="store_true", help="ignore HTTPS errors (staging)")
    p = sub.add_parser("diff")
    p.add_argument("old")
    p.add_argument("new")
    args = ap.parse_args(argv)
    sys.exit({"audit": cmd_audit, "diff": cmd_diff}[args.cmd](args) or 0)


if __name__ == "__main__":
    main()
