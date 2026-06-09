#!/usr/bin/env python3
import json
import os

import anthropic
from dotenv import load_dotenv

from ideogram import IdeogramClient

load_dotenv()

SYSTEM_PROMPT = """You are a professional logo design assistant. Your job is to help users create logos using Ideogram AI.

When a user describes a logo they want, you should:
1. Craft a detailed, professional image generation prompt optimized for logo design
2. Call the generate_logo tool with your refined prompt
3. Present the resulting image URLs to the user clearly
4. Ask if they want variations, adjustments, or to upscale any of the generated logos

Guidelines for crafting logo prompts:
- Be specific about style (minimal, modern, vintage, geometric, typographic, etc.)
- Mention colors explicitly when the user has preferences
- Include the company/brand name if provided
- Specify if it should be flat design, gradient, or have depth
- Add "clean white background, vector style" for professional logos
- Avoid photorealistic elements — logos should be crisp and scalable

When presenting results, show each image URL on its own line and ask for feedback."""

TOOLS = [
    {
        "name": "generate_logo",
        "description": "Generate logo images using Ideogram AI. Call this after crafting a refined prompt from the user's description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed, professional prompt for logo generation.",
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
        "description": "Upscale a generated logo to a higher resolution. Use this when the user wants a high-resolution version of a specific logo.",
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


def process_tool_call(name: str, tool_input: dict, ideogram: IdeogramClient) -> str:
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
                return "No images were generated. Please try again with a different prompt."
            lines = [f"Generated {len(images)} logo(s):"]
            for i, img in enumerate(images, 1):
                url = img.get("url", "")
                lines.append(f"Logo {i}: {url}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error generating logo: {e}"

    if name == "upscale_logo":
        try:
            result = ideogram.upscale(image_url=tool_input["image_url"])
            images = result.get("data", [])
            if not images:
                return "Upscaling failed. Please try again."
            url = images[0].get("url", "")
            return f"Upscaled logo: {url}"
        except Exception as e:
            return f"Error upscaling logo: {e}"

    return f"Unknown tool: {name}"


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

    print("=== Logo Design Agent ===")
    print("Describe the logo you want and I'll generate it for you.")
    print("Type 'quit' or 'exit' to stop.\n")

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

        # Agentic loop
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
                print(f"[Calling tool: {tool_use.name}]")
                result = process_tool_call(tool_use.name, tool_use.input, ideogram)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result,
                    }
                )

            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_agent()
