# Qwen-Omni lokaal testen op de Mac mini

## Wat hier wel en niet kan

**Qwen3.8-Omni-Flash is niet te downloaden.** Dat model (18 sep 2026) heeft geen open
weights en draait alleen als hosted API via DashScope, Alibaba Cloud Model Studio en
QwenCloud. Lokaal draaien is geen configuratiekwestie maar onmogelijk.

Wat wél open is, is de voorganger **Qwen3-Omni-30B-A3B** — tekst, beeld, audio en video
in, tekst en spraak uit. Die is te downloaden van Hugging Face. De kanttekening: de
beschikbare 4-bit MLX-conversie voor Apple Silicon ondersteunt naar verwachting alleen
tekstinvoer, en audio vereist een omweg. Juist het audiostuk is dus het onzekerst.

Dit script test dat verschil hard uit in plaats van erover te speculeren.

## Draaien

```bash
bash qwen_local/setup.sh                    # maakt zelf een Nederlands testfragment
bash qwen_local/setup.sh ~/opname.m4a       # of gebruik een echte klantopname
```

Het script:

1. controleert chip, geheugen en schijfruimte, en stopt met uitleg als het niet past;
2. zet een virtualenv op met `mlx` en `mlx-vlm`;
3. maakt een Nederlands audiofragment met de macOS-stem Xander (of zet jouw opname om);
4. draait een **teksttest** — die hoort te slagen;
5. draait een **audiotest** — dit is de test die ertoe doet.

De eerste keer wordt ~18 GB aan gewichten gedownload.

## Eisen

| | |
|---|---|
| Chip | Apple Silicon (M1 of nieuwer) — MLX draait niet op Intel |
| Geheugen | minimaal 24 GB, comfortabel vanaf 32 GB |
| Schijf | ~25 GB vrij |

Een Mac mini M4 met 16 GB is te klein; het script weigert dan met uitleg.

## Als de audiotest faalt

Dat is de verwachte uitkomst. Er blijft dan een lokaal tekstmodel over, en daar heb je
geen omni-model voor nodig. De route die op een Mac wél werkt voor Nederlandse audio:

```bash
bash qwen_local/whisper_fallback.sh ~/opname.m4a
```

Dat transcribeert met `mlx-whisper` (large-v3-turbo, Nederlands). Beoordeel de
transcriptie op namen, bedragen en datums — dat bepaalt of het bruikbaar is voor
klantgesprekken.

## Waarom lokaal, en wanneer niet

Lokaal draaien is aantrekkelijk om één reden: klantopnames verlaten je machine niet. Dat
is voor opnames van Nederlandse klanten een echt argument, want de hosted Qwen-API draait
in Singapore- en China-regio's.

Daar staat tegenover dat je een generatie ouder model draait, in 4-bit, op hardware die
er niet voor gebouwd is. Als de kwaliteit tegenvalt is de eerlijke conclusie dat lokaal
omni hier nog niet klaar is — niet dat er iets misging.
