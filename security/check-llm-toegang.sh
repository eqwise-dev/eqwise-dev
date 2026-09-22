#!/usr/bin/env bash
# Nulmeting: waar kan een AI-agent op deze Mac op dit moment bij?
# Read-only — dit script wijzigt niets.
#
#   bash security/check-llm-toegang.sh

set -uo pipefail

ok()    { printf '  \033[32m[ok]\033[0m    %s\n' "$1"; }
warn()  { printf '  \033[33m[let op]\033[0m %s\n' "$1"; }
bad()   { printf '  \033[31m[open]\033[0m  %s\n' "$1"; }
info()  { printf '  [info]  %s\n' "$1"; }
kop()   { printf '\n\033[1m%s\033[0m\n' "$1"; }

SETTINGS="${HOME}/.claude/settings.json"

# JSON-waarde uitlezen zonder jq-afhankelijkheid.
# Geeft een scalar terug, de lengte van een lijst, of de sleutels van een object.
jget() { # jget <bestand> <sleutel.pad>
  python3 - "$1" "$2" <<'PY' 2>/dev/null
import json, sys
try:
    cur = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(1)
for part in sys.argv[2].split("."):
    if not isinstance(cur, dict) or part not in cur:
        sys.exit(1)
    cur = cur[part]
if isinstance(cur, list):
    print(len(cur))
elif isinstance(cur, dict):
    print(", ".join(sorted(cur)))
else:
    print(cur)
PY
}

printf '\033[1mLLM-toegang op deze Mac — %s\033[0m\n' "$(date '+%Y-%m-%d %H:%M')"

# ── Laag 1: macOS ────────────────────────────────────────────────────────────
kop "Laag 1 — macOS"

if [[ "$(uname -s)" != "Darwin" ]]; then
  warn "Dit is geen macOS; de macOS-controles worden overgeslagen."
else
  if fdesetup status 2>/dev/null | grep -q "FileVault is On"; then
    ok "FileVault staat aan."
  else
    bad "FileVault staat uit — zet aan bij Privacy en beveiliging."
  fi

  # Kan dit proces de TCC-database lezen? Zo ja, dan heeft de bovenliggende app
  # volledige schijftoegang, en daarmee alles wat vanuit die app start.
  if [[ -r "${HOME}/Library/Application Support/com.apple.TCC/TCC.db" ]]; then
    bad "Deze terminal heeft VOLLEDIGE SCHIJFTOEGANG. Alles wat je hier start ook."
    info "Systeeminstellingen > Privacy en beveiliging > Volledige schijftoegang."
  else
    ok "Deze terminal heeft geen volledige schijftoegang."
  fi

  if [[ "$(id -u)" -eq 0 ]]; then
    bad "Je draait als root. Doe agent-werk nooit als root."
  fi
fi

# ── Laag 2: permissieregels ─────────────────────────────────────────────────
kop "Laag 2 — Permissieregels (~/.claude/settings.json)"

if [[ ! -f "$SETTINGS" ]]; then
  bad "Geen ~/.claude/settings.json — er gelden geen persoonlijke deny-regels."
  info "Kopieer security/claude-settings-user.json hiernaartoe."
else
  if ! python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$SETTINGS" 2>/dev/null; then
    bad "~/.claude/settings.json is geen geldige JSON — Claude Code slaat het over."
  else
    n_deny=$(jget "$SETTINGS" permissions.deny || echo 0)
    n_ask=$(jget  "$SETTINGS" permissions.ask || echo 0)
    [[ "${n_deny:-0}" -gt 0 ]] && ok "${n_deny} deny-regels actief." || bad "Geen deny-regels."
    [[ "${n_ask:-0}"  -gt 0 ]] && ok "${n_ask} ask-regels actief."   || warn "Geen ask-regels."

    for pat in '.ssh' '.env' 'Keychains'; do
      if grep -q -- "$pat" "$SETTINGS"; then
        ok "Regel gevonden voor '${pat}'."
      else
        warn "Geen regel voor '${pat}'."
      fi
    done

    blok=$(jget "$SETTINGS" permissions.blockReadsOutsideWorkingDirectories || echo None)
    [[ "$blok" == "True" ]] \
      && ok "blockReadsOutsideWorkingDirectories staat aan." \
      || bad "blockReadsOutsideWorkingDirectories staat uit — lezen buiten de projectmap mag."

    byp=$(jget "$SETTINGS" permissions.disableBypassPermissionsMode || echo None)
    [[ "$byp" == "disable" ]] \
      && ok "bypassPermissions-modus is uitgeschakeld." \
      || warn "bypassPermissions-modus is nog mogelijk."

    # Deny-regels met één leidende slash: die verwijzen niet naar / maar naar ~/.claude.
    if grep -Eq '"(Read|Edit)\(/[^/]' "$SETTINGS"; then
      bad "Regel met één leidende slash gevonden — die verankert aan ~/.claude, niet aan /."
      info "Gebruik // voor absolute paden, of ~/ voor je thuismap."
    fi
  fi
fi

# ── Laag 3: sandbox ─────────────────────────────────────────────────────────
kop "Laag 3 — Sandbox"

if [[ -f "$SETTINGS" ]] && [[ "$(jget "$SETTINGS" sandbox.enabled || echo None)" == "True" ]]; then
  ok "Sandbox staat aan."
  n_dom=$(jget "$SETTINGS" sandbox.network.allowedDomains || echo 0)
  if [[ "${n_dom:-0}" -eq 0 ]]; then
    info "Geen vooraf toegestane domeinen — je krijgt een vraag per nieuw domein."
  elif [[ "${n_dom}" -gt 20 ]]; then
    warn "${n_dom} toegestane domeinen. Elk breed domein is een mogelijke uitgang."
  else
    ok "${n_dom} toegestane domeinen."
  fi
  n_cred=$(jget "$SETTINGS" sandbox.credentials.files || echo 0)
  [[ "${n_cred:-0}" -gt 0 ]] \
    && ok "${n_cred} credential-bestanden afgeschermd binnen de sandbox." \
    || warn "Geen sandbox.credentials — er is geen ingebouwde standaardlijst."
else
  bad "Sandbox staat uit — shell-commando's kunnen overal bij waar jij bij kunt."
  info "Zet aan met /sandbox in een sessie, of sandbox.enabled in je instellingen."
fi

# ── Laag 4: secrets binnen bereik ───────────────────────────────────────────
kop "Laag 4 — Secrets"

envs=$(find "$HOME" -maxdepth 4 -name '.env' -type f \
        -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null | head -20)
if [[ -z "$envs" ]]; then
  ok "Geen .env-bestanden gevonden binnen 4 niveaus onder je thuismap."
else
  n=$(printf '%s\n' "$envs" | wc -l | tr -d ' ')
  warn "${n} .env-bestand(en) binnen bereik:"
  printf '%s\n' "$envs" | sed 's|^|          |'
fi

shopt -s nullglob
keys=("$HOME"/.ssh/id_*)
shopt -u nullglob
if [[ ${#keys[@]} -eq 0 ]]; then
  info "Geen SSH-sleutels in ~/.ssh."
else
  for k in "${keys[@]}"; do
    [[ "$k" == *.pub ]] && continue
    if head -3 "$k" 2>/dev/null | grep -q "ENCRYPTED\|bcrypt"; then
      ok "$(basename "$k") heeft een passphrase."
    else
      bad "$(basename "$k") lijkt géén passphrase te hebben."
    fi
  done
fi

# ── Laag 5: MCP-verbindingen ────────────────────────────────────────────────
kop "Laag 5 — MCP-verbindingen"

GLOBAL_CFG="${HOME}/.claude.json"
if [[ -f "$GLOBAL_CFG" ]]; then
  servers=$(jget "$GLOBAL_CFG" mcpServers || echo "-")
  [[ -z "$servers" ]] && servers="-"
  if [[ "$servers" == "-" ]]; then
    ok "Geen MCP-servers op gebruikersniveau."
  else
    warn "MCP-servers op gebruikersniveau: ${servers}"
    info "Elke server is permanent bereik. Haal weg wat je niet gebruikt."
  fi
fi

if [[ -f "$SETTINGS" ]]; then
  auto=$(jget "$SETTINGS" enableAllProjectMcpServers || echo None)
  [[ "$auto" == "True" ]] \
    && bad "enableAllProjectMcpServers staat aan — elke .mcp.json uit elk project wordt goedgekeurd." \
    || ok "Project-MCP-servers worden niet automatisch goedgekeurd."
fi

if [[ -f ".mcp.json" ]]; then
  warn "Deze projectmap bevat een .mcp.json — controleer welke servers daarin staan."
fi

printf '\nKlaar. Uitleg per punt: security/llm-toegang-mac.md\n'
