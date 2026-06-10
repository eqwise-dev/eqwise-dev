#!/usr/bin/env python3
import base64
import os

import anthropic
import requests
from dotenv import load_dotenv

from ideogram import IdeogramClient

load_dotenv()

SYSTEM_PROMPT = """You are a professional logo design assistant.

═══════════════════════════════════════════════════════════
MANDATORY RULE — memorise this, apply it every single time:
Whenever the user asks you to create, make, or generate a logo,
you MUST ask for quality level and style FIRST, before doing anything else.
Show both menus in one message, exactly as written below, then wait.
═══════════════════════════════════════════════════════════

STEP 1 — Ask this, verbatim, before every logo generation:

---
Before I start, two quick questions:

**Quality**
1. Quick       — Accept first result immediately, no review
2. Standard    — Light check; one refinement if there are major issues
3. Premium     — Careful review; up to 3 attempts until it looks professional
4. Perfect     — Strict review; up to 5 attempts, only accept when excellent

**Style**
A. Design / Flat   — Clean vector graphics, ideal for logos  ★ recommended
B. 3D Render       — Three-dimensional with depth and lighting
C. General         — Balanced, versatile
D. Realistic       — Photorealistic elements
E. Anime           — Japanese animation aesthetic

Reply with e.g. **2A**, **3, B**, or **Premium + Flat**
---

STEP 2 — Once the user replies, generate the logo with those settings.

─────────────────────────────────────────────────────────
QUALITY BEHAVIOUR (apply based on the user's choice)
─────────────────────────────────────────────────────────
1 Quick     Call generate_logo once. Present results immediately without any evaluation.
2 Standard  After generating, view the images. If there are MAJOR issues (garbled or
            missing text, completely wrong style, obvious artefacts), refine the prompt
            once and regenerate. Otherwise accept.
3 Premium   After generating, carefully evaluate each logo. Refine and regenerate
            up to 2 more times (3 total) when: text is unclear, style is off-brand,
            colours are wrong, or composition is messy. Accept when professional.
4 Perfect   Be strict. After each attempt, critically evaluate every detail. Refine
            and regenerate up to 4 more times (5 total). Only accept when the result
            is truly excellent — clean design, correct text, on-brand colours, works
            at any size.

─────────────────────────────────────────────────────────
STYLE → style_type mapping (pass to generate_logo tool)
─────────────────────────────────────────────────────────
A / Design / Flat   → DESIGN
B / 3D Render       → RENDER_3D
C / General         → GENERAL
D / Realistic       → REALISTIC
E / Anime           → ANIME
Default when unspecified: DESIGN

─────────────────────────────────────────────────────────
PROMPT CRAFTING RULES
─────────────────────────────────────────────────────────
- Describe the visual style explicitly (minimal, modern, geometric, vintage, etc.)
- State colours when given; otherwise choose brand-appropriate ones
- Include the brand name and note it must render as clean, legible text
- Specify layout: flat, outlined, badge, emblem, wordmark, icon+text, etc.
- End every prompt with: "clean white background, professional logo design"
- No photorealistic elements — logos must be crisp and scalable

─────────────────────────────────────────────────────────
VISUAL QUALITY CHECKLIST (use for levels 2–4 after seeing images)
─────────────────────────────────────────────────────────
✓ Professional, clean composition
✓ Text rendered correctly — no garbled, missing, or distorted letters
✓ Colours match the brief and look harmonious
✓ Concept is clear and recognisable at small sizes
✓ Sharp vector-style edges — no photo noise, blur, or artefacts

When refining after a failed attempt, explicitly state what was wrong and how you fixed it.

─────────────────────────────────────────────────────────
IMPORTANT OUTPUT RULES
─────────────────────────────────────────────────────────
- Never mention the name of any image generation service or API.
- Present final logo URLs clearly, one per line, labelled Logo 1, Logo 2, etc.
- After delivering results, ask if the user wants variations, adjustments, or a high-resolution version."""


def fetch_image_base64(url: str) -> tuple[str, str]:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    media_type = resp.headers.get("content-type", "image/png").split(";")[0].strip()
    return base64.standard_b64encode(resp.content).decode("utf-8"), media_type


def process_tool_call(name: str, tool_input: dict, ideogram: IdeogramClient) -> list:
    if name == "generate_logo":
        try:
            result = ideogram.generate(
                prompt=tool_input["prompt"],
                negative_prompt=tool_input.get("negative_prompt"),
                style_type=tool_input.get("style_type", "DESIGN"),
                num_images=tool_input.get("num_images", 2),
                seed=tool_input.get("seed"),
            )
            images = result.get("data", [])
            if not images:
                return [{"type": "text", "text": "No images were generated. Please try again."}]

            urls = "\n".join(f"Logo {i+1}: {img.get('url', '')}" for i, img in enumerate(images))
            content = [{"type": "text", "text": f"Generated {len(images)} logo(s):\n{urls}"}]

            for i, img in enumerate(images):
                url = img.get("url", "")
                if not url:
                    continue
                try:
                    b64_data, media_type = fetch_image_base64(url)
                    content.append({"type": "text", "text": f"Logo {i+1}:"})
                    content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64_data},
                    })
                except Exception as e:
                    content.append({"type": "text", "text": f"(Could not load Logo {i+1} for review: {e})"})

            return content

        except Exception as e:
            return [{"type": "text", "text": f"Error generating logo: {e}"}]

    if name == "upscale_logo":
        try:
            result = ideogram.upscale(image_url=tool_input["image_url"])
            images = result.get("data", [])
            if not images:
                return [{"type": "text", "text": "Upscaling failed. Please try again."}]
            url = images[0].get("url", "")
            content = [{"type": "text", "text": f"High-resolution version: {url}"}]
            if url:
                try:
                    b64_data, media_type = fetch_image_base64(url)
                    content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64_data},
                    })
                except Exception:
                    pass
            return content
        except Exception as e:
            return [{"type": "text", "text": f"Error upscaling: {e}"}]

    return [{"type": "text", "text": f"Unknown tool: {name}"}]


TOOLS = [
    {
        "name": "generate_logo",
        "description": (
            "Generate logo images. Call this after the user has chosen quality and style. "
            "The tool returns the generated images embedded for visual evaluation. "
            "Based on the chosen quality level, decide to accept or refine and call again."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed professional prompt for logo generation.",
                },
                "style_type": {
                    "type": "string",
                    "enum": ["DESIGN", "RENDER_3D", "GENERAL", "REALISTIC", "ANIME"],
                    "description": "Visual style. DESIGN for flat/vector logos (default).",
                    "default": "DESIGN",
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "Elements to exclude from the image (optional).",
                },
                "num_images": {
                    "type": "integer",
                    "description": "Number of variations to generate (1–4). Default 2.",
                    "default": 2,
                },
                "seed": {
                    "type": "integer",
                    "description": "Seed for reproducibility (optional).",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "upscale_logo",
        "description": "Upscale a logo to high resolution for print-ready output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "URL of the logo to upscale.",
                },
            },
            "required": ["image_url"],
        },
    },
]

TOOL_STATUS = {
    "generate_logo": "Generating logo...",
    "upscale_logo":  "Upscaling to high resolution...",
}


def run_agent():
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    ideogram_key = os.getenv("IDEOGRAM_API_KEY")

    if not anthropic_key:
        raise SystemExit("ANTHROPIC_API_KEY not set. Add it to your .env file.")
    if not ideogram_key:
        raise SystemExit("IDEOGRAM_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=anthropic_key)
    ideogram = IdeogramClient(api_key=ideogram_key)

    messages = []

    print("=== EQwise Logo Design Agent ===")
    print("Describe the logo you want. Type quit or exit to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        while True:
            response = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=4096,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            text_parts = [b.text for b in response.content if b.type == "text"]
            if text_parts:
                print(f"\nAgent: {''.join(text_parts)}\n")

            tool_uses = [b for b in response.content if b.type == "tool_use"]

            if not tool_uses or response.stop_reason == "end_turn":
                messages.append({"role": "assistant", "content": response.content})
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_use in tool_uses:
                status = TOOL_STATUS.get(tool_use.name, "Working...")
                print(f"[{status}]")
                content_blocks = process_tool_call(tool_use.name, tool_use.input, ideogram)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": content_blocks,
                })

            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_agent()
