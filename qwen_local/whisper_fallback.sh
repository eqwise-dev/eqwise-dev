#!/usr/bin/env bash
# Route die op een Mac wél werkt voor Nederlandse audio: mlx-whisper transcribeert,
# een lokaal tekstmodel vat samen. Draai dit als de audiotest in setup.sh faalt.
# Gebruik:  bash qwen_local/whisper_fallback.sh opname.m4a

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HERE/.venv"
INPUT="${1:-$HERE/sample_nl.wav}"

[ -f "$INPUT" ] || { echo "Geen audiobestand: $INPUT" >&2; exit 1; }

[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --quiet --upgrade mlx-whisper

printf '\n\033[1m==> Transcriberen (Nederlands)\033[0m\n'
python - "$INPUT" <<'PY'
import sys, time
import mlx_whisper

path = sys.argv[1]
start = time.time()
result = mlx_whisper.transcribe(
    path,
    path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
    language="nl",
)
print(result["text"].strip())
print(f"\n[{time.time() - start:.1f}s]")
PY

echo
echo "Beoordeel de transcriptie hierboven op namen, bedragen en datums."
echo "Klopt die, dan is dit je lokale pijplijn en heb je Qwen-Omni niet nodig."
