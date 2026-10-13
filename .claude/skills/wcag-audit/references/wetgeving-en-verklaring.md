# Legislation and the toegankelijkheidsverklaring (accessibility statement)

> Laws and their supervision change. Check the current text (wetten.overheid.nl, digitoegankelijk.nl, the ACM website) before advising a client on legal duties, and recommend legal advice for certainty. This file is a working summary, not legal advice.

## Which regime applies?

| Organisation | Regime | Core duty |
|---|---|---|
| Government bodies (Rijk, gemeenten, provincies, waterschappen, many semi-public bodies) | Besluit digitale toegankelijkheid overheid (in force since 2018) | WCAG 2.1 AA via EN 301 549, plus a published toegankelijkheidsverklaring in the register on digitoegankelijk.nl |
| Companies offering services covered by the **European Accessibility Act** (Directive (EU) 2019/882), applying since **28 June 2025** | Dutch implementation of the EAA | Accessible website/app for the covered service + information on how the service meets the requirements |
| Other businesses | No general legal duty for the website (equal treatment law can still apply) | Voluntary, but good for usability, SEO and reach |

### EAA services in scope (consumer-facing)
- e-commerce: selling products or services online to consumers (webshops, booking and ordering sites)
- consumer banking services
- passenger transport services (websites, apps, e-tickets, travel information) for air, bus, rail and water
- electronic communication services
- services giving access to audiovisual media
- e-books and their software

**Micro-enterprise exemption (services):** fewer than 10 employees **and** an annual turnover or balance sheet total of at most €2 million. Note: they are exempt, not forbidden; recommend accessibility anyway.

Technical yardstick: EN 301 549 (whose web part is WCAG 2.1 AA). Aim for WCAG 2.2 AA so the site is ready for the next update of the standard.

Supervision in the Netherlands is done by designated regulators (the ACM for many consumer services). Check the current assignment of regulators before naming one to a client.

## What the statement must contain

### EAA service information (in terms and conditions or an equivalent public page)
- a description of the service in an accessible format
- how the service meets the accessibility requirements (which standard, what has been done)
- any claimed exemption (disproportionate burden) with its reasoning
- a contact point for questions and complaints, and the supervisory authority

### Government toegankelijkheidsverklaring
Made with the generator on digitoegankelijk.nl and published in the register. Its status (A = voldoet volledig, B = voldoet gedeeltelijk, C = eerste maatregelen genomen, and lower statuses) depends on an **audit report from an independent expert party** following WCAG-EM. An audit made with this skill supports the work, but is not that independent audit. Say so clearly.

## Template: voluntary toegankelijkheidsverklaring (Dutch, for the client's site)

```markdown
# Toegankelijkheidsverklaring

[Organisatie] wil dat iedereen [domein] kan gebruiken, ook mensen met een beperking.
We streven naar de richtlijnen WCAG 2.2 op niveau AA.

## Hoe toegankelijk is deze website?
Op [datum] hebben we [aantal] representatieve pagina's onderzocht: [lijst of omschrijving:
homepagina, dienstenpagina's, contactformulier, blog, zoekresultaten].
We gebruikten geautomatiseerde tests (axe-core), toetsenbord- en zoomtests en een
handmatige beoordeling.

Uitkomst: de website voldoet [grotendeels / gedeeltelijk] aan WCAG 2.2 AA.

## Bekende problemen
| Probleem | Waar | WCAG | Opgelost uiterlijk |
|---|---|---|---|
| [bijv. Sommige video's hebben nog geen ondertiteling] | [Blog] | 1.2.2 | [maand jaar] |

## Wat we hebben verbeterd
- [bijv. Alle knoppen en links zijn nu goed zichtbaar als je met het toetsenbord navigeert]
- [bijv. Formuliervelden hebben duidelijke labels]

## Loop je ergens tegenaan?
Mail naar [e-mailadres] of bel [telefoon]. Vertel ons om welke pagina het gaat en wat er
misgaat. We reageren binnen [5] werkdagen en zoeken samen naar een oplossing.

[Alleen voor EAA-diensten: Ben je niet tevreden over onze reactie? Je kunt een klacht
indienen bij [toezichthouder].]

Deze verklaring is opgesteld op [datum] en voor het laatst bijgewerkt op [datum].
```

## Writing rules
- Only claim what the audit evidence shows. List known problems honestly with realistic dates.
- Write in plain Dutch (B1 level), and make the statement page itself accessible.
- Link it from the footer on every page ("Toegankelijkheid").
- Re-audit at least once a year and after a redesign, and update the date.
