#!/usr/bin/env bash
#
# Hulpscript bij de verzendbrug van het EQwise-secretariaat.
#
# Bouwt het JSON-bericht met jq, zodat aanhalingstekens, accenten en regeleinden in een
# omschrijving niet stukgaan op handmatig geknutselde curl-regels.
#
#   secretariaat.sh ping
#   secretariaat.sh rij Meldingen Titel="Contactformulier komt niet aan" Ernst=hoog Status=nieuw
#   secretariaat.sh voortgang M-0012 "Oorzaak gevonden, verzendadres aangepast." in behandeling
#   secretariaat.sh status Meldingen M-0012 opgelost
#
# Met --dryrun als eerste argument wordt niets verstuurd en toont het script alleen het bericht,
# met de sleutel weggelaten. Gebruik dat om een lange omschrijving na te kijken voor je hem wegschrijft.
#
# De sleutel komt uit SECRETARIAAT_SLEUTEL en staat nooit in een bestand of in de chat.

set -euo pipefail

DRYRUN=0
if [[ "${1:-}" == "--dryrun" ]]; then
  DRYRUN=1
  shift
fi

ACTIE="${1:-}"
[[ -n "$ACTIE" ]] || { echo "gebruik: secretariaat.sh [--dryrun] ping|rij|voortgang|status ..." >&2; exit 2; }
shift

command -v jq >/dev/null || { echo "jq is nodig maar niet gevonden" >&2; exit 3; }

: "${SECRETARIAAT_URL:?SECRETARIAAT_URL ontbreekt}"
if [[ $DRYRUN -eq 0 ]]; then
  : "${SECRETARIAAT_SLEUTEL:?SECRETARIAAT_SLEUTEL ontbreekt}"
fi

# velden_naar_json zet argumenten van de vorm Kolom=waarde om in één JSON-object.
velden_naar_json() {
  local paar sleutel waarde
  local uit='{}'
  for paar in "$@"; do
    [[ "$paar" == *=* ]] || { echo "veld zonder =: $paar" >&2; exit 2; }
    sleutel="${paar%%=*}"
    waarde="${paar#*=}"
    uit=$(jq -n --argjson basis "$uit" --arg k "$sleutel" --arg v "$waarde" '$basis + {($k): $v}')
  done
  printf '%s' "$uit"
}

case "$ACTIE" in
  ping)
    BERICHT=$(jq -n '{actie: "ping"}')
    ;;
  rij)
    TABBLAD="${1:?tabblad ontbreekt}"; shift
    [[ $# -gt 0 ]] || { echo "geef minstens één veld mee als Kolom=waarde" >&2; exit 2; }
    RIJ=$(velden_naar_json "$@")
    BERICHT=$(jq -n --arg t "$TABBLAD" --argjson r "$RIJ" '{actie: "rijen", tabblad: $t, rijen: [$r]}')
    ;;
  voortgang)
    MELDING="${1:?meldingnummer ontbreekt, bijvoorbeeld M-0012}"; shift
    UPDATE="${1:?updatetekst ontbreekt}"; shift
    STATUS="${*:-}"
    [[ -n "$STATUS" ]] || { echo "status na de update ontbreekt" >&2; exit 2; }
    RIJ=$(jq -n --arg m "$MELDING" --arg u "$UPDATE" --arg s "$STATUS" \
      '{Melding: $m, Update: $u, "Status na update": $s, "Zichtbaar voor klant": "ja", Bron: "vera"}')
    BERICHT=$(jq -n --argjson r "$RIJ" '{actie: "rijen", tabblad: "Voortgang", rijen: [$r]}')
    ;;
  status)
    TABBLAD="${1:?tabblad ontbreekt}"; shift
    ID="${1:?ID ontbreekt}"; shift
    STATUS="${*:-}"
    [[ -n "$STATUS" ]] || { echo "nieuwe status ontbreekt" >&2; exit 2; }
    BERICHT=$(jq -n --arg t "$TABBLAD" --arg i "$ID" --arg s "$STATUS" \
      '{actie: "status", tabblad: $t, id: $i, status: $s}')
    ;;
  *)
    echo "onbekende actie: $ACTIE" >&2
    exit 2
    ;;
esac

if [[ $DRYRUN -eq 1 ]]; then
  printf '%s\n' "$BERICHT"
  exit 0
fi

MET_SLEUTEL=$(jq -n --argjson b "$BERICHT" --arg k "$SECRETARIAAT_SLEUTEL" '{sleutel: $k} + $b')

ANTWOORD=$(printf '%s' "$MET_SLEUTEL" | curl -sL -X POST "$SECRETARIAAT_URL" \
  -H 'Content-Type: application/json' --data-binary @-)

if [[ -z "$ANTWOORD" ]]; then
  echo "geen antwoord van de verzendbrug, de implementatie is waarschijnlijk verlopen" >&2
  exit 4
fi

printf '%s\n' "$ANTWOORD"

if printf '%s' "$ANTWOORD" | grep -qi 'geweigerd'; then
  echo "de brug weigerde het bericht, controleer SECRETARIAAT_SLEUTEL" >&2
  exit 5
fi
