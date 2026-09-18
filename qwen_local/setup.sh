#!/usr/bin/env bash
# Zet Qwen3-Omni lokaal op een Apple Silicon Mac op en test of audio werkt.
# Gebruik:  bash qwen_local/setup.sh [pad/naar/opname.wav]
# Zonder argument maakt het script zelf een Nederlands audiofragment met macOS `say`.

set -euo pipefail

MODEL="pherber3/Qwen3-Omni-30B-A3B-Instruct-4bit-mlx"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HERE/.venv"
SAMPLE="${1:-}"

say_step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
fail()     { printf '\n\033[31mFOUT: %s\033[0m\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- hardware
say_step "Hardware controleren"

[ "$(uname -s)" = "Darwin" ] || fail "Dit script is voor macOS."
[ "$(uname -m)" = "arm64" ]  || fail "Apple Silicon vereist (MLX draait niet op Intel)."

CHIP="$(sysctl -n machdep.cpu.brand_string)"
RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
echo "Chip:      $CHIP"
echo "Geheugen:  ${RAM_GB} GB unified memory"

if [ "$RAM_GB" -lt 24 ]; then
  fail "Te weinig geheugen. De 4-bit versie is ~18 GB aan gewichten; je hebt
      minimaal 24 GB nodig en 32 GB+ om comfortabel te draaien.
      Op ${RAM_GB} GB gaat dit swappen of omvallen. Gebruik dan de hosted API."
fi
[ "$RAM_GB" -ge 32 ] || echo "LET OP: ${RAM_GB} GB is krap. Sluit andere zware apps."

FREE_GB=$(( $(df -k "$HOME" | awk 'NR==2 {print $4}') / 1048576 ))
echo "Vrije schijf: ${FREE_GB} GB (download is ~18 GB)"
[ "$FREE_GB" -ge 25 ] || fail "Te weinig vrije schijfruimte; maak ~25 GB vrij."

# ---------------------------------------------------------------- omgeving
say_step "Python-omgeving klaarzetten"

command -v python3 >/dev/null || fail "python3 niet gevonden. Installeer via: xcode-select --install"

if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
  echo "Virtualenv aangemaakt: $VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

python -m pip install --quiet --upgrade pip
echo "mlx-vlm installeren (dit duurt even)..."
python -m pip install --quiet --upgrade mlx mlx-vlm huggingface_hub
python -c "import mlx_vlm, mlx; print('mlx-vlm', mlx_vlm.__version__ if hasattr(mlx_vlm,'__version__') else 'ok')"

# ---------------------------------------------------------------- audio
say_step "Nederlands testfragment klaarzetten"

if [ -n "$SAMPLE" ]; then
  [ -f "$SAMPLE" ] || fail "Opgegeven audiobestand bestaat niet: $SAMPLE"
  WAV="$HERE/sample_input.wav"
  afconvert -f WAVE -d LEI16@16000 -c 1 "$SAMPLE" "$WAV" \
    || fail "Kon $SAMPLE niet omzetten naar 16 kHz mono wav."
  echo "Eigen opname omgezet: $WAV"
else
  AIFF="$HERE/sample_nl.aiff"
  WAV="$HERE/sample_nl.wav"
  TEXT="Goedemiddag. Dit is een test voor EQwise. We spreken af dat de nieuwe \
website voor de klant volgende week vrijdag live gaat, dat Martin de teksten \
aanlevert, en dat de kosten uitkomen op vierduizend tweehonderd euro."
  # Xander en Claire zijn de Nederlandse stemmen in macOS.
  VOICE=""
  for v in Xander Claire; do
    if say -v '?' 2>/dev/null | grep -q "^$v "; then VOICE="$v"; break; fi
  done
  [ -n "$VOICE" ] || fail "Geen Nederlandse systeemstem gevonden. Installeer er een via
      Systeeminstellingen > Toegankelijkheid > Gesproken materiaal > Systeemstem,
      of geef zelf een opname mee: bash qwen_local/setup.sh opname.m4a"
  say -v "$VOICE" -o "$AIFF" "$TEXT"
  afconvert -f WAVE -d LEI16@16000 -c 1 "$AIFF" "$WAV"
  echo "Testfragment gemaakt met stem '$VOICE': $WAV"
fi

# ---------------------------------------------------------------- test 1
say_step "Test 1 van 2 — tekst (model wordt nu gedownload, ~18 GB, eenmalig)"

TXT_START=$SECONDS
python -m mlx_vlm.generate \
  --model "$MODEL" \
  --max-tokens 200 \
  --prompt "Vat samen in het Nederlands, in maximaal drie zinnen: de website van de klant gaat volgende week vrijdag live, Martin levert de teksten aan, en het budget is 4200 euro. Noem daarna de actiepunten als lijst." \
  || fail "De teksttest faalde. Stuur de foutmelding hierboven door."
echo "Teksttest duurde $(( SECONDS - TXT_START )) seconden."

# ---------------------------------------------------------------- test 2
say_step "Test 2 van 2 — Nederlandse audio (dit is de test die ertoe doet)"

echo "Als deze stap faalt, is dat het verwachte resultaat: de MLX-conversie van"
echo "Qwen3-Omni ondersteunt naar verwachting alleen tekst. De foutmelding is de uitkomst."
echo

AUD_START=$SECONDS
set +e
python -m mlx_vlm.generate \
  --model "$MODEL" \
  --max-tokens 300 \
  --audio "$WAV" \
  --prompt "Luister naar deze Nederlandse opname. Geef eerst een letterlijke transcriptie, daarna een samenvatting en de concrete afspraken met bedragen en datums."
AUDIO_RC=$?
set -e

echo
say_step "Uitkomst"
echo "Chip:            $CHIP (${RAM_GB} GB)"
echo "Model:           $MODEL"
echo "Teksttest:       geslaagd"
if [ $AUDIO_RC -eq 0 ]; then
  echo "Audiotest:       GESLAAGD in $(( SECONDS - AUD_START ))s — lokaal Nederlands audiobegrip werkt."
  echo
  echo "Beoordeel hierboven zelf: klopt de transcriptie, staan het bedrag (4200)"
  echo "en de datum er correct in? Dat bepaalt of dit bruikbaar is voor klantgesprekken."
else
  echo "Audiotest:       GEFAALD (exitcode $AUDIO_RC) — audio werkt niet in deze MLX-build."
  echo
  echo "Dit was de verwachte uitkomst. Lokaal blijft er dan een tekstmodel over,"
  echo "en daarvoor heb je geen omni-model nodig. Voor Nederlandse audio op deze Mac"
  echo "is mlx-whisper (transcriptie) plus een tekstmodel de route die wél werkt."
fi
