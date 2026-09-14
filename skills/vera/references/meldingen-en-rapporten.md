# Meldingen, buglog en rapportopslag

Naslag bij werkproces D en E van de skill `vera`. Hier staat wat er eenmalig in de sheet moet worden
klaargezet, welke kopregels de tabbladen precies hebben, en hoe een melding er in de praktijk
uitziet. De werkwijze zelf staat in `SKILL.md`, niet hier.

## 1. Eenmalig klaarzetten in de sheet

In de Google Sheet "EQwise Secretariaat" komen drie tabbladen bij. Rij 1 is de kopregel, precies zoals
hieronder, want de verzendbrug zoekt de kolommen op naam. Plak elke regel in cel A1, dan verdeelt
Sheets hem over de kolommen.

**Meldingen**

```text
ID	Gemeld	Titel	Klant of project	Melder	Soort	Ernst	Status	Waar	Omschrijving	Eigenaar	Uiterlijk	Zichtbaar voor klant	Bron	Rapport	Oplossing	Notitie
```

**Voortgang**

```text
ID	Tijd	Melding	Update	Status na update	Zichtbaar voor klant	Bron
```

**Rapporten**

```text
ID	Datum	Titel	Soort	Klant of project	Uitgevoerd door	Samenvatting	Bevindingen	Bestand	Meldingen	Status	Bron
```

In de Apps Script van de verzendbrug moeten de nieuwe tabbladen een ID-voorvoegsel krijgen, in
dezelfde tabel waar `Taken` nu `T-` krijgt: `Meldingen` wordt `M-`, `Voortgang` wordt `V-` en
`Rapporten` wordt `R-`. Zolang dat niet is gedaan schrijft de brug de rij wel weg, maar blijft de
kolom ID leeg en klopt de verwijzing vanuit Voortgang niet.

Wie de brug niet kan aanpassen, kan de tabbladen alsnog gebruiken: zet in de kolom ID dan een
handmatige formule of vul het nummer met de hand, en houd de nummering oplopend per tabblad.

## 2. Wat je bij een melding uitvraagt

Zes vragen, in één bericht, nooit druppelsgewijs:

1. Om welke site of welk project gaat het
2. Wat gaat er mis, in de woorden van de melder
3. Op welke pagina of bij welke handeling, met de URL als die er is
4. Sinds wanneer, en gebeurt het elke keer of soms
5. Op welk apparaat en in welke browser is het gezien
6. Wat is het gevolg, blijft er werk liggen of gaat er iets verloren

Bij een storing sla je deze zes over. Registreren met wat je hebt gaat voor volledigheid.

## 3. Kolommen, wat er precies in hoort

| Kolom | Wat erin hoort |
| --- | --- |
| Gemeld | Datum en tijd waarop de melding binnenkwam, niet wanneer jij hem wegschrijft |
| Titel | Één regel in gewone taal, dit is wat de klant op de statuspagina ziet |
| Melder | Naam van wie het meldde, of `Martin`, of de naam van het rapport |
| Soort | `bug`, `storing`, `fout`, `bevinding` of `wens` |
| Ernst | `kritiek`, `hoog`, `normaal` of `laag`, volgens de tabel in de skill |
| Status | `nieuw`, `bevestigd`, `in behandeling`, `wacht op klant`, `opgelost`, `vervallen` |
| Waar | URL, paginanaam of het onderdeel, bijvoorbeeld `/contact` of `hoofdmenu, mobiel` |
| Omschrijving | Feitelijk, twee tot vier regels, zonder oordeel over de oorzaak |
| Eigenaar | Wie het oplost: `Martin`, een specialist, of `klant` |
| Uiterlijk | Alleen invullen als Martin een datum heeft toegezegd, anders leeg |
| Zichtbaar voor klant | `ja`, tenzij het een openstaand beveiligingslek of een interne aantekening is |
| Bron | Waar de melding vandaan komt, bijvoorbeeld `telefoon klant 2026-09-14` of `rapport R-0031` |
| Rapport | Het rapportnummer of de link, als de melding uit een rapport komt |
| Oplossing | Bij afsluiten: wat er mis was, wat er is gedaan, sinds wanneer het werkt |

De kolom Omschrijving is geen plakplek voor logregels. Komt een melding uit een debug-log, dan neem
je maximaal drie regels over en verwijder je serverpaden, sleutels en mailadressen. De volledige log
hoort in de klantmap in Drive, met de link in Notitie.

## 4. Een melding van begin tot eind

```text
Meldingen
M-0012  2026-09-14 10:20  Contactformulier komt niet aan  OmniHealth  Sanne Bakker
        bug  hoog  nieuw  /contact
        "Verzenden geeft een groene melding, maar er komt niets binnen. Sinds 12 september,
         elke keer. Gezien op iPhone Safari en op Windows Chrome. Aanvragen blijven liggen."
        Eigenaar Martin  Zichtbaar voor klant ja  Bron telefoon klant 2026-09-14

Voortgang
V-0031  2026-09-14 10:25  M-0012  Melding bevestigd bij Sanne, Martin kijkt vandaag.      bevestigd
V-0032  2026-09-14 15:40  M-0012  Oorzaak gevonden, verzendadres stond nog op oude
                                  domein. Aangepast, testmail ontvangen.                  in behandeling
V-0033  2026-09-15 09:10  M-0012  Klant heeft bevestigd dat de aanvragen binnenkomen.     opgelost
```

Op de statuspagina van de klant staat op 14 september alleen dit:

```text
Loopt nu
M-0012  Contactformulier komt niet aan
        Status: in behandeling, sinds 14 september
        Wat er speelt: aanvragen via /contact bereiken jullie mailbox niet.
        Wat wij doen: het verzendadres is aangepast, we controleren of alles nu doorkomt.
        Volgende stap: terugkoppeling morgen.
```

Wat er bewust niet op staat: welke instelling er precies fout stond, wie het heeft veroorzaakt, en
hoe lang het al zo stond. Dat hoort in de kolom Oplossing en in het gesprek met Martin.

## 5. Rapporten

| Kolom | Wat erin hoort |
| --- | --- |
| Soort | `SEO`, `AEO`, `security`, `pagespeed`, `toegankelijkheid`, `design`, `techniek`, `overig` |
| Uitgevoerd door | De specialist of de skill, bijvoorbeeld `security-agent` of `website AI-agent` |
| Samenvatting | Maximaal vijf regels, de kern zoals Martin die zou navertellen |
| Bevindingen | Aantal, en tussen haakjes hoeveel daarvan meldingen zijn geworden |
| Bestand | Link naar het rapport in `Rapporten/<jaar>/` in de klantmap |
| Meldingen | De meldingnummers die eruit zijn ontstaan, gescheiden door een komma |
| Status | `ontvangen`, `verwerkt`, `gedeeld met klant` |

Een rapport staat pas op `verwerkt` als elke bevinding die actie vraagt een meldingnummer heeft. Op
`gedeeld met klant` staat het alleen nadat Martin het heeft vrijgegeven.

## 6. Terugkerende bronnen van meldingen

| Bron | Hoe je eraan komt |
| --- | --- |
| Debug-log van een site | De website AI-agent van die site leest de log uit, jij neemt de kern over |
| Security-audit | De security-agent, bevindingen altijd met Zichtbaar voor klant op `nee` tot ze verholpen zijn |
| Pagespeed en Core Web Vitals | De website AI-agent, meestal `wens` of `bevinding`, zelden `bug` |
| Toegankelijkheidsscan | De website AI-agent, per bevinding wegen of het echt actie vraagt |
| SEO en AEO | De SEO-skills, een gedaalde pagina is een melding, een idee is een taak |
| Klant zelf | Via Martin, of via de reactie op een gedeelde voorbeeldlink |

Wat in alle gevallen geldt: de scan is de bron, niet de waarheid. Je controleert een bevinding, of je
laat hem controleren, voordat je hem als bug bij de klant neerlegt.

## 7. Wat de klant wel en niet ziet

| Wel | Niet |
| --- | --- |
| Meldingnummer en titel in gewone taal | De ernstindeling en de interne prioriteit |
| De status en sinds wanneer die geldt | Wie van ons eraan werkt of hoe druk het is |
| Wat er speelt en wat wij doen | Oorzaakanalyse, foutmeldingen, serverpaden |
| De volgende stap, met datum als die is toegezegd | Een datum die Martin niet heeft gegeven |
| Wat recent is opgelost en wat zij kunnen controleren | Openstaande beveiligingsbevindingen |
