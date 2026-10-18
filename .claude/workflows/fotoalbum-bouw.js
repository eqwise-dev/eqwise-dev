export const meta = {
  name: 'fotoalbum-bouw',
  description: 'Fotoalbum stap 2: verhaal en layout, teksten per hoofdstuk, ON1-verbetering, boek en web bouwen, dubbele kwaliteitscontrole',
  whenToUse: 'Na goedgekeurde curatie (fotoalbum-selectie of importeer_keuzebak.py). Args: {album: "<pad naar album.json>", curatie: "<pad naar curatie.json>", wensen?: "<vrije tekst>", stijlgids?: "<pad naar stijlgids.md>"}',
  phases: [
    { title: 'Verhaal', detail: 'art director: hoofdstukken, volgorde, layout per pagina' },
    { title: 'Teksten', detail: 'intro, bijschriften en alt-teksten per hoofdstuk' },
    { title: 'Bouw', detail: 'build.py, ON1 via Folder Actions, opnieuw bouwen' },
    { title: 'Controle', detail: 'print- en webcontrole, daarna één herstelronde' },
  ],
}

if (!args || !args.album || !args.curatie) throw new Error('Geef args.album en args.curatie.')
const { album, curatie } = args
const wensen = args.wensen || 'geen extra wensen'
// Optioneel: stijlgids met de eigen stem van de fotograaf (fotoselectie-pipeline/stijlgids-v1.0.0.md).
const stijlgids = args.stijlgids || ''

const PLAN = {
  type: 'object',
  properties: {
    titel: { type: 'string' },
    hoofdstukken: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          titel: { type: 'string' },
          thema: { type: 'string', description: 'waar dit hoofdstuk over gaat, voor de tekstschrijver' },
          moment_ids: { type: 'array', items: { type: 'integer' } },
        },
        required: ['titel', 'thema', 'moment_ids'],
      },
    },
    paginas_totaal: { type: 'integer' },
  },
  required: ['titel', 'hoofdstukken', 'paginas_totaal'],
}

const TEKST = {
  type: 'object',
  properties: {
    hoofdstuk: { type: 'string' },
    intro: { type: 'string' },
    paginas: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer', description: 'positie van de pagina binnen het hoofdstuk in album.json, vanaf 0' },
          bijschrift: { type: 'string' },
          alt: { type: 'array', items: { type: 'string' }, description: 'alt-tekst per foto, zelfde volgorde als fotos[]' },
        },
        required: ['index', 'bijschrift', 'alt'],
      },
    },
  },
  required: ['hoofdstuk', 'intro', 'paginas'],
}

const BEVINDINGEN = {
  type: 'object',
  properties: {
    bevindingen: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ernst: { type: 'string', enum: ['blokkerend', 'belangrijk', 'klein'] },
          waar: { type: 'string', description: 'pagina, hoofdstuk of bestand' },
          probleem: { type: 'string' },
          oplossing: { type: 'string', description: 'concrete wijziging in album.json of instellingen' },
        },
        required: ['ernst', 'waar', 'probleem', 'oplossing'],
      },
    },
  },
  required: ['bevindingen'],
}

phase('Verhaal')
const plan = await agent(
  `Je bent art director van een groot liggend fotoboek (Blurb Large Landscape 33x28 cm) met vooral vogelfoto's, dat ook als webpagina verschijnt.
Gebruik de skill eqwise-art-director voor je ontwerpoordeel. Lees ${curatie} (alleen momenten met albumwaardig=true) en selectie.json in dezelfde map (megapixels per foto).

Wensen van de fotograaf: ${wensen}

Schrijf ${album}. Bestaat het al, behoud dan "drukker", "web", "harmoniseren" en "on1" en vervang de rest. Bestaat het niet, neem die vier blokken over uit fotoalbum/voorbeeld/album.json en zet "fotomap" relatief naar de fotomap uit curatie.json. Lees fotoalbum/README.md voor het formaat.

Regels:
- Een verhaal, geen catalogus: hoofdstukken op seizoen, plek of leefgebied; afwisseling in ritme (rustige volle pagina na een drukke pagina), soorten niet allemaal achter elkaar.
- Layouts: vol, duo, drie, vier, passe-partout, panorama. Vol of panorama alleen voor de sterkste foto's (kwaliteit 4-5) met genoeg pixels: vol vraagt ongeveer 8,5 MP, panorama minstens 6300 px breed. Kleinere of sterk bijgesneden foto's in drie, vier of passe-partout.
- Zet "focus" zo dat kop en oog binnen beeld blijven bij bijsnijden; bij een panorama nooit kop of oog op het midden (de rug van het boek).
- Neem soorten met soort_status "ONEENS" niet op in bijschriften als zeker; laat bijschrift en alt leeg, de tekstschrijver vult ze.
- Komt curatie.json uit de fotoselectie-pipeline (veld "bron"), gebruik dan per moment "plek", "land", "tijd" en "categorie": hoofdstukken volgen de reis in de tijd, per plek (Serengeti, Ngorongoro, ...); zet per hoofdstuk "plek" en "land" zodat er niets online opgezocht hoeft te worden. Kwaliteit = sterren uit de facet-score; foto's met dezelfde "koppeling"-reeks of bijna dezelfde tijd zijn bijna-dubbelen: kies er één. Mensen (categorie "mensen") alleen met reden, en dan "alleen_print": true.
- Meerdere fotografen (veld "maker" per moment in curatie.json): neem "maker" en "tijd" (al gelijkgezet per toestel) over bij elke foto in album.json, zodat build.py "Foto: <naam>" bij het bijschrift zet. Zelfde moment door twee fotografen (zelfde soort, "tijd" binnen een paar minuten, al gelijkgezet per camera): kies alleen de beste, ongeacht van wie. Een goede mix van fotografen is prettig, maar kwaliteit gaat voor. Foto's van reisvrienden krijgen "alleen_print": true, tenzij album.json "medefotografen_web": true heeft of de wensen zeggen dat ze toestemming gaven. De plek van de bronvermelding staat in "fotocredits" ("per_foto", "begin", "eind" of "begin_en_eind"); laat die instelling staan.
- Omvang: gebruik het maximum uit "drukker.max_paginas" (standaard 240) als plafond en vul het boek als de selectie dat draagt; reken met de pagina's die build.py zelf toevoegt (titel, overzicht, per hoofdstuk opening en zo nodig kaart of luchtbeeld). Liever 200 sterke pagina's dan 240 met opvulling. Even aantal. Titelpagina, overzichtskaart en hoofdstukkaarten voegt build.py zelf toe.
- Ontwerp als een prijswinnend natuurfotoboek: veel wit, één sterke foto per spread waar dat kan, rust na drukte, kaartjes als decoratie die vertellen waar je bent. Zet "maker" (naam fotograaf) en per hoofdstuk zo nodig "plek" (bijvoorbeeld de naam van een wildpark als OSM die niet kent), "gps" ([lat, lon] als foto's geen GPS hebben) of "periode". Kies per hoofdstuk "icoon" (kust, duin, water, heide, bos, berg, savanne, ijs, veer of geen) als de automatische keuze op trefwoorden niet past.
Geef het plan terug: hoofdstukken met thema en moment_ids, in volgorde.`,
  { label: 'art director', schema: PLAN })
if (!plan) throw new Error('Art director gaf geen plan.')
log(`${plan.hoofdstukken.length} hoofdstukken, ${plan.paginas_totaal} pagina's`)

const teksten = await parallel(plan.hoofdstukken.map((h, i) => () => agent(
  `Schrijf de teksten voor hoofdstuk ${i + 1} "${h.titel}" van het fotoboek in ${album} (thema: ${h.thema}).
${stijlgids ? `Schrijf in de eigen stem van de fotograaf: lees eerst ${stijlgids} en houd je aan de kenmerken en aan de sectie "Wat dit NIET betekent" (niets verzinnen dat niet op de foto of in de gegevens staat). ` : 'Gebruik de skill eqwise-taalgebruik. '}Lees ${album} voor de pagina's van dit hoofdstuk en ${curatie} voor soort, soort_status, beschrijving en kenmerken per moment.
- intro: 2-3 zinnen, persoonlijk en concreet, geen clichés.
- bijschrift per pagina: kort; noem de soort alleen met zekerheid als soort_status "zeker" is, bij "waarschijnlijk" of "ONEENS" vaag blijven of de familie noemen.
- alt per foto: beschrijvend voor wie de foto niet ziet en goed vindbaar (soort, gedrag, omgeving), 8-16 woorden, niet beginnen met "foto van".
Wijzig ${album} NIET; geef alleen de teksten terug.`,
  { label: `teksten: ${h.titel}`, phase: 'Teksten', schema: TEKST })))

phase('Bouw')
const bouw = await agent(
  `Verwerk deze teksten in ${album} (per hoofdstuk op titel, per pagina op index; alt per foto in volgorde):
${JSON.stringify(teksten.filter(Boolean), null, 1)}

Daarna, in de repository:
1. python3 fotoalbum/build.py "${album}" --proef
2. Staat er iets in uitvoer/te-verbeteren.json? Draai python3 fotoalbum/on1_brug.py stuur "${album}" en dan python3 fotoalbum/on1_brug.py haal "${album}" --wacht 30.
   Komt er niets terug van ON1, ga dan door en meld dat ON1 niet draaide.
   Foto's met factor > 2,2: zet ze liever in een kleinere layout in ${album} dan ze te laten opblazen.
3. Bouw opnieuw met --proef.
Antwoord met: aantal pagina's, alle regels die met "!" beginnen uit de laatste build, en wat ON1 deed.`,
  { label: 'build + ON1', effort: 'low' })

phase('Controle')
const controles = await parallel([
  () => agent(
    `Controleer het boek als kritische fotoboekredacteur. Bekijk met Read: uitvoer/print/proef.png (in delen als het groot is), uitvoer/print/harmonisatie.jpg, en ${album}.
Buildrapport: ${bouw}
Let op: kop of oog van een vogel in de rug of buiten de veilige zone; tekst over een vogel; te kleine foto's (TE KLEIN, MATIG); kleurafstemming die een vogel onnatuurlijk maakt; herhaling van bijna dezelfde foto's; ritme en afwisseling; spreads die visueel botsen; lege of half lege pagina's.
Geef daarnaast als aparte bevinding (ernst "klein", waar "inkrimpen") de pagina's die het boek ZWAKKER maken: foto's die technisch of beeldend achterblijven bij de rest (onscherp oog, MATIG/TE KLEIN, bijna-dubbel, saaie compositie), zwakste eerst, met per pagina één zin waarom. Die worden niet automatisch verwijderd; de fotograaf kiest of het boek kleiner wordt.`,
    { label: 'printcontrole', phase: 'Controle', schema: BEVINDINGEN }),
  () => agent(
    `Controleer de webversie uitvoer/web/index.html van ${album}: alt-teksten aanwezig en zinvol, foto's met "alleen_print" echt weggelaten, JSON-LD geldig, eerste foto niet lazy, mobiel geen horizontaal scrollen (maak met Chrome headless een screenshot op 390 px breed en bekijk het), totale beeldgrootte redelijk.`,
    { label: 'webcontrole', phase: 'Controle', schema: BEVINDINGEN }),
])
const bevindingen = controles.filter(Boolean).flatMap(c => c.bevindingen)
const teHerstellen = bevindingen.filter(b => b.ernst !== 'klein')
log(`${bevindingen.length} bevindingen, ${teHerstellen.length} te herstellen`)

let herstel = 'niets te herstellen'
if (teHerstellen.length) {
  herstel = await agent(
    `Herstel deze bevindingen door ${album} aan te passen (niet de scripts), en bouw daarna opnieuw met python3 fotoalbum/build.py "${album}" --proef:
${JSON.stringify(teHerstellen, null, 1)}
Een bevinding die je niet kunt herstellen zonder de fotograaf (foto vervangen, soort onzeker): laat staan en noem hem. Antwoord met wat je deed en wat open blijft.`,
    { label: 'herstel', phase: 'Controle' })
}

return {
  plan: plan.hoofdstukken.map(h => h.titel),
  bouw,
  kleine_punten: bevindingen.filter(b => b.ernst === 'klein'),
  herstel,
}
