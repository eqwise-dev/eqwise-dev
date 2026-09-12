# EQwise-skills, broncode

Hier staat de broncode van de EQwise-skills die in Claude draaien. De map in Claude zelf is de
draaiende versie, deze map is de versie die bijgehouden en teruggelezen kan worden.

## vera

De persoonlijke secretaresse van Martin. Bestanden:

- `vera/SKILL.md`, de skill zelf
- `vera/references/sessiedossier.md`, het model voor het sessiedossier, het startblok en het
  wegschrijven van een besluit. Vera leest dit pas op het moment dat ze het nodig heeft, zodat de
  skill zelf kort blijft.

### Bijwerken in Claude

1. Maak een zip van de map `vera`, met `SKILL.md` in de wortel van de zip en de map `references`
   ernaast.
2. Ga in claude.ai naar Instellingen, Capabilities, Skills, en vervang de bestaande skill `vera`
   door deze zip.
3. Start een nieuw gesprek en zeg "Vera, waar was ik gebleven" om te controleren of werkproces D
   werkt.

### Wat werkproces D nodig heeft

- De Drive-map `EQwise/Secretariaat/Sessies`. Bestaat die niet, dan maakt Vera hem aan bij het
  eerste sessiedossier.
- Het bestaande tabblad Taken in de sheet "EQwise Secretariaat". Er is geen nieuw tabblad en geen
  wijziging in de Apps Script-verzendbrug nodig: besluiten zijn taken met `Besluit:` voor de tekst.
- Filter in de sheet op de kolom Taak met `Besluit:` om het besluitenregister te zien.

### Versienummers

Skills krijgen vanaf nu een versienummer, en dat hoort onder `metadata` in de frontmatter:

```yaml
metadata:
  version: "1.2.0"
```

Een losse `version`-sleutel op het hoogste niveau wordt door de validatie geweigerd; toegestaan zijn
alleen `name`, `description`, `license`, `allowed-tools`, `metadata` en `compatibility`. `vera` staat
op 1.2.0 en is voorlopig de enige met een nummer. Derde cijfer bij een verduidelijking in de tekst,
tweede bij nieuw gedrag, eerste bij een andere werkwijze.

### Agentboom

Vera houdt het overzicht op https://claude.ai/code/artifact/ba4925e2-2518-4439-9d6f-b50837188d98
bij: agents en skills met hun versienummer, wie wat aanstuurt, en de status. Publiceren gaat altijd
naar diezelfde URL. Gemeten gegevens van de geheugenwacht en wat Vera zelf toevoegt staan er met een
eigen bronregel, zodat de herkomst per blok zichtbaar blijft.
