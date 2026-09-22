# Wachter tegen een te brede werkmap. Werkt in zsh en bash.
#
# Claude Code maakt de map waarin je start automatisch leesbaar. Start je in je
# thuismap, dan is dat je hele thuismap — zonder één vraag. Deze functie weigert
# dat en noemt het alternatief.
#
# Installeren: in ~/.zshrc (of ~/.bashrc)
#     source /pad/naar/security/claude-veilig-starten.sh
#
# Dit is geen beveiligingsgrens: met `command claude` loop je eromheen. Het punt
# is dat je dat dan bewust doet. De echte grenzen staan in ~/.claude/settings.json.

claude() {
  _cc_doel=$(pwd -P)
  _cc_home=$(cd "$HOME" 2>/dev/null && pwd -P) || _cc_home="$HOME"

  for _cc_map in \
    "$_cc_home" \
    "$_cc_home/Documents" \
    "$_cc_home/Desktop" \
    "$_cc_home/Downloads" \
    "$_cc_home/Library" \
    "$_cc_home/Library/Mobile Documents" \
    "$_cc_home/Pictures" \
    "/" "/Volumes" "/Users"
  do
    if [ "$_cc_doel" = "$_cc_map" ]; then
      printf '\342\234\213 Niet gestart: %s is te breed als werkmap.\n' "$_cc_doel" >&2
      printf '   Alles in deze map zou leesbaar zijn zonder een enkele vraag.\n' >&2
      printf '   Start vanuit een projectmap, of forceer met: command claude\n' >&2
      unset _cc_doel _cc_home _cc_map
      return 1
    fi
  done

  # De wortel van een gekoppeld volume: externe schijf, NAS, Time Machine.
  case "$_cc_doel" in
    /Volumes/*/*) : ;;
    /Volumes/*)
      printf '\342\234\213 Niet gestart: %s is de wortel van een gekoppeld volume.\n' "$_cc_doel" >&2
      printf '   Start in een submap, of forceer met: command claude\n' >&2
      unset _cc_doel _cc_home _cc_map
      return 1 ;;
  esac

  [ -f "$_cc_doel/.env" ] && printf '\342\232\240 Er staat een .env in deze map.\n' >&2

  unset _cc_doel _cc_home _cc_map
  command claude "$@"
}
