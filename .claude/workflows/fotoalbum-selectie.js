export const meta = {
  name: 'fotoalbum-selectie',
  description: 'Fotoalbum stap 1: bursts groeperen, per moment de beste opname kiezen, curatie en vogelsoort met onafhankelijke controle',
  whenToUse: 'Start van een nieuw fotoalbum, zodra de foto\'s in fotos/origineel/ en fotos/bewerkt/ staan. Args: {fotomap: "<pad>", lokaal?: true | "mlx" | "mlx:<model>" | "<modelnaam>", regio?: "Tanzania"}',
  phases: [
    { title: 'Inventaris', detail: 'selectie.py: bursts, scherpte, contactvellen' },
    { title: 'Curatie', detail: 'per batch momenten beoordelen en soort bepalen' },
    { title: 'Soortcontrole', detail: 'tweede, blinde determinatie per moment' },
    { title: 'Samenvatting', detail: 'curatie.json en overzicht voor goedkeuring' },
  ],
}

if (!args || !args.fotomap) throw new Error('Geef args.fotomap: de map met origineel/ en bewerkt/.')
const FOTOMAP = args.fotomap
// Optioneel: lokaal beeldmodel (bijv. Qwen-VL in Ollama/LM Studio) als derde, onafhankelijke determinatie.
// args.lokaal: true (automatische modelkeuze) of een modelnaam; args.regio: bijv. "Tanzania".
const LOKAAL = args.lokaal || false
const REGIO = args.regio || ''
// "mlx" of "mlx:<model>" = direct via mlx-vlm (qwen_local op de Mac mini); andere tekst = modelnaam op een server.
const LOKAAL_OPTIE = LOKAAL === true ? '' : String(LOKAAL).startsWith('mlx')
  ? `--mlx ${String(LOKAAL).includes(':') ? `"${String(LOKAAL).slice(4)}" ` : ''}` : `--model "${LOKAAL}" `
const MAX_BATCHES = 4

const INVENTARIS = {
  type: 'object',
  properties: {
    uitmap: { type: 'string', description: 'absolute map met selectie.json en contactvellen' },
    groepen: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'integer' },
          contactvel: { type: 'string', description: 'absoluut pad' },
          keuze: { type: 'array', items: { type: 'string' } },
          reden: { type: 'string' },
          aantal: { type: 'integer' },
        },
        required: ['id', 'contactvel', 'keuze', 'reden', 'aantal'],
      },
    },
  },
  required: ['uitmap', 'groepen'],
}

const CURATIE = {
  type: 'object',
  properties: {
    momenten: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'integer' },
          keuze: { type: 'array', items: { type: 'string' }, description: 'definitieve bestand(en), relatief aan de fotomap' },
          keuze_gewijzigd: { type: 'boolean' },
          albumwaardig: { type: 'boolean' },
          kwaliteit: { type: 'integer', minimum: 1, maximum: 5 },
          soort: { type: 'string', description: 'Nederlandse naam van de vogel of het andere dier; "geen dier" bij landschap of mensen' },
          wetenschappelijke_naam: { type: 'string', description: 'Latijnse naam, leeg als onbekend' },
          soort_zekerheid: { type: 'string', enum: ['hoog', 'middel', 'laag'] },
          beschrijving: { type: 'string', description: 'één zin: wat gebeurt er, licht, omgeving' },
          opmerking: { type: 'string', description: 'probleem of reden voor wijziging, leeg als niets' },
        },
        required: ['id', 'keuze', 'keuze_gewijzigd', 'albumwaardig', 'kwaliteit', 'soort', 'wetenschappelijke_naam', 'soort_zekerheid', 'beschrijving', 'opmerking'],
      },
    },
  },
  required: ['momenten'],
}

const SOORT = {
  type: 'object',
  properties: {
    oordelen: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'integer' },
          soort: { type: 'string' },
          wetenschappelijke_naam: { type: 'string' },
          zekerheid: { type: 'string', enum: ['hoog', 'middel', 'laag'] },
          kenmerken: { type: 'string', description: 'zichtbare kenmerken waarop het oordeel rust' },
          lokaal_soort: { type: 'string', description: 'antwoord van het lokale model, leeg als niet gebruikt' },
          lokaal_wetenschappelijk: { type: 'string' },
          lokaal_zekerheid: { type: 'string' },
        },
        required: ['id', 'soort', 'wetenschappelijke_naam', 'zekerheid', 'kenmerken'],
      },
    },
    lokaal_model: { type: 'string', description: 'naam van het gebruikte lokale model, leeg als niet gebruikt' },
  },
  required: ['oordelen'],
}

phase('Inventaris')
const inv = await agent(
  `Draai in de repository: python3 fotoalbum/selectie.py "${FOTOMAP}"
Dat schrijft selectie.json en groep-NNN.jpg contactvellen in <fotomap>/../uitvoer/selectie/.
Lees daarna selectie.json en geef per groep id, het ABSOLUTE pad van het contactvel, keuze, reden en het aantal foto's.
Fouten van het script: los ze niet op door code te wijzigen; meld ze in je antwoord door groepen leeg te laten.`,
  { label: 'selectie.py', schema: INVENTARIS, effort: 'low' })

if (!inv || !inv.groepen.length) throw new Error('Geen foto\'s gevonden of selectie.py faalde.')
log(`${inv.groepen.length} momenten gevonden`)

const grootte = Math.ceil(inv.groepen.length / Math.min(MAX_BATCHES, Math.ceil(inv.groepen.length / 15)))
const batches = []
for (let i = 0; i < inv.groepen.length; i += grootte) batches.push(inv.groepen.slice(i, i + grootte))

const resultaten = await pipeline(
  batches,
  (batch, _, n) => agent(
    `Je bent curator van een fotoalbum met vooral vogel- en wildfoto's (veel burst-JPG's), bijvoorbeeld van een safari in Oost-Afrika.
Bekijk met Read elk contactvel hieronder. Links staan alle opnames van één moment met hun scherptescore, groen = automatische keuze; rechts een 100%-uitsnede van de keuze.

Beoordeel per moment:
- Is de keuze goed? Het OOG van de vogel moet scherp zijn; vogel niet afgesneden (vleugelpunten, staart, poten); geen storende tak voor kop of oog; licht en houding. Scherptescores meten het hele beeld en kunnen misleiden (scherpe takken, onscherpe vogel). Wijzig de keuze als een andere opname duidelijk beter is; geef dan het relatieve bestandspad uit de groep. Kies alleen een tweede opname als die echt iets anders laat zien (andere houding, actie).
- Bevat de reden "LET OP: ... veel scherper"? Vergelijk de bewerkte versie met het scherpere frame en meld in opmerking wat beter is; wijzig de keuze niet zelf, de fotograaf beslist.
- albumwaardig: zou een kritische natuurfotograaf deze opname in een groot fotoboek willen? Bijna-dubbelen van een ander moment in deze batch: alleen de beste albumwaardig.
- soort: Nederlandse naam van de vogel of het zoogdier (ook olifant, leeuw, gnoe), plus de wetenschappelijke naam. Veel Oost-Afrikaanse soorten lijken sterk op elkaar (scharrelaars, glansspreeuwen, wevers, gieren, gazellen): eerlijke zekerheid, twijfel = middel of laag. Let op de regio uit de map- of bestandsnaam en EXIF.
- beschrijving: één feitelijke zin.

Momenten (id, contactvel, huidige keuze, reden):
${batch.map(g => `- ${g.id}: ${g.contactvel} | keuze ${g.keuze.join(', ')} | ${g.reden}`).join('\n')}`,
    { label: `curatie ${n + 1}/${batches.length}`, phase: 'Curatie', schema: CURATIE }),
  (cur, batch, n) => {
    if (!cur) return null
    // Blinde tweede determinatie: de controleur ziet het eerste oordeel niet.
    const vogels = cur.momenten.filter(m => m.albumwaardig && !/^geen /.test(m.soort))
    if (!vogels.length) return { cur, soort: { oordelen: [] } }
    return agent(
      `Determineer onafhankelijk de diersoort (vogel of zoogdier) op deze foto's, met Nederlandse en wetenschappelijke naam. Houd rekening met de regio waar de foto's zijn gemaakt (bijvoorbeeld Tanzania). Open elke foto met Read (paden relatief aan ${FOTOMAP}).
Noem de zichtbare kenmerken waarop je oordeel rust (snavel, oogring, vleugelstrepen, poten, verenkleed, formaat t.o.v. omgeving).
Wees streng: geslacht of familie is beter dan een verkeerde soort; dan zekerheid laag.

${vogels.map(m => `- ${m.id}: ${m.keuze[0]}`).join('\n')}
${LOKAAL ? `
Daarna, PAS NA je eigen oordeel: laat het lokale beeldmodel dezelfde foto's determineren met
  python3 fotoalbum/soort_lokaal.py herken ${LOKAAL_OPTIE}${REGIO ? `--regio "${REGIO}" ` : ''}<paden>
Geeft het script per foto een "fout" (bijv. model zonder beeldinvoer), laat de lokaal-velden dan leeg en noem de fout in je antwoord.
(paden relatief aan ${FOTOMAP}) en neem per id over: lokaal_soort, lokaal_wetenschappelijk, lokaal_zekerheid, plus lokaal_model.
Pas je eigen oordeel NIET aan op dat van het lokale model. Draait er geen lokaal model, laat de velden leeg.` : ''}`,
      { label: `soortcontrole ${n + 1}/${batches.length}`, phase: 'Soortcontrole', schema: SOORT })
      .then(soort => ({ cur, soort }))
  },
)

phase('Samenvatting')
const momenten = []
for (const r of resultaten.filter(Boolean)) {
  const tweede = new Map((r.soort ? r.soort.oordelen : []).map(o => [o.id, o]))
  for (const m of r.cur.momenten) {
    const o = tweede.get(m.id)
    // Eens als de Nederlandse of de wetenschappelijke naam overeenkomt (Nederlandse namen variëren).
    const gelijk = (a, b) => a && b && a.trim().toLowerCase() === b.trim().toLowerCase()
    const zelfde = (a, an, b, bn) => gelijk(a, b) || gelijk(an, bn)
    const eens = !o || zelfde(o.soort, o.wetenschappelijke_naam, m.soort, m.wetenschappelijke_naam)
    // Derde stem van het lokale model: beslist bij onenigheid (2 van 3), en verlaagt "zeker" als het afwijkt.
    const lokaal = o && o.lokaal_soort ? zelfde(o.lokaal_soort, o.lokaal_wetenschappelijk, m.soort, m.wetenschappelijke_naam)
      ? 'curator' : zelfde(o.lokaal_soort, o.lokaal_wetenschappelijk, o.soort, o.wetenschappelijke_naam) ? 'controle' : 'anders' : null
    momenten.push({
      ...m,
      soort_controle: o ? o.soort : null,
      soort_kenmerken: o ? o.kenmerken : null,
      // Pas "zeker" als beide onafhankelijk dezelfde soort met hoge zekerheid noemen.
      soort_lokaal: o && o.lokaal_soort ? `${o.lokaal_soort} (${o.lokaal_wetenschappelijk || '?'}, ${o.lokaal_zekerheid || '?'})` : null,
      soort_status: !o ? 'niet gecontroleerd'
        : !eens ? (lokaal === 'curator' ? 'waarschijnlijk (2 van 3)' : lokaal === 'controle' ? `waarschijnlijk ${o.soort} (2 van 3)` : 'ONEENS: fotograaf beslist')
        : lokaal === 'anders' ? 'waarschijnlijk (lokaal model wijkt af)'
        : (m.soort_zekerheid === 'hoog' && o.zekerheid === 'hoog') ? 'zeker' : 'waarschijnlijk',
    })
  }
}
const ontbrekend = inv.groepen.length - momenten.length
if (ontbrekend > 0) log(`LET OP: ${ontbrekend} momenten zonder curatie (agent faalde); die staan als niet beoordeeld in curatie.json`)

const samenvatting = await agent(
  `Schrijf dit JSON-object naar ${inv.uitmap}/curatie.json (met Write, ongewijzigd):
${JSON.stringify({ fotomap: FOTOMAP, momenten }, null, 1)}

Maak daarna ${inv.uitmap}/curatie.html: een overzicht voor de fotograaf om goed te keuren, per moment het contactvel (relatieve src groep-NNN.jpg), soort met status, kwaliteit, albumwaardig ja/nee, opmerking. Zet bovenaan eerst alles wat een beslissing vraagt: soort_status ONEENS, opmerkingen met LET OP, en gewijzigde keuzes. Donkere, rustige opmaak, werkt op mobiel.
Antwoord met een korte Nederlandse samenvatting: aantal momenten, albumwaardig, soorten, en de punten die de fotograaf moet beslissen.`,
  { label: 'curatie.json + overzicht', effort: 'low' })

return { uitmap: inv.uitmap, momenten: momenten.length, albumwaardig: momenten.filter(m => m.albumwaardig).length, samenvatting }
