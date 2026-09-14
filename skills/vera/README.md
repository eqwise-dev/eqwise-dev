# Vera, versiebeheerde kopie

Dit is de bronversie van de skill `vera`, het secretariaat van EQwise. De versie die Claude
daadwerkelijk gebruikt is de gesynchroniseerde skill in het Claude-account van Martin. Deze map
bestaat zodat wijzigingen aan Vera reviewbaar zijn en terug te draaien.

| Bestand | Wat het is |
| --- | --- |
| `SKILL.md` | De skill zelf, inclusief werkproces D (meldingen en buglog) en E (rapporten) |
| `references/meldingen-en-rapporten.md` | Naslag: kopregels van de tabbladen, kolomuitleg, voorbeelden, wat de klant wel en niet ziet |
| `scripts/secretariaat.sh` | Hulpscript dat het JSON voor de verzendbrug opbouwt met jq |

## Na een wijziging hier

1. Neem de nieuwe `SKILL.md` over in de gesynchroniseerde skill, anders verandert er niets aan
   wat Claude doet.
2. Maak in de Google Sheet "EQwise Secretariaat" de tabbladen **Meldingen**, **Voortgang** en
   **Rapporten** aan, met de kopregels uit `references/meldingen-en-rapporten.md` in rij 1.
3. Vul in de Apps Script van de verzendbrug de ID-voorvoegsels aan: `Meldingen` wordt `M-`,
   `Voortgang` wordt `V-`, `Rapporten` wordt `R-`.

Stap 2 en 3 zijn eenmalig. Zonder stap 2 weigert de brug de rijen en valt Vera terug op
tab-gescheiden regels in de chat. Zonder stap 3 komen de rijen er wel in, maar blijft de kolom ID
leeg en is een melding niet te koppelen aan zijn voortgangsregels.

## Het hulpscript

```bash
export SECRETARIAAT_URL="https://script.google.com/macros/s/..."
export SECRETARIAAT_SLEUTEL="..."   # nooit in een bestand, alleen in de omgeving

skills/vera/scripts/secretariaat.sh ping
skills/vera/scripts/secretariaat.sh rij Meldingen Titel="Formulier komt niet aan" Ernst=hoog
skills/vera/scripts/secretariaat.sh --dryrun voortgang M-0012 "Oorzaak gevonden." in behandeling
```

`--dryrun` toont alleen het bericht dat verstuurd zou worden, zonder de sleutel, en raakt de sheet
niet aan. Het script heeft `jq` en `curl` nodig.
