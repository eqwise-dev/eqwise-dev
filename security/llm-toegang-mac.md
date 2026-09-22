# Je LLM niet overal bij laten — Mac

Doel van dit document: de reikwijdte van AI-agents (Claude Code, Claude Desktop,
MCP-verbindingen) op je Mac terugbrengen van "alles wat mijn gebruiker kan" naar
"precies wat de klus nodig heeft".

Dit is laag 1 van je beveiliging. Schijfversleuteling, wachtwoordbeheer en
back-ups komen daarna — zie *Wat hierna komt* onderaan.

---

## Het probleem in één alinea

Claude Code draait als jouw macOS-gebruiker. Zonder extra instellingen kan alles
wat de agent start dus bij alles wat jij kunt: `~/.ssh`, je browserprofielen,
klant-`.env`-bestanden, je Keychain-bestanden, elke gemonteerde schijf. Dat is
geen bug — het is de standaardpositie van elk programma dat je start. De vraag is
niet óf je dat inperkt, maar in welke lagen.

Er zijn drie lagen die los van elkaar werken, en je hebt ze alle drie nodig:

| Laag | Wat het tegenhoudt | Wie handhaaft |
|---|---|---|
| **Permissieregels** (`deny` / `ask`) | Claude's eigen tools: Read, Edit, Bash-commando's die Claude Code herkent | Claude Code |
| **Sandbox** (macOS Seatbelt) | Álle processen die een shell-commando start, ook scripts | Het besturingssysteem |
| **macOS-account & TCC** | Wat je hele terminal überhaupt mag zien | macOS |

Belangrijk om te begrijpen: **permissieregels zijn geen OS-grens.** Ze gelden
voor Claude's bestandstools en voor bestandscommando's die Claude Code herkent
(`cat`, `head`, `tail`, `sed`, `tee`, en redirects als `> bestand`). Een Python-
of Node-script dat zélf een bestand opent, valt er buiten. Daarvoor is de sandbox.

---

## Laag 1 — macOS: geef de agent niet je hele Mac

Dit kost een half uur en levert de meeste winst op, omdat het onder Claude Code
zit: geen instelling in een JSON-bestand kan het omzeilen.

### 1.1 Geef je terminal géén volledige schijftoegang

Systeeminstellingen → Privacy en beveiliging → Volledige schijftoegang.
Staat Terminal, iTerm, Warp, VS Code of Claude Desktop daar aan? Zet uit.

Zonder volledige schijftoegang vraagt macOS zelf toestemming per map bij
`~/Desktop`, `~/Documents` en `~/Downloads` — die prompt is je vangnet als een
agent daar iets zoekt wat er niets te zoeken heeft. Met volledige schijftoegang
verdwijnt dat vangnet voor alles wat vanuit die app start.

Draai je Claude Code in achtergrondsessies, dan vraagt de sessie-host apart
toestemming voor die mappen; laat dat zo.

### 1.2 Overweeg een apart macOS-gebruikersaccount voor agent-werk

De harde variant: een tweede account (bijvoorbeeld `martin-dev`) waarin je
klantprojecten en Claude Code draait. Je eigen mail, browserprofielen,
privébestanden en iCloud-documenten staan in het andere account en zijn voor de
agent simpelweg niet leesbaar — afgedwongen door bestandsrechten, niet door
configuratie.

Kost wat gedoe (twee keer inloggen, of `su` naar het account), maar is de enige
laag die ook overeind blijft als je een keer per ongeluk `--dangerously-skip-permissions`
typt of een verkeerde instelling deelt.

Wil je dat niet: sla deze stap over, maar doe 1.1 en 1.3 dan wél.

### 1.3 Zet FileVault aan

Systeeminstellingen → Privacy en beveiliging → FileVault. Bewaar de herstelsleutel
in je wachtwoordmanager, niet in iCloud-alleen. Dit beschermt niet tegen een
agent, wel tegen een gestolen MacBook — en dat hoort in hetzelfde gesprek thuis.

---

## Laag 2 — Permissieregels in Claude Code

### 2.1 Zet het gebruikersbestand neer

Kopieer [`claude-settings-user.json`](./claude-settings-user.json) naar
`~/.claude/settings.json`. Heb je daar al een bestand: voeg de `permissions`- en
`sandbox`-blokken samen, gooi je eigen instellingen niet weg. Lijsten uit
verschillende bestanden worden door Claude Code samengevoegd, dus je kunt
gerust regels toevoegen.

Controleer daarna in een sessie met `/permissions` dat de regels geladen zijn, en
met `/status` welke instellingenbestanden Claude Code gelezen heeft.

### 2.2 De drie syntaxvallen waar iedereen in trapt

**Val 1 — één slash is géén absoluut pad.**
`Read(/Users/martin/geheim)` slaat nergens op wat je denkt: één leidende slash
verankert aan de *bron van de instelling*. In `~/.claude/settings.json` wordt dat
`~/.claude/Users/martin/geheim`. Gebruik `//` voor een echt absoluut pad, of `~/`
voor je thuismap:

| Patroon | Betekent |
|---|---|
| `//Users/martin/geheim/**` | `/Users/martin/geheim/**` — absoluut |
| `~/.ssh/**` | je thuismap |
| `/src/**` in projectinstellingen | `<projectmap>/src/**` |
| `.env` of `**/.env` | elke `.env` op of onder de huidige map |

**Val 2 — deny wint altijd, van welk bestand dan ook.**
De volgorde is `deny` → `ask` → `allow`, en de eerste match bepaalt. Een
specifieke `allow` kan geen gat knippen in een brede `deny`. Dat is precies wat
je wilt: je kunt jezelf niet per ongeluk toestemming terug geven via een
projectbestand.

**Val 3 — een `deny` op een Bash-commando is geen slot.**
`Bash(rm *)` stopt `rm -rf build/`, maar niet `/bin/rm -rf build/` of
`bash -c 'rm -rf build/'`. Bash-regels matchen de commandotekst, meer niet.
Gebruik ze om gedrag te sturen, niet als beveiligingsgrens — die zit in laag 3.

### 2.3 Zet leestoegang buiten je projectmap dicht

De sterkste regel in het sjabloon is deze:

```json
"permissions": { "blockReadsOutsideWorkingDirectories": true }
```

Hiermee weigeren Claude's bestandstools élk pad buiten je werkmap en je
`additionalDirectories`, in elke permissiemodus. Geen lijst met uitzonderingen
meer bijhouden: alles buiten het project is dicht tenzij je de map expliciet
toevoegt met `/add-dir`.

### 2.4 Sluit de ontsnappingsluiken

```json
"permissions": { "disableBypassPermissionsMode": "disable" }
```

Dit zet `bypassPermissions` (en `--dangerously-skip-permissions`) uit vanuit je
eigen gebruikersbestand. Je sluit jezelf er vrijwillig mee buiten — dat is het
punt. Wil je ook de automatische modus uit, zet `permissions.disableAutoMode` op
`"disable"`.

---

## Laag 3 — De sandbox: de enige echte grens

Op macOS zit de sandbox ingebouwd (Seatbelt), er is niets te installeren. Zet aan
met `/sandbox` in een sessie, of via `sandbox.enabled: true` in je instellingen —
het sjabloon doet dat al.

Wat de sandbox doet en permissieregels níét:

* Hij geldt voor **elk proces dat een shell-commando start**, inclusief kinderen.
  Een Python-script dat zelf `~/.ssh/id_ed25519` openmaakt, wordt hier gestopt.
* Hij knijpt het **netwerk** af. Standaard staat er geen enkel domein open; bij
  een nieuw domein krijg je een vraag. Zonder netwerkisolatie heeft
  bestandsisolatie weinig zin — dan kan een gecompromitteerde agent nog altijd
  wegsturen wat hij leest.
* Hij beschermt de bestanden waaruit Claude Code zichzelf configureert
  (`.claude/`, `.mcp.json`, hooks, shell-startbestanden) tegen schrijven vanuit
  de sandbox. Anders kon een commando zichzelf rechten geven.

### 3.1 Netwerk: houd de lijst kort

```json
"sandbox": { "network": { "allowedDomains": ["registry.npmjs.org", "pypi.org"] } }
```

De lijst in het sjabloon is een startpunt voor jouw werk (npm, PyPI, GitHub,
WordPress.org). Let op: **elk breed domein is een mogelijke uitgang.** De proxy
beslist op basis van de hostnaam en kijkt standaard niet in het TLS-verkeer, dus
`github.com` toestaan betekent dat data via GitHub naar buiten kán. Houd de lijst
zo kort als je werk toelaat.

Wil je helemaal geen vragen meer maar harde weigering buiten de lijst, zet
`sandbox.network.strictAllowlist` op `true` — dat werkt alleen vanuit je
gebruikersbestand of beheerde instellingen, niet vanuit een projectbestand.

### 3.2 Credentials apart afschermen

```json
"sandbox": {
  "credentials": {
    "files": [{ "path": "~/.ssh", "mode": "deny" }],
    "envVars": [{ "name": "GITHUB_TOKEN", "mode": "deny" }]
  }
}
```

Bestanden worden onleesbaar binnen de sandbox; omgevingsvariabelen worden
gewist vóór elk sandboxcommando. Er is géén ingebouwde standaardlijst — alleen
wat jij opsomt, is beschermd. Wil je credentials uit *alle* subprocessen strippen,
ook buiten de sandbox, zet dan `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`.

### 3.3 De ontsnappingsklep

Als een commando niet sandboxed kan draaien, mag Claude het opnieuw proberen met
`dangerouslyDisableSandbox` — dat gaat dan wel door de gewone permissievraag. Het
sjabloon zet daar een `ask`-regel op, zodat je het altijd ziet. Wil je het luik
helemaal dicht: `"allowUnsandboxedCommands": false` (in `/sandbox` heet dat
*Strict sandbox mode*). Reken op wat wrijving bij tooling die netwerk nodig heeft.

---

## Laag 4 — Secrets buiten bereik houden

De beste bescherming is dat het geheim er niet ligt waar de agent werkt.

1. **Nooit een echte `.env` in een repo-map die je met een agent deelt.** In dit
   project staat nu een `.gitignore` die `.env` en `*.pem`/`*.key` tegenhoudt, en
   een `.claude/settings.json` die ze ook onleesbaar maakt voor de agent.
2. **Roteer wat al eens langs een agent is gekomen.** Een sleutel die in een
   sessie, een log of een transcript heeft gestaan, beschouw je als gelekt. Dat
   geldt voor je Ideogram- en Anthropic-keys in dit project net zo goed.
3. **Klantcredentials (SiteGround, FTP, WP-admin) in je wachtwoordmanager**, niet
   in een tekstbestand in een projectmap. Gebruik voor WordPress application
   passwords per site, zodat je er één kunt intrekken zonder de rest te raken.
4. **SSH-sleutels met een passphrase**, toegevoegd aan de agent. Dan is het
   bestand op zichzelf niet genoeg.

---

## Laag 5 — MCP-verbindingen: bij jou de grootste reikwijdte

Dit is het stuk dat in jouw situatie zwaarder weegt dan je lokale bestanden. Een
MCP-server voor een klantsite geeft de agent schrijfrechten op een productiesite —
een bereik dat geen enkele `deny`-regel op je Mac inperkt.

* **`enableAllProjectMcpServers` op `false`** (staat zo in het sjabloon). Anders
  keurt Claude Code elke server in een `.mcp.json` van een project automatisch
  goed — ook in een repo die je net van iemand anders hebt gekloond.
* **Scope je tokens per site.** Eén token per klantsite, met de rechten die de
  klus nodig heeft. Niet één sleutel die overal bij kan.
* **Werk op staging waar het kan.** Een agent die per ongeluk 40 pagina's
  herschrijft op staging is een middag werk; op productie is het een klantgesprek.
* **Blokkeer specifieke servers of tools** met `deniedMcpServers`, of met een
  `deny`-regel per tool: `mcp__<server>__<tool>`, bijvoorbeeld een delete-tool.
* **Ruim op wat je niet gebruikt.** Elke verbonden server is permanent bereik.
  Loop je lijst door en haal eruit wat je deze maand niet nodig had.

---

## Laag 6 — Wat rechten *niet* oplossen: prompt injection

Rechten bepalen wat de agent *mag*. Ze bepalen niet wat de agent *wil*. Een
webpagina die je laat ophalen, een issue-tekst, een reviewcommentaar of de inhoud
van een klantsite kan instructies bevatten die de agent probeert te sturen.

Wat helpt:

* De sandbox-netwerklijst kort houden — zonder uitgang gaat er niets weg.
* `blockReadsOutsideWorkingDirectories` — er is niets interessants te lezen.
* Wantrouwen bij onverwachte stappen. Als een agent ineens in `~/.ssh` wil kijken
  of naar een onbekend domein wil posten terwijl je om een CSS-fix vroeg: stoppen
  en kijken waar die instructie vandaan kwam.

Dit is de reden dat je alle drie de lagen wilt en niet alleen de makkelijke.

---

## Startpakket: de eerste 30 minuten

In deze volgorde, want elke stap staat los van de volgende:

1. Volledige schijftoegang van je terminal/editor afhalen. *(5 min, laag 1)*
2. `security/claude-settings-user.json` naar `~/.claude/settings.json`. *(5 min, laag 2)*
3. `/sandbox` aanzetten, een dag werken, domeinen goedkeuren die je echt nodig hebt. *(10 min + gewenning, laag 3)*
4. Je MCP-lijst doorlopen en weghalen wat je niet gebruikt. *(10 min, laag 5)*
5. `security/check-llm-toegang.sh` draaien en de uitkomst bewaren als nulmeting.

Daarna, als je meer wilt: apart macOS-account (1.2) en `strictAllowlist` (3.1).

---

## Controleren

```bash
bash security/check-llm-toegang.sh
```

Read-only script: het verandert niets, het rapporteert alleen wat er nu staat.
Draai het opnieuw na elke wijziging, en nog eens over een maand.

In een Claude Code-sessie:

* `/permissions` — welke regels gelden er, en uit welk bestand
* `/status` — welke instellingenbestanden geladen zijn
* `/sandbox` — staat de sandbox aan, en welke paden en domeinen staan open
* `claude doctor` — meldt ongeldige regels en verdachte domeinnotaties

---

## Wat hierna komt

Buiten de scope van dit document, maar hoort in hetzelfde rijtje thuis:

* Wachtwoordmanager + passkeys, 2FA op je hosting- en domeinaccounts
* Back-ups met een offline of onveranderlijke kopie
* Wat je klanten mag laten zien: toegangsbeheer, logging, incidentprocedure
  (relevant zodra een klant naar je verwerkersovereenkomst vraagt)

---

## Bronnen

* [Configure permissions](https://code.claude.com/docs/en/permissions)
* [Configure the sandboxed Bash tool](https://code.claude.com/docs/en/sandboxing)
* [Settings files and precedence](https://code.claude.com/docs/en/settings)
* [Settings reference](https://code.claude.com/docs/en/settings-reference)
