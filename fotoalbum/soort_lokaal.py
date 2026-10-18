#!/usr/bin/env python3
"""Soortherkenning met een lokaal beeldmodel (bijvoorbeeld Qwen-VL in Ollama of LM Studio).

De foto's verlaten de computer niet. Werkt met elke server die de OpenAI-chat-API spreekt
(LM Studio, llama.cpp, vLLM, Ollama vanaf /v1) en met de eigen API van Ollama.

Gebruik:
  python3 fotoalbum/soort_lokaal.py modellen                      # wat draait er lokaal?
  python3 fotoalbum/soort_lokaal.py herken foto1.jpg foto2.jpg [--regio Tanzania] [--model naam]

Zonder --model kiest het script zelf: eerst een model met "qwen" en "vl" in de naam, dan
een ander beeldmodel (llava, gemma3, minicpm-v, pixtral). Uitvoer: JSON per foto met
soort, wetenschappelijke_naam, zekerheid en kenmerken.
"""

import argparse
import base64
import io
import json
import os
import sys
import urllib.request

from PIL import Image, ImageOps

SERVERS = [s for s in (os.environ.get("LOKAAL_MODEL_URL"),) if s] + [
    "http://localhost:11434",  # Ollama
    "http://localhost:1234",   # LM Studio
    "http://localhost:8080",   # llama.cpp-server
    "http://localhost:8000",   # vLLM
]
VOORKEUR = [("qwen", "vl"), ("qwen3-vl",), ("qwen2.5vl",), ("llava",), ("gemma3",), ("minicpm-v",), ("pixtral",)]

VRAAG = """Je bent een ervaren veldornitholoog en safarigids. Determineer het dier op deze foto{regio}.
Antwoord ALLEEN met JSON, zonder uitleg eromheen:
{{"soort": "Nederlandse naam (of 'geen dier')", "wetenschappelijke_naam": "Latijnse naam of leeg",
 "zekerheid": "hoog|middel|laag", "kenmerken": "zichtbare kenmerken waarop je oordeel rust"}}
Wees streng: bij twijfel tussen soorten noem je het geslacht of de familie en zet je zekerheid op laag."""


def _json(url, data=None, timeout=10):
    verzoek = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(verzoek, timeout=timeout) as antwoord:
        return json.loads(antwoord.read().decode("utf-8"))


def vind_modellen():
    """[(server, api, modelnaam)] voor alle bereikbare lokale servers."""
    gevonden = []
    for server in SERVERS:
        try:
            for m in _json(server + "/api/tags", timeout=2).get("models", []):
                gevonden.append((server, "ollama", m["name"]))
            continue
        except (OSError, ValueError):
            pass
        try:
            for m in _json(server + "/v1/models", timeout=2).get("data", []):
                gevonden.append((server, "openai", m["id"]))
        except (OSError, ValueError):
            pass
    return gevonden


def kies_model(gevonden, naam=None):
    if naam:
        for g in gevonden:
            if g[2] == naam or g[2].startswith(naam):
                return g
        sys.exit(f"Model '{naam}' niet gevonden. Beschikbaar: {', '.join(g[2] for g in gevonden) or 'geen'}")
    for woorden in VOORKEUR:
        for g in gevonden:
            if all(w in g[2].lower() for w in woorden):
                return g
    sys.exit("Geen lokaal beeldmodel gevonden. Draait Ollama of LM Studio? Kies anders zelf met --model.")


def _beeld(pad, maat=1280):
    # Verkleind en rechtop: sneller, en lokale modellen schalen toch terug.
    img = ImageOps.exif_transpose(Image.open(pad)).convert("RGB")
    img.thumbnail((maat, maat))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def _lees_json(tekst):
    tekst = tekst.strip()
    if "</think>" in tekst:  # denkende modellen zetten hun redenering ervoor
        tekst = tekst.split("</think>")[-1]
    begin, eind = tekst.find("{"), tekst.rfind("}")
    if begin < 0 or eind < 0:
        return {"soort": "onbekend", "wetenschappelijke_naam": "", "zekerheid": "laag", "kenmerken": tekst[:200]}
    return json.loads(tekst[begin:eind + 1])


def herken(pad, model, regio=None):
    server, api, naam = model
    vraag = VRAAG.format(regio=f", gemaakt in {regio}" if regio else "")
    b64 = _beeld(pad)
    if api == "ollama":
        antwoord = _json(server + "/api/chat", {
            "model": naam, "stream": False, "options": {"temperature": 0},
            "messages": [{"role": "user", "content": vraag, "images": [b64]}]}, timeout=600)
        tekst = antwoord["message"]["content"]
    else:
        antwoord = _json(server + "/v1/chat/completions", {
            "model": naam, "temperature": 0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": vraag},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]}, timeout=600)
        tekst = antwoord["choices"][0]["message"]["content"]
    return {"bestand": str(pad), "model": naam, **_lees_json(tekst)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("actie", choices=["modellen", "herken"])
    parser.add_argument("fotos", nargs="*")
    parser.add_argument("--model")
    parser.add_argument("--regio")
    args = parser.parse_args()
    gevonden = vind_modellen()
    if args.actie == "modellen":
        for server, api, naam in gevonden:
            print(f"{naam:40s} {api:7s} {server}")
        if not gevonden:
            print("Geen lokale modelserver gevonden (Ollama 11434, LM Studio 1234, llama.cpp 8080, vLLM 8000).")
        else:
            print(f"\nAutomatische keuze: {kies_model(gevonden)[2]}")
        return
    model = kies_model(gevonden, args.model)
    print(json.dumps([herken(p, model, args.regio) for p in args.fotos], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
