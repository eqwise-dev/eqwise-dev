# Welke mappen en documenten kan de agent zien?

Vervolg op [`llm-toegang-mac.md`](./llm-toegang-mac.md). Dat document beschrijft
de drie lagen; dit document maakt er één concreet mappenbeleid van: welke mappen
open staan, welke je dicht zet, en wat dat in de praktijk voor je werk betekent.

---

## Het model in vier regels

1. De map waarin je `claude` start is de **werkmap**. Alles daarin is leesbaar,
   zonder één vraag.
2. Daar komen de mappen bij die je expliciet toevoegt: `--add-dir` bij het
   starten, `/add-dir` tijdens een sessie, of `permissions.additionalDirectories`
   in je instellingen.
3. Alles daarbuiten geeft een vraag — of een weigering, als je
   `blockReadsOutsideWorkingDirectories` aanzet.
4. `deny`-regels gaan boven alles. Ook boven een map die je zelf hebt toegevoegd,
   ook boven een "ja, niet meer vragen" die je eerder gaf.

Regel 4 is je vangnet: je kunt jezelf niet per ongeluk toegang terug geven.

---

## Regel 1 — Start nooit in je thuismap

Dit is de fout die alle andere maatregelen ongedaan maakt:

```bash
cd ~ && claude        # ← je hele thuismap is nu werkmap
```

Documents, Desktop, Downloads, je iCloud-map, je administratie: allemaal leesbaar
zonder dat er ook maar iets gevraagd wordt. Geen enkele instelling repareert dat
achteraf, behalve de `deny`-regels uit regel 4.

Hetzelfde geldt voor `~/Documents` of `~/Desktop` als werkmap, en voor `/Volumes`.

### Een wachter in je shell

Zet dit in je `~/.zshrc` (of neem [`claude-veilig-starten.sh`](./claude-veilig-starten.sh)
over). Het weigert een start in een map die te breed is:

```sh
source ~/pad/naar/security/claude-veilig-starten.sh
```

Het is een shell-functie, geen beveiligingsgrens — je kunt er altijd omheen met
`command claude`. Het punt is dat je het dan bewust doet.

---

## Regel 2 — Eén boom voor werk, de rest daarbuiten

De simpelste manier om te bepalen wat een agent kan zien, is om alles wat hij mag
zien in één boom te zetten:

```
~/Werk/
├── klanten/
│   ├── ontslagspecialist/
│   └── omnihealth/
├── eqwise/
└── experimenten/
```

Alles wat níét in `~/Werk` staat — je administratie, je privé-documenten, je
iCloud-map, je Downloads — ligt er per constructie buiten. Niet omdat een regel
het tegenhoudt, maar omdat je er nooit een sessie start.

**Staan je klantprojecten nu in `~/Documents`?** Dan is verplaatsen naar `~/Werk`
de stap die dit document van je vraagt. Je kunt `~/Documents` niet dichtzetten en
er één projectmap uit uitzonderen: een `!`-uitzondering werkt niet tegen een regel
die met `~/` verankerd is, en een uitzondering kan een map die als geheel
geblokkeerd is sowieso niet heropenen. Het is dus alles of niets per map.

---

## Regel 3 — Zet de weigering hard aan

```json
"permissions": { "blockReadsOutsideWorkingDirectories": true }
```

Zonder deze instelling krijg je een *vraag* bij elk pad buiten je werkmap. Dat
werkt precies zo lang als je aandacht duurt: bij de twintigste vraag op een
drukke dag klik je op ja. Met de instelling aan is het antwoord nee, in elke
permissiemodus, en moet je bewust `/add-dir` typen om een map erbij te halen.

---

## Regel 4 — De mappen die je expliciet dichtzet

Ook mét regel 1 tot en met 3 wil je deze op slot, omdat ze je meest gevoelige
gegevens bevatten en omdat je ooit een keer ergens anders start dan je dacht:

| Map | Waarom |
|---|---|
| `~/Documents/**` | Contracten, administratie, klantgegevens. Let op: bij aanstaande iCloud-synchronisatie staat hier ook alles van je andere apparaten. |
| `~/Desktop/**` | Bureaublad is bij de meeste mensen een tussenopslag voor precies de bestanden die je niet wilt delen. |
| `~/Downloads/**` | Dubbel risico: hier staan gevoelige bijlagen én bestanden van onbekende herkomst. Een agent die daar leest, leest ook wat iemand anders erin heeft gezet. |
| `~/Library/Mobile Documents/**` | Je hele iCloud Drive, inclusief de synchronisatie van Bureaublad en Documenten. |
| `~/Pictures/**` | Fotobibliotheek, scans van paspoorten en facturen. |
| `~/Library/Mail/**`, `~/Library/Messages/**` | Je mail- en berichtenarchief. |
| `~/Library/Containers/**`, `~/Library/Group Containers/**` | Hier bewaren apps als Notities, WhatsApp en Signal hun gegevens. |
| `//Volumes/**` | Externe schijven, NAS-shares en Time Machine-back-ups. Een gemonteerde back-up bevat een kopie van alles wat je hierboven net hebt dichtgezet. |

Deze staan als blok in [`claude-settings-user.json`](./claude-settings-user.json).

### Variant: je werkt tóch in Documents

Zet dan niet heel `~/Documents` dicht, maar de submappen die ertoe doen:

```json
"deny": [
  "Read(~/Documents/Administratie/**)",
  "Read(~/Documents/Prive/**)",
  "Read(~/Documents/Contracten/**)"
]
```

Zwakker dan de map als geheel dichtzetten — je bent nu zelf de lijst aan het
bijhouden — maar beter dan niets. Verplaatsen naar `~/Werk` blijft de betere zet.

---

## Regel 5 — Zet `/cd` aan de ketting

`/cd` verplaatst een lopende sessie naar een andere map, inclusief de
instellingen, hooks en MCP-servers van díé map. Claude kan `/cd` niet zelf
aanroepen — het is jouw commando — maar het is wel de snelste manier om per
ongeluk je hele thuismap open te zetten.

```json
"permissions": {
  "allow": ["Cd(~/Werk/**)"]
}
```

Zodra je één `Cd`-allow-regel toevoegt, schakelt `/cd` over naar
allowlist-modus: alleen nog doelen die matchen, de rest wordt geweigerd. Met
`~/Werk/**` kun je binnen je werkboom bewegen en er niet meer uit.

Let op de matchregels, die anders zijn dan bij `Read`:

| Regel | Matcht | Matcht niet |
|---|---|---|
| `Cd(~/Werk/*)` | `~/Werk/klanten` | `~/Werk/klanten/omnihealth`, `~/Werk` |
| `Cd(~/Werk/**)` | `~/Werk` en alles eronder | alles buiten `~/Werk` |

`*` is hier precies één mapniveau, `**` gaat over niveaus heen. Wil je `/cd`
helemaal uitzetten: een kale `Cd` in `deny`.

Deze regel staat **niet** in het sjabloon, want hij gaat uit van een `~/Werk`-map
die jij nog moet maken. Voeg hem toe als regel 2 staat.

---

## Regel 6 — Dezelfde grens, maar dan op OS-niveau

Alles hierboven geldt voor Claude's eigen bestandstools. Een script dat een
commando start, opent bestanden zelf — daar komt de sandbox om de hoek kijken.
In de **projectinstellingen** van een gevoelig project:

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "denyRead": ["~/"],
      "allowRead": ["."]
    }
  }
}
```

Dit sluit je hele thuismap af voor alles wat in de sandbox draait, en zet alleen
deze projectmap open. De smallere regel wint van de bredere, dus een `denyRead`
op een specifiek bestand blijft ook gelden binnen een brede `allowRead`.

Dit moet in `.claude/settings.json` van het project staan, niet in je
gebruikersbestand: `.` verwijst in een gebruikersbestand naar `~/.claude`, en dan
staat je projectmap alsnog dicht.

Schrijven is standaard al beperkt tot je werkmap, de tijdelijke map van de sessie
en je toegevoegde mappen. Meer nodig? `sandbox.filesystem.allowWrite` met een
specifiek pad, niet een hele boom.

---

## Regel 7 — Claude Desktop telt mee

De desktop-app en de VS Code-extensie lezen dezelfde instellingenbestanden als de
terminal, dus je `deny`-regels gelden daar ook. Wat níét meekomt is regel 1: in
de app kies je een map in een dialoogvenster, en dat is even makkelijk je
thuismap als je projectmap. Kies daar bewust.

En laat macOS zijn werk doen: zonder volledige schijftoegang vraagt het systeem
zélf toestemming bij `~/Desktop`, `~/Documents` en `~/Downloads`. Dat is precies
de vraag die je wilt zien.

---

## Controleren wat er nu open staat

```bash
bash security/check-llm-toegang.sh
```

Het script meldt per map uit de tabel hierboven of er een regel voor is, en
waarschuwt als je hem draait vanuit een map die te breed is als werkmap.

In een sessie:

* `/status` — welke werkmap en welke toegevoegde mappen gelden er
* `/permissions` — welke regels, en uit welk bestand ze komen
* `/sandbox` → tabblad **Config** — welke paden de sandbox open en dicht heeft

---

## Wat dit niet oplost

Een map die je bewust toevoegt, is open. Als je `/add-dir ~/Documents` typt omdat
een klus dat vraagt, staat je documentenmap open tot het eind van de sessie —
tenzij er een `deny`-regel op staat, en die is er na regel 4 wél. Dat is de reden
dat regel 4 en regel 3 allebei in de lijst staan: de een fenceert, de ander
weigert.
