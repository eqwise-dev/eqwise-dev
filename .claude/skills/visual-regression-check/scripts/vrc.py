#!/usr/bin/env python3
"""vrc.py - visual regression check for (WordPress) websites.

Captures stabilised full-page screenshots with Playwright, keeps an approved
baseline per client, diffs new captures pixel by pixel and writes a JSON + HTML
report with cropped before/after images of every changed region, so an AI agent
(or a person) can triage only what changed.

Commands
  init     <client> --site URL [--limit N]   create config from the sitemap
  baseline <client> [--pages a,b]            capture the approved baseline
  check    <client> [--pages a,b]            capture now, diff against baseline
  approve  <client> [--run ID] [--pages a,b] promote a run's captures to baseline
  compare  --a URL --b URL [--name X]        diff two URLs (live vs draft, prod vs staging)
  status   <client>                          show baseline age and latest run

Exit codes: 0 = no visual changes, 1 = changes found, 2 = errors.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import numpy as np
    import yaml
    from PIL import Image, ImageDraw
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover
    sys.exit(
        f"Missing dependency: {exc.name}. Install with:\n"
        "  pip install playwright pillow numpy pyyaml && python -m playwright install chromium"
    )

Image.MAX_IMAGE_PIXELS = None

DEFAULTS = {
    "widths": [375, 768, 1440],
    "browsers": ["chromium"],
    "full_page": True,
    "max_height": 15000,
    "threshold": 0.1,          # per-pixel colour tolerance, 0..1 (pixelmatch scale)
    "ignore_antialiasing": True,  # tolerate 1px shifts / anti-aliasing edges
    "max_diff_ratio": 0.0005,  # page counts as changed above this share of pixels
    "min_region_px": 24,       # ignore change regions with fewer changed pixels
    "wait_ms": 800,
    "timeout_ms": 45000,
    "hide": [
        # cookie banners and chat widgets common on Dutch WordPress sites
        "#cmplz-cookiebanner-container", ".cmplz-cookiebanner", ".cmplz-manage-consent",
        ".cky-consent-container", ".cky-btn-revisit-wrapper", "#CybotCookiebotDialog",
        "#BorlabsCookieBox", "#cookie-law-info-bar", "#moove_gdpr_cookie_info_bar",
        ".real-cookie-banner", "#tidio-chat", ".crisp-client", "#hubspot-messages-iframe-container",
        "#wpadminbar", ".grecaptcha-badge",
    ],
    "mask": ["video", "iframe"],
    "css": "",
}

STABILISE_CSS = """
*, *::before, *::after {
  animation-duration: 0s !important; animation-delay: 0s !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0s !important; transition-delay: 0s !important;
  caret-color: transparent !important; scroll-behavior: auto !important;
}
[data-aos], .aos-init, .elementor-invisible, .et_animated, .et-waypoint, .wow {
  opacity: 1 !important; visibility: visible !important; transform: none !important;
}
"""

UA = "Mozilla/5.0 (EQwise visual-regression-check)"


# --------------------------------------------------------------------------- paths
def root_dir(args) -> Path:
    return Path(args.root or os.environ.get("VRC_ROOT") or "visual-tests").resolve()


def client_dir(args, client: str) -> Path:
    return root_dir(args) / client


def load_config(args, client: str) -> dict:
    path = client_dir(args, client) / "config.yaml"
    if not path.exists():
        sys.exit(f"No config at {path}. Run: vrc.py init {client} --site https://...")
    own = yaml.safe_load(path.read_text()) or {}
    cfg = {**DEFAULTS, **own}
    if not own.get("replace_default_selectors"):
        for key in ("hide", "mask"):  # client lists add to the built-in defaults
            cfg[key] = list(dict.fromkeys(DEFAULTS[key] + list(own.get(key) or [])))
    if not cfg.get("pages"):
        sys.exit(f"{path} has no pages.")
    return cfg


def slugify(path: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", urlparse(path).path.strip("/")).strip("-").lower()
    return s or "home"


def select_pages(cfg: dict, only: str | None) -> list[dict]:
    pages = cfg["pages"]
    if not only:
        return pages
    wanted = {p.strip() for p in only.split(",") if p.strip()}
    sel = [p for p in pages if p["name"] in wanted]
    missing = wanted - {p["name"] for p in sel}
    if missing:
        sys.exit(f"Unknown page(s): {', '.join(sorted(missing))}")
    return sel


def page_url(cfg: dict, page: dict) -> str:
    return page.get("url") or urljoin(cfg["base_url"].rstrip("/") + "/", page.get("path", "/").lstrip("/"))


def shot_name(page: str, width: int) -> str:
    return f"{page}@{width}.png"


# --------------------------------------------------------------------------- capture
class Capturer:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._pw = sync_playwright().start()
        self._browsers = {}

    def browser(self, name: str):
        if name not in self._browsers:
            launcher = getattr(self._pw, name, None)
            if launcher is None:
                raise ValueError(f"Unknown browser {name!r} (use chromium, firefox or webkit)")
            self._browsers[name] = launcher.launch()
        return self._browsers[name]

    def close(self):
        for b in self._browsers.values():
            b.close()
        self._pw.stop()

    def capture(self, url: str, width: int, browser: str, out: Path, page_cfg: dict | None = None) -> dict:
        cfg, page_cfg = self.cfg, page_cfg or {}
        ctx_opts = {
            "viewport": {"width": width, "height": 900},
            "device_scale_factor": 1,
            "reduced_motion": "reduce",
            "locale": cfg.get("locale", "nl-NL"),
            "timezone_id": cfg.get("timezone", "Europe/Amsterdam"),
            "user_agent": UA if browser == "chromium" else None,
            "ignore_https_errors": bool(cfg.get("ignore_https_errors", False)),
        }
        creds = cfg.get("http_credentials_env")
        if creds:
            ctx_opts["http_credentials"] = {"username": os.environ.get(creds[0], ""), "password": os.environ.get(creds[1], "")}
        ctx = self.browser(browser).new_context(**{k: v for k, v in ctx_opts.items() if v is not None})
        page = ctx.new_page()
        page.set_default_timeout(cfg["timeout_ms"])
        t0 = time.time()
        try:
            resp = page.goto(url, wait_until="load", timeout=cfg["timeout_ms"])
            status = resp.status if resp else None
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            hide = list(cfg["hide"]) + list(page_cfg.get("hide", []))
            css = STABILISE_CSS + cfg.get("css", "") + page_cfg.get("css", "")
            if hide:
                css += "\n" + ",\n".join(hide) + " { display: none !important; }"
            page.add_style_tag(content=css)
            # scroll through the page so lazy images and reveal-on-scroll content load
            page.evaluate(
                """async () => {
                    const step = Math.max(300, window.innerHeight * 0.8);
                    const max = Math.min(document.documentElement.scrollHeight, 30000);
                    for (let y = 0; y < max; y += step) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
                    window.scrollTo(0, 0);
                    document.querySelectorAll('img[loading="lazy"]').forEach(i => i.loading = 'eager');
                    await Promise.race([
                        Promise.all([...document.images].filter(i => !i.complete).map(i => new Promise(r => { i.onload = i.onerror = r; }))),
                        new Promise(r => setTimeout(r, 8000)),
                    ]);
                    if (document.fonts) await document.fonts.ready;
                }"""
            )
            page.wait_for_timeout(cfg["wait_ms"])
            mask_sel = list(cfg["mask"]) + list(page_cfg.get("mask", []))
            masks = [page.locator(s) for s in mask_sel]
            shot = {"path": str(out), "full_page": cfg["full_page"], "animations": "disabled", "caret": "hide",
                    "mask": masks, "mask_color": "#FF00FF"}
            if cfg["full_page"]:
                height = page.evaluate("document.documentElement.scrollHeight")
                if height > cfg["max_height"]:
                    shot["clip"] = {"x": 0, "y": 0, "width": width, "height": cfg["max_height"]}
            out.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(**shot)
            return {"ok": True, "http_status": status, "seconds": round(time.time() - t0, 1)}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc).splitlines()[0]}"}
        finally:
            ctx.close()


# --------------------------------------------------------------------------- diff
def _yiq(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.29889531 * r + 0.58662247 * g + 0.11448223 * b
    i = 0.59597799 * r - 0.27417610 * g - 0.32180189 * b
    q = 0.21147017 * r - 0.52261711 * g + 0.31114694 * b
    return np.stack([y, i, q], axis=-1)


def _delta(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = a - b
    return 0.5053 * d[..., 0] ** 2 + 0.299 * d[..., 1] ** 2 + 0.1957 * d[..., 2] ** 2


def _changed(a: np.ndarray, b: np.ndarray, limit: float, tolerate_shift: bool) -> np.ndarray:
    """Boolean mask of pixels that differ. With tolerate_shift a pixel only counts
    when no pixel in the other image's 3x3 neighbourhood matches it (both ways),
    which removes anti-aliasing noise and sub-pixel shifts."""
    ya, yb = _yiq(a), _yiq(b)
    direct = _delta(ya, yb) > limit
    if not tolerate_shift or not direct.any():
        return direct

    def unmatched(src, ref):
        h, w = src.shape[:2]
        pad = np.pad(ref, ((1, 1), (1, 1), (0, 0)), mode="edge")
        best = np.full((h, w), np.inf, dtype=np.float32)
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                np.minimum(best, _delta(src, pad[dy:dy + h, dx:dx + w]), out=best)
        return best > limit

    return direct & unmatched(ya, yb) & unmatched(yb, ya)


def _regions(mask: np.ndarray, cell: int = 16, min_px: int = 24) -> list[dict]:
    """Group changed pixels into rectangles via connected components on a coarse grid."""
    h, w = mask.shape
    gh, gw = -(-h // cell), -(-w // cell)
    padded = np.zeros((gh * cell, gw * cell), dtype=bool)
    padded[:h, :w] = mask
    counts = padded.reshape(gh, cell, gw, cell).sum(axis=(1, 3))
    grid = counts > 0
    seen = np.zeros_like(grid)
    out = []
    for gy, gx in zip(*np.nonzero(grid)):
        if seen[gy, gx]:
            continue
        q, cells = deque([(gy, gx)]), []
        seen[gy, gx] = True
        while q:
            y, x = q.popleft()
            cells.append((y, x))
            for ny in range(y - 2, y + 3):  # 2-cell reach merges nearby fragments
                for nx in range(x - 2, x + 3):
                    if 0 <= ny < gh and 0 <= nx < gw and grid[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
        ys, xs = [c[0] for c in cells], [c[1] for c in cells]
        px = int(sum(counts[c] for c in cells))
        if px < min_px:
            continue
        x0, y0 = min(xs) * cell, min(ys) * cell
        x1, y1 = min((max(xs) + 1) * cell, w), min((max(ys) + 1) * cell, h)
        out.append({"x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0), "changed_px": px})
    out.sort(key=lambda r: r["changed_px"], reverse=True)
    return out


def diff_images(base_path: Path, cur_path: Path, out_dir: Path, stem: str, cfg: dict) -> dict:
    base = Image.open(base_path).convert("RGB")
    cur = Image.open(cur_path).convert("RGB")
    w = max(base.width, cur.width)
    # widths normally match (fixed viewport); pad with magenta so extra area counts as changed
    a = np.full((base.height, w, 3), (255, 0, 255), dtype=np.uint8)
    b = np.full((cur.height, w, 3), (255, 0, 255), dtype=np.uint8)
    a[:, : base.width] = np.asarray(base)
    b[:, : cur.width] = np.asarray(cur)
    h = cur.height  # all masks and regions are in current-image coordinates
    limit = 35215 * cfg["threshold"] ** 2
    delta = cur.height - base.height

    def aligned_mask(offset: int) -> np.ndarray:
        """Changed pixels of current row y vs baseline row y - offset; rows without a
        counterpart in the baseline count as changed."""
        m = np.ones((h, w), dtype=bool)
        lo, hi = max(0, offset), min(h, base.height + offset)
        stripe = 1024  # diff in stripes (1px overlap) to keep memory low on long pages
        for y0 in range(lo, hi, stripe):
            y1 = min(hi, y0 + stripe)
            s0, s1 = max(lo, y0 - 1), min(hi, y1 + 1)
            part = _changed(a[s0 - offset:s1 - offset].astype(np.float32), b[s0:s1].astype(np.float32),
                            limit, cfg["ignore_antialiasing"])
            m[y0:y1] = part[y0 - s0: y0 - s0 + (y1 - y0)]
        return m

    mask = aligned_mask(0)
    if delta and cfg.get("shift_compensation", True):
        # content inserted or removed above pushes everything below it; a pixel only
        # counts when it also differs with the page aligned at the bottom
        mask &= aligned_mask(delta)
    changed = int(mask.sum())
    ratio = changed / float(w * h)
    regions = _regions(mask, min_px=cfg["min_region_px"]) if changed else []
    regions_px = sum(r["changed_px"] for r in regions)
    is_changed = bool(regions) and (ratio > cfg["max_diff_ratio"] or base.size != cur.size)
    result = {
        "changed": is_changed,
        "diff_ratio": round(ratio, 6),
        "changed_px": changed,
        "changed_px_in_regions": regions_px,
        "size_baseline": [base.width, base.height],
        "size_current": [cur.width, cur.height],
        "height_delta": delta,
        "shift_compensated": bool(delta and cfg.get("shift_compensation", True)),
        "regions": [],
    }
    if not is_changed:
        return result

    out_dir.mkdir(parents=True, exist_ok=True)
    # overview: faded current image, changed pixels red, regions boxed
    faded = (b * 0.25 + 191).astype(np.uint8)
    faded[mask] = (230, 0, 0)
    ov = Image.fromarray(faded)
    draw = ImageDraw.Draw(ov)
    for n, r in enumerate(regions[:30], 1):
        draw.rectangle([r["x"] - 3, r["y"] - 3, r["x"] + r["w"] + 3, r["y"] + r["h"] + 3], outline=(0, 90, 255), width=3)
        draw.text((r["x"] + 4, max(0, r["y"] - 16)), f"#{n}", fill=(0, 90, 255))
    diff_path = out_dir / f"{stem}.diff.png"
    ov.save(diff_path, optimize=True)
    result["diff_image"] = str(diff_path)

    # per-region side-by-side crops: baseline | current | diff
    for n, r in enumerate(regions[: cfg.get("max_regions", 12)], 1):
        pad = 40
        x0, y0 = max(0, r["x"] - pad), max(0, r["y"] - pad)
        x1, y1 = min(w, r["x"] + r["w"] + pad), min(h, r["y"] + r["h"] + pad)
        y1 = min(y1, y0 + 1600)
        cur_crop = b[y0:y1, x0:x1]

        def base_crop(offset):
            out = np.full_like(cur_crop, 255)
            s0, s1 = max(0, y0 - offset), min(base.height, y1 - offset)
            if s1 > s0:
                out[s0 + offset - y0: s1 + offset - y0] = a[s0:s1, x0:x1]
            return out

        options = [base_crop(0)] + ([base_crop(delta)] if delta else [])
        best = min(options, key=lambda o: int(np.abs(o.astype(np.int16) - cur_crop).sum()))
        crops = [Image.fromarray(best), Image.fromarray(cur_crop), ov.crop((x0, y0, x1, y1))]
        cw, ch = x1 - x0, y1 - y0
        label_h = 22
        sheet = Image.new("RGB", (cw * 3 + 20, ch + label_h), "white")
        d = ImageDraw.Draw(sheet)
        for i, (img, label) in enumerate(zip(crops, ("BASELINE", "CURRENT", "DIFF"))):
            sheet.paste(img, (i * (cw + 10), label_h))
            d.text((i * (cw + 10) + 4, 4), f"{label}  #{n}  y={r['y']}", fill=(0, 0, 0))
        crop_path = out_dir / f"{stem}.region{n:02d}.png"
        sheet.save(crop_path, optimize=True)
        result["regions"].append({**r, "crop": str(crop_path)})
    for r in regions[cfg.get("max_regions", 12):]:
        result["regions"].append(r)
    return result


# --------------------------------------------------------------------------- report
def write_report(run_dir: Path, report: dict) -> None:
    (run_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))

    def rel(p):
        return html.escape(os.path.relpath(p, run_dir)) if p else ""

    rows = []
    order = {"error": 0, "changed": 1, "new": 2, "pass": 3}
    for it in sorted(report["items"], key=lambda i: (order.get(i["status"], 9), i["page"], i["width"])):
        head = (f"<h2 class='{it['status']}'>{html.escape(it['page'])} @ {it['width']}px · {it['browser']} · "
                f"<b>{it['status'].upper()}</b></h2><p><a href='{html.escape(it.get('url', ''))}'>{html.escape(it.get('url', ''))}</a>")
        if it["status"] == "error":
            rows.append(head + f"<br>{html.escape(it.get('error', ''))}</p>")
            continue
        d = it.get("diff") or {}
        if d:
            head += (f" · {d['diff_ratio'] * 100:.3f}% pixels · height {d['size_baseline'][1]}→{d['size_current'][1]}px"
                     f" · {len(d['regions'])} region(s)")
        head += "</p>"
        if it["status"] == "changed":
            crops = "".join(f"<figure><img src='{rel(r['crop'])}' loading='lazy'><figcaption>#{n} at x={r['x']} y={r['y']}, "
                            f"{r['w']}×{r['h']}px</figcaption></figure>"
                            for n, r in enumerate(d["regions"], 1) if r.get("crop"))
            imgs = (f"<div class='trio'><a href='{rel(it.get('baseline'))}'>baseline</a> · <a href='{rel(it['current'])}'>current</a>"
                    f" · <a href='{rel(d.get('diff_image'))}'>full diff</a></div>{crops}")
            rows.append(head + imgs)
        else:
            rows.append(head)
    s = report["summary"]
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visual check {html.escape(report['client'])}</title><style>
body{{font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:16px;color:#1a1a1a;background:#fafafa}}
h1{{font-size:22px}} h2{{font-size:16px;margin:28px 0 4px;padding:6px 10px;border-radius:6px;background:#eee}}
h2.changed{{background:#fff1d6}} h2.error{{background:#ffd9d9}} h2.new{{background:#dfefff}} h2.pass{{background:#e3f6e3}}
figure{{margin:10px 0}} img{{max-width:100%;border:1px solid #ddd;background:#fff}} figcaption{{font-size:13px;color:#555}}
.sum span{{display:inline-block;margin-right:14px}}</style></head><body>
<h1>Visual check · {html.escape(report['client'])}</h1>
<p>Run {html.escape(report['run_id'])} · baseline from {html.escape(report.get('baseline_captured_at') or 'n/a')}</p>
<p class="sum"><span>✅ pass {s['pass']}</span><span>⚠️ changed {s['changed']}</span><span>🆕 new {s['new']}</span><span>❌ error {s['error']}</span></p>
{''.join(rows)}</body></html>"""
    (run_dir / "report.html").write_text(doc)


# --------------------------------------------------------------------------- commands
def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def sitemap_urls(site: str, limit: int, errors: list | None = None) -> list[str]:
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    for cand in ("sitemap_index.xml", "wp-sitemap.xml", "sitemap.xml"):
        try:
            root = ET.fromstring(fetch(urljoin(site.rstrip("/") + "/", cand)))
            break
        except Exception as exc:
            if errors is not None:
                errors.append(f"{cand}: {exc}")
            continue
    else:
        return []
    if root.tag.endswith("sitemapindex"):
        maps = [e.text.strip() for e in root.iter(f"{ns}loc")]
        # pages first, then posts and others; skip taxonomy/author maps
        maps.sort(key=lambda u: (0 if "page" in u else 1 if "post" in u else 2))
        maps = [m for m in maps if not re.search(r"(category|tag|author|taxonomies|users|product_cat)", m)]
        urls = []
        for m in maps:
            try:
                urls += [e.text.strip() for e in ET.fromstring(fetch(m)).iter(f"{ns}loc")]
            except Exception:
                continue
            if len(urls) >= limit * 3:
                break
    else:
        urls = [e.text.strip() for e in root.iter(f"{ns}loc")]
    seen, out = set(), []
    for u in urls:
        if u not in seen and not re.search(r"\.(jpg|jpeg|png|webp|gif|pdf)$", u, re.I):
            seen.add(u)
            out.append(u)
    return out[:limit]


def cmd_init(args):
    cdir = client_dir(args, args.client)
    cfg_path = cdir / "config.yaml"
    if cfg_path.exists() and not args.force:
        sys.exit(f"{cfg_path} already exists (use --force to overwrite).")
    site = args.site.rstrip("/")
    sm_errors: list[str] = []
    urls = sitemap_urls(site, args.limit, sm_errors) if not args.no_sitemap else []
    host = urlparse(site).netloc
    paths = ["/"] + [urlparse(u).path or "/" for u in urls if urlparse(u).netloc == host]
    pages, names = [], set()
    for p in paths:
        n = slugify(p)
        if n in names:
            continue
        names.add(n)
        pages.append({"name": n, "path": p})
    pages = pages[: args.limit]
    cfg = {
        "name": args.client,
        "base_url": site,
        "widths": DEFAULTS["widths"],
        "browsers": DEFAULTS["browsers"],
        "threshold": DEFAULTS["threshold"],
        "max_diff_ratio": DEFAULTS["max_diff_ratio"],
        "hide": [],
        "mask": [],
        "pages": pages,
    }
    cdir.mkdir(parents=True, exist_ok=True)
    header = ("# visual-regression-check config. Built-in defaults (cookie banners, chat widgets,\n"
              "# admin bar hidden; video + iframe masked) apply on top of the lists below.\n"
              "# Per page you can add: hide, mask, css, url (full URL instead of path).\n")
    cfg_path.write_text(header + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    gi = root_dir(args) / ".gitignore"
    if not gi.exists():
        gi.write_text("*/runs/\n_compare/\n")
    out = {"config": str(cfg_path), "pages": len(pages), "from_sitemap": len(urls)}
    if not urls and sm_errors:
        out["sitemap_errors"] = sm_errors
        out["hint"] = "No sitemap read; only the home page was added. Add pages to config.yaml by hand."
    print(json.dumps(out, indent=2))


def _capture_set(cfg, pages, out_dir: Path, capt: Capturer) -> list[dict]:
    items = []
    for browser in cfg["browsers"]:
        for page in pages:
            url = page_url(cfg, page)
            for width in page.get("widths", cfg["widths"]):
                out = out_dir / browser / shot_name(page["name"], width)
                res = capt.capture(url, width, browser, out, page)
                print(f"  {'ok ' if res['ok'] else 'ERR'} {browser:8} {width:>5}px  {page['name']}"
                      + ("" if res["ok"] else f"  {res['error']}"), file=sys.stderr)
                items.append({"page": page["name"], "url": url, "width": width, "browser": browser,
                              "path": str(out), **res})
    return items


def cmd_baseline(args):
    cfg = load_config(args, args.client)
    pages = select_pages(cfg, args.pages)
    bdir = client_dir(args, args.client) / "baseline"
    capt = Capturer(cfg)
    try:
        items = _capture_set(cfg, pages, bdir, capt)
    finally:
        capt.close()
    bdir.mkdir(parents=True, exist_ok=True)
    meta_path = bdir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"shots": {}}
    now = dt.datetime.now().isoformat(timespec="seconds")
    for it in items:
        if it["ok"]:
            meta["shots"][f"{it['browser']}/{shot_name(it['page'], it['width'])}"] = {"captured_at": now, "url": it["url"]}
    meta["captured_at"] = now
    meta_path.write_text(json.dumps(meta, indent=2))
    errors = [i for i in items if not i["ok"]]
    print(json.dumps({"baseline_dir": str(bdir), "captured": len(items) - len(errors),
                      "errors": [{k: e[k] for k in ("page", "width", "browser", "error")} for e in errors]}, indent=2))
    return 2 if errors else 0


def _diff_items(cfg, items, base_root: Path | None, run_dir: Path, base_lookup=None) -> list[dict]:
    out = []
    for it in items:
        rec = {k: it.get(k) for k in ("page", "url", "width", "browser")}
        rec["current"] = it["path"]
        if not it["ok"]:
            rec.update(status="error", error=it["error"])
            out.append(rec)
            continue
        base = base_lookup(it) if base_lookup else base_root / it["browser"] / shot_name(it["page"], it["width"])
        rec["baseline"] = str(base)
        if not base or not Path(base).exists():
            rec["status"] = "new"
            out.append(rec)
            continue
        stem = f"{it['browser']}-{it['page']}@{it['width']}"
        d = diff_images(Path(base), Path(it["path"]), run_dir / "diff", stem, cfg)
        rec["diff"] = d
        rec["status"] = "changed" if d["changed"] else "pass"
        out.append(rec)
    return out


def _summary(items):
    s = {k: 0 for k in ("pass", "changed", "new", "error")}
    for i in items:
        s[i["status"]] += 1
    return s


def _finish(run_dir: Path, report: dict) -> int:
    write_report(run_dir, report)
    s = report["summary"]
    changed = [
        {"page": i["page"], "width": i["width"], "browser": i["browser"],
         "diff_pct": round(i["diff"]["diff_ratio"] * 100, 3), "height_delta": i["diff"]["height_delta"],
         "regions": len(i["diff"]["regions"]),
         "crops": [r["crop"] for r in i["diff"]["regions"] if r.get("crop")][:6]}
        for i in report["items"] if i["status"] == "changed"
    ]
    print(json.dumps({"run_id": report["run_id"], "summary": s, "report_html": str(run_dir / "report.html"),
                      "report_json": str(run_dir / "report.json"), "changed": changed,
                      "errors": [{"page": i["page"], "width": i["width"], "error": i["error"]}
                                 for i in report["items"] if i["status"] == "error"]}, indent=2))
    return 2 if s["error"] else 1 if s["changed"] else 0


def cmd_check(args):
    cfg = load_config(args, args.client)
    pages = select_pages(cfg, args.pages)
    cdir = client_dir(args, args.client)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{args.label}" if args.label else "")
    run_dir = cdir / "runs" / run_id
    capt = Capturer(cfg)
    try:
        items = _capture_set(cfg, pages, run_dir / "current", capt)
    finally:
        capt.close()
    results = _diff_items(cfg, items, cdir / "baseline", run_dir)
    meta_path = cdir / "baseline" / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    report = {"client": args.client, "run_id": run_id, "created_at": dt.datetime.now().isoformat(timespec="seconds"),
              "baseline_captured_at": meta.get("captured_at"), "config": {k: cfg[k] for k in ("threshold", "max_diff_ratio", "widths", "browsers")},
              "summary": _summary(results), "items": results}
    return _finish(run_dir, report)


def cmd_approve(args):
    cdir = client_dir(args, args.client)
    runs = sorted((cdir / "runs").glob("*")) if (cdir / "runs").exists() else []
    if not runs:
        sys.exit("No runs to approve.")
    run_dir = cdir / "runs" / args.run if args.run and args.run != "latest" else runs[-1]
    report = json.loads((run_dir / "report.json").read_text())
    wanted = {p.strip() for p in args.pages.split(",")} if args.pages else None
    bdir = cdir / "baseline"
    meta_path = bdir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"shots": {}}
    approved = []
    for it in report["items"]:
        if it["status"] not in ("changed", "new") and not args.all:
            continue
        if it["status"] == "error" or (wanted and it["page"] not in wanted):
            continue
        dest = bdir / it["browser"] / shot_name(it["page"], it["width"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(it["current"], dest)
        meta["shots"][f"{it['browser']}/{dest.name}"] = {"captured_at": report["created_at"], "url": it["url"],
                                                         "approved_from_run": report["run_id"],
                                                         "approved_at": dt.datetime.now().isoformat(timespec="seconds")}
        approved.append(f"{it['browser']}/{dest.name}")
    meta_path.write_text(json.dumps(meta, indent=2))
    print(json.dumps({"run_id": report["run_id"], "approved": approved}, indent=2))


def cmd_compare(args):
    cfg = {**DEFAULTS}
    if args.client:
        cfg = load_config(args, args.client)
    if args.widths:
        cfg["widths"] = [int(w) for w in args.widths.split(",")]
    name = args.name or slugify(urlparse(args.a).path)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{name}"
    run_dir = root_dir(args) / "_compare" / run_id
    capt = Capturer(cfg)
    items_a, items_b = [], []
    try:
        for browser in cfg["browsers"]:
            for width in cfg["widths"]:
                for url, side, bucket in ((args.a, "a", items_a), (args.b, "b", items_b)):
                    out = run_dir / side / browser / shot_name(name, width)
                    res = capt.capture(url, width, browser, out)
                    print(f"  {'ok ' if res['ok'] else 'ERR'} {side} {browser:8} {width:>5}px  {url}", file=sys.stderr)
                    bucket.append({"page": name, "url": url, "width": width, "browser": browser, "path": str(out), **res})
    finally:
        capt.close()
    lookup = {(i["browser"], i["width"]): i for i in items_a}

    def base_for(it):
        a = lookup[(it["browser"], it["width"])]
        return a["path"] if a["ok"] else None

    results = _diff_items(cfg, items_b, None, run_dir, base_lookup=base_for)
    report = {"client": f"compare: {name}", "run_id": run_id, "created_at": dt.datetime.now().isoformat(timespec="seconds"),
              "baseline_captured_at": f"A = {args.a}", "a": args.a, "b": args.b,
              "summary": _summary(results), "items": results}
    return _finish(run_dir, report)


def cmd_status(args):
    cdir = client_dir(args, args.client)
    cfg = load_config(args, args.client)
    meta_path = cdir / "baseline" / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    expected = [f"{b}/{shot_name(p['name'], w)}" for b in cfg["browsers"] for p in cfg["pages"] for w in p.get("widths", cfg["widths"])]
    have = meta.get("shots", {})
    missing = [e for e in expected if e not in have]
    oldest = min((v["captured_at"] for v in have.values()), default=None)
    age_days = None
    if oldest:
        age_days = (dt.datetime.now() - dt.datetime.fromisoformat(oldest)).days
    runs = sorted((cdir / "runs").glob("*")) if (cdir / "runs").exists() else []
    latest = None
    if runs and (runs[-1] / "report.json").exists():
        r = json.loads((runs[-1] / "report.json").read_text())
        latest = {"run_id": r["run_id"], "summary": r["summary"]}
    print(json.dumps({"client": args.client, "pages": len(cfg["pages"]), "expected_shots": len(expected),
                      "baseline_shots": len(have), "missing_baseline": missing[:20],
                      "oldest_baseline": oldest, "oldest_baseline_age_days": age_days, "latest_run": latest}, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="storage root (default ./visual-tests or $VRC_ROOT)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init");      p.add_argument("client"); p.add_argument("--site", required=True)
    p.add_argument("--limit", type=int, default=15); p.add_argument("--no-sitemap", action="store_true"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("baseline");  p.add_argument("client"); p.add_argument("--pages")
    p = sub.add_parser("check");     p.add_argument("client"); p.add_argument("--pages"); p.add_argument("--label")
    p = sub.add_parser("approve");   p.add_argument("client"); p.add_argument("--run", default="latest"); p.add_argument("--pages")
    p.add_argument("--all", action="store_true", help="also copy unchanged shots")
    p = sub.add_parser("compare");   p.add_argument("--a", required=True); p.add_argument("--b", required=True)
    p.add_argument("--name"); p.add_argument("--widths"); p.add_argument("--client", help="reuse hide/mask settings of a client")
    p = sub.add_parser("status");    p.add_argument("client")

    args = ap.parse_args(argv)
    fn = {"init": cmd_init, "baseline": cmd_baseline, "check": cmd_check, "approve": cmd_approve,
          "compare": cmd_compare, "status": cmd_status}[args.cmd]
    sys.exit(fn(args) or 0)


if __name__ == "__main__":
    main()
