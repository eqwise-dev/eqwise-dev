#!/usr/bin/env python3
import base64
import os

import anthropic
import requests
from dotenv import load_dotenv

from ideogram import IdeogramClient

load_dotenv()

QUALITY_LEVELS = {
    "1": {
        "label": "Quick",
        "description": "Fast, accepts first result (no review)",
        "instructions": (
            "QUALITY MODE: Quick\n"
            "Accept the first generated result regardless of quality. "
            "Do NOT evaluate or refine. Present the logos to the user immediately."
        ),
    },
    "2": {
        "label": "Standard",
        "description": "Light review, one refinement if needed",
        "instructions": (
            "QUALITY MODE: Standard\n"
            "After generating, visually review the logos. If there are major issues "
            "(garbled/missing text, completely wrong style, obvious artifacts), "
            "refine the prompt ONCE and regenerate. Otherwise accept what was generated."
        ),
    },
    "3": {
        "label": "Premium",
        "description": "Careful review, up to 3 attempts total",
        "instructions": (
            "QUALITY MODE: Premium\n"
            "After generating, carefully evaluate each logo. Refine and regenerate "
            "(up to 2 more times, 3 attempts total) if any of these issues exist: "
            "wrong or unclear text rendering, off-brand style, poor color choices, "
            "messy composition, or unclear concept. "
            "Accept only when logos are professional and match the brief well."
        ),
    },
    "4": {
        "label": "Perfect",
        "description": "Strict review, iterate until excellent (up to 5 attempts)",
        "instructions": (
            "QUALITY MODE: Perfect\n"
            "Be strict. After each generation, critically evaluate every logo. "
            "Refine and regenerate (up to 4 more times, 5 attempts total) until the logos are "
            "truly excellent: clean professional design, correctly rendered text, "
            "colors that fit the brand, clear concept at any size, vector-quality aesthetics. "
            "Only accept when you are genuinely satisfied with the result."
        ),
    },
}

BASE_SYSTEM_PROMPT = """You are a professional logo design assistant. Your job is to help users create logos using Ideogram AI.

WORKFLOW:
1. When a user describes a logo, craft a detailed professional prompt and call generate_logo
2. After generation you will see the actual logo images — visually evaluate them
3. Based on your quality mode (see below), decide to accept or refine and retry
4. When satisfied, present the final logo URLs clearly and ask for feedback

PROMPT CRAFTING:
- Specify style explicitly: minimal, modern, vintage, geometric, typographic, abstract, etc.
- State colors when the user has preferences; otherwise choose brand-appropriate ones
- Include the company/brand name and note it must render as clean legible text
- Add design approach: flat, gradient, outlined, badge-style, wordmark, etc.
- End every prompt with: "clean white background, vector style, professional logo design"
- Never use photorealistic elements — logos must be crisp and scalable

VISUAL QUALITY EVALUATION (after seeing the generated images, check for):
- Professional, clean composition with clear visual hierarchy
- Text rendered correctly — no garbled, missing, or distorted letters
- Colors match the brief and look harmonious
- Concept is recognizable and would work at small sizes (favicon, business card)
- Vector-style aesthetics — sharp edges, clean shapes, no photo noise or blur
- No obvious artifacts, smearing, or low-resolution areas

When refining a prompt after a failed attempt, explicitly address what was wrong.

{quality_instructions}"""


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
                num_images=tool_input.get("num_images", 2),
                seed=tool_input.get("seed"),
            )
            images = result.get("data", [])
            if not images:
                return [{"type": "text", "text": "No images were generated. Please try again."}]

            urls = "\n".join(f"Logo {i+1}: {img.get('url', '')}" for i, img in enumerate(images))
            content = [{"type": "text", "text": f"Generated {len(images)} logo(s):\n{urls}\n\nVisually evaluating now:"}]

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
            content = [{"type": "text", "text": f"Upscaled logo: {url}"}]
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
            return [{"type": "text", "text": f"Error upscaling logo: {e}"}]

    return [{"type": "text", "text": f"Unknown tool: {name}"}]


TOOLS = [
    {
        "name": "generate_logo",
        "description": (
            "Generate logo images using Ideogram AI. "
            "Call this with a refined professional prompt. "
            "The tool returns the generated images for you to visually evaluate. "
            "Based on your quality mode, decide whether to accept or call this tool again with an improved prompt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed professional prompt for logo generation.",
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "Elements to avoid in the generated image (optional).",
                },
                "num_images": {
                    "type": "integer",
                    "description": "Number of logo variations to generate (1-4). Default 2.",
                    "default": 2,
                },
                "seed": {
                    "type": "integer",
                    "description": "Random seed for reproducibility (optional).",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "upscale_logo",
        "description": "Upscale a generated logo to higher resolution. Use when the user wants a print-ready version.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "URL of the Ideogram-generated image to upscale.",
                },
            },
            "required": ["image_url"],
        },
    },
]


def select_quality_level() -> dict:
    print("\nSelect quality level:")
    for key, level in QUALITY_LEVELS.items():
        print(f"  {key}. {level['label']:<10} — {level['description']}")
    print()
    while True:
        choice = input("Quality [1-4, default 2]: ").strip() or "2"
        if choice in QUALITY_LEVELS:
            level = QUALITY_LEVELS[choice]
            print(f"Selected: {level['label']}\n")
            return level
        print("Please enter 1, 2, 3, or 4.")


def run_agent():
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    ideogram_key = os.getenv("IDEOGRAM_API_KEY")

    if not anthropic_key:
        raise SystemExit("ANTHROPIC_API_KEY not set. Add it to your .env file.")
    if not ideogram_key:
        raise SystemExit("IDEOGRAM_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=anthropic_key)
    ideogram = IdeogramClient(api_key=ideogram_key)

    print("=== Logo Design Agent ===")
    quality = select_quality_level()
    system_prompt = BASE_SYSTEM_PROMPT.format(quality_instructions=quality["instructions"])

    messages = []

    print("Describe the logo you want and I'll generate it for you.")
    print("Commands: /quality [1-4] to change quality level, quit/exit to stop.\n")

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

        if user_input.startswith("/quality"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1] in QUALITY_LEVELS:
                quality = QUALITY_LEVELS[parts[1]]
                system_prompt = BASE_SYSTEM_PROMPT.format(quality_instructions=quality["instructions"])
                print(f"Quality changed to: {quality['label']} — {quality['description']}\n")
            else:
                print("Usage: /quality [1|2|3|4]\n")
            continue

        messages.append({"role": "user", "content": user_input})

        # Agentic loop — runs until Claude stops calling tools
        while True:
            response = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=4096,
                thinking={"type": "adaptive"},
                system=system_prompt,
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
                print(f"[{tool_use.name}] Calling Ideogram API...")
                content_blocks = process_tool_call(tool_use.name, tool_use.input, ideogram)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": content_blocks,
                })

            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_agent()
