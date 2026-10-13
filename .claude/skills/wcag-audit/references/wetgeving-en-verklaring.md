# Accessibility legislation: EU, NL, BE, DE, UK, US, and the accessibility statement

Researched on 13 October 2026 from primary sources: EUR-Lex, wetten.overheid.nl, officielebekendmakingen.nl, acm.nl, digitoegankelijk.nl, economie.fgov.be, gesetze-im-internet.de, legislation.gov.uk, gov.uk, federalregister.gov and ada.gov. Items marked **[niet geverifieerd]** (not verified) did not come from a primary source. The law moves: re-check before giving a client advice with legal consequences, and recommend a lawyer for certainty. This is a working reference, not legal advice.

## 0. Quick decision for a client

1. **Government body or (semi-)public organisation?** → section 3 (public sector, WAD). In NL: Tijdelijk besluit digitale toegankelijkheid overheid (see 3.1).
2. **Selling online to consumers (B2C)?**
   - Selling only to businesses (B2B) → the EAA e-commerce rules do not apply (Art. 2(2) "provided to consumers", Art. 3(30) "consumer contract"). The national equal treatment law still applies (NL: WGBH/CZ).
   - Fewer than 10 employees AND turnover or balance sheet ≤ €2m → exempt in NL and DE. **Not in Belgium:** there micro-enterprises only get extra time until 28-06-2030.
   - Otherwise the EAA applies via national law (section 2).
3. **Customers in other EU countries?** → section 2.4 (cross-border).
4. **Banking, passenger transport, telecom, e-books, access to audiovisual media?** → also EAA, but with a different supervisor in NL (section 2.3).
5. **UK or US customers?** → sections 5 and 6.

## 1. Technical standard: WCAG 2.1 or 2.2?

- The laws name no WCAG version. Compliance is presumed via the harmonised standard **EN 301 549** cited in the Official Journal of the EU (EAA Art. 15, NL BW 6:230fd, DE BFSG § 4).
- **Current reference: EN 301 549 v3.2.1 (2021) = WCAG 2.1 A + AA.** It is cited in the OJ under the WAD by Implementing Decision (EU) 2021/1339. As of 13-10-2026 no standard was found cited specifically under the EAA. AccessibleEU calls v3.2.1 the current reference for EAA and WAD alike.
- **EN 301 549 v4.1.1 (September 2026) = WCAG 2.2 AA**, the first version written with the EAA in mind. AccessibleEU (07-09-2026): "not yet the legal reference standard … Until the European Commission formally cites EN 301 549 v4.1.1 in the Official Journal …, the current reference remains EN 301 549 v3.2.1". The date of that citation is not known; vendors expect end 2026 **[niet geverifieerd]**.
- **ACM (NL):** "In de loop van 2026 wordt WCAG 2.2 niveau AA de nieuwe standaard … Wij adviseren om al met WCAG 2.2 aan de slag te gaan."
- **Advice:** build and audit to WCAG 2.2 AA (a superset of 2.1). In reports, mark which findings are 2.2-only (2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8), so the client sees what is legally required today and what is future-proof.

## 2. European Accessibility Act (Directive (EU) 2019/882)

### 2.1 Directive (applies from 28 June 2025, Art. 31)
- **Services in scope (Art. 2(2), "provided to consumers")**:
  - (a) electronic communications
  - (b) access to audiovisual media (EPGs, subtitles and similar)
  - (c) air, bus, rail and waterborne passenger transport: websites, apps, e-tickets, real-time travel information and self-service terminals. For urban, suburban and regional transport only the terminals are covered.
  - (d) consumer banking (credit, payment services, e-money, some investment services)
  - (e) e-books
  - (f) **e-commerce**
- **E-commerce, Art. 3(30):** "services provided at a distance, through websites and mobile device-based services by electronic means and at the individual request of a consumer with a view to concluding a consumer contract". Recital 43 makes it apply to the online sale of any product or service.
- **Service provider, Art. 3(4):** anyone who "provides a service on the Union market or makes offers to provide such a service to consumers in the Union". Where the provider is established is not a criterion.
- **Excluded content (Art. 2(4)):**
  - pre-recorded media and office files published before 28-06-2025
  - online maps, if essential information is accessible in another way
  - third-party content the operator does not fund or control
  - archives not updated after 28-06-2025
- **Micro-enterprise, Art. 3(23):** fewer than 10 persons AND turnover ≤ €2m OR balance sheet ≤ €2m. Art. 4(5) exempts micro-enterprises **providing services** from the service requirements. Product requirements still apply to them.
- **Requirements (Annex I):**
  - Section III: the service is perceivable, operable, understandable and robust (POUR); the website and app are accessible "in a consistent and adequate way"; support services such as a help desk give accessibility information in accessible ways.
  - Section IV(g), e-commerce: (i) accessibility information about the products sold, where the economic operator provides it; (ii) accessible identification, security and payment; (iii) accessible identification methods, e-signatures and payment services.
  - Section IV(e), banking: the same, plus information no harder than CEFR level B2.
- **Information duty (Art. 13 + Annex V):** in the "general terms and conditions, or equivalent document", available in written and oral form, accessible, and kept for as long as the service runs. It must contain:
  - a general description of the service in an accessible format
  - an explanation of how the service works
  - how the requirements are met
- **Exceptions (Art. 14 + Annex VI):** fundamental alteration of the service, or a disproportionate burden.
  - The burden assessment must be documented and kept for 5 years, and redone at least every 5 years.
  - It cannot be used if the provider received outside funding for accessibility.
  - Authorities must be notified, except by micro-enterprises.
- **Transition (Art. 32):** service contracts concluded before 28-06-2025 may continue unchanged for at most 5 years (until 28-06-2030).
- **Penalties (Art. 30):** "effective, proportionate and dissuasive"; amounts are set nationally.
- **Not an accessibility statement in the WAD sense:** the EAA requires the Annex V information. In practice it is often published as a "toegankelijkheidsverklaring" (accessibility statement), and the Dutch and Belgian guidance use that term too.

### 2.2 Netherlands
- **Implementatiewet toegankelijkheidsvoorschriften producten en diensten**: Wet van 8 april 2024, Stb. 2024, 87; in force 28-06-2025 (Stb. 2024, 341). Transposition was about two years late.
- **Webshops: BW art. 6:230fa–230fd.**
  - 6:230fb: design and provide the service according to Annex I, sections III and IV(g), and Annex V; prepare and publish the information "schriftelijk en mondeling" (in writing and orally); keep procedures that maintain compliance; take corrective measures immediately.
  - 6:230fc: exempt "ondernemingen met minder dan 10 werknemers en een jaaromzet of een jaarlijks balanstotaal van ten hoogste 2 miljoen euro". ACM counts staff using the EU SME user guide. Ondernemersplein words this differently; follow the law.
  - 6:230fd: presumption of conformity via harmonised standards.
  - Transition: Overgangswet art. 190aa (old contracts, at most 5 years).
- **Other acts amended:** Warenwet (products), WGBH/CZ (art. 5c/5d), Telecommunicatiewet (ch. 7A), Wft art. 4:22.0a (banking) and Whc (art. 8.15, ch. 8A).
- **Supervisors (acm.nl):**

  | Area | Supervisor |
  |---|---|
  | E-commerce and electronic communications | ACM |
  | Financial e-commerce and banking | AFM |
  | E-books and access to audiovisual media | Commissariaat voor de Media |
  | Products and e-readers | RDI |
  | Passenger transport | ILT |
  | 112 | Inspectie J&V |

- **Sanctions:**
  - ACM can impose a fine under Whc art. 2.15 of at most €900,000 or 1% of turnover (4% in a coordinated EU CPC action), and a last onder dwangsom (an order with penalty payments). Whether art. 8.15 is in the fineable annex could not be read from the scraped text **[niet geverifieerd]**.
  - CvdM and ILT: up to the 5th category fine.
- **ACM guidance (acm.nl web page, last modified 07-05-2026):**
  - WCAG 2.1 AA now, 2.2 AA advised.
  - **"Een onafhankelijke WCAG-audit of keuring is dus niet verplicht"** (an independent audit or inspection is not required); no certificate or label is needed.
  - The toegankelijkheidsverklaring must be easy to find, accessible itself, and also offered orally (for example as an audio fragment).
  - The customer service desk must give accessibility information accessibly.
  - Product accessibility information must be shown, and login, payment and signing, including the related e-mails, must be accessible.
  - The provider stays responsible when it hires a web builder.
  - **Meldplicht** (duty to report): non-compliance must be reported to the ACM, with an improvement plan, within **1 week** for critical or serious problems and within **1 month** for moderate or minor ones, unless fixed within that time. A claimed exception must also be reported.
  - "Ontbreekt het u aan tijd of kennis? Dan telt dit niet als onevenredige last" (lacking time or knowledge does not count as a disproportionate burden).
- **ACM enforcement:** 61% of about 100 of the largest Dutch webshops were not accessible (publication around March 2026 **[datum niet geverifieerd]**). Webshop accessibility is an ACM priority for 2026, and consumers can report problems to the ACM.
- **WGBH/CZ:** the duty to make effective adjustments, gradually ensure general accessibility, and not discriminate in goods and services also applies to private companies. Complaints go to the College voor de Rechten van de Mens. Article numbers and case law **[niet geverifieerd]**.
- **SME information:** ondernemersplein.overheid.nl ("Regels voor digitale toegankelijkheid") and the mkbtoegankelijk.nl test.

### 2.3 Belgium (FOD Economie guideline "Toegankelijke e-handelsdiensten", 07-10-2026)
- **Law:** Wet van 5 november 2023, which amends the Wetboek van economisch recht (WER), Book VIII, art. VIII.59–VIII.62 and annexes 1–2, for banking and e-commerce. Products and telecom are covered by separate acts **[niet geverifieerd]**.
- **Micro-enterprises are NOT exempt.** They get an extra transition period until **28-06-2030**. This differs from NL and DE.
- **Information duty:** in the general terms and conditions "of in een gelijkwaardig document zoals een toegankelijkheidsverklaring" (or an equivalent document such as an accessibility statement).
- **Exceptions:** an exception must be reported in advance to the Economische Inspectie via accessibility-exceptions.economie.fgov.be.
- **Supervisor:** FOD Economie, Economische Inspectie. Complaints go via ConsumerConnect.
- **Sanctions:**
  - settlement (transactie) €26–€60,000
  - administrative fine €260–€100,000 or up to 4% of annual turnover
  - in bad faith: up to €250,000 or 6% of annual turnover
  - collective action (for example by Test-Aankoop) is also possible
- **Technical standard:** the guideline lists functional requirements only and names no WCAG version. EN 301 549 is the logical yardstick through the presumption of conformity.
- **Public sector:** Wet van 19 juli 2018 (federal), plus regional decrees and ordinances. Standard EN 301 549; accessibility statement following the EU model; monitoring by FOD BOSA and the regional bodies.

### 2.4 Germany
- **BFSG** (Barrierefreiheitsstärkungsgesetz, 16-07-2021). Services for consumers after 28-06-2025.
- **Micro-enterprise exemption for services:** § 3(3), § 2 no. 17.
- **Standard:** presumption of conformity via harmonised standards (§ 4); WCAG 2.1 AA in practice.
- **Information duty (§ 14, Anlage 3):** in the AGB (general terms and conditions) "oder auf andere deutlich wahrnehmbare Weise" (or another clearly visible way), with a general description of the service in an accessible format, among other content.
- **Supervisor:** MLBF (Marktüberwachungsstelle der Länder für die Barrierefreiheit), Magdeburg, fully operational since 26-09-2025.
- **Fines (§ 37):** up to €100,000 (for example offering a non-compliant service), and up to €10,000 for information failures. The service can be banned as a last resort **[§ 30 niet geverifieerd]**.
- **Consumers and associations** can ask the MLBF to act (§ 32). Conciliation (Schlichtung) is possible (§ 34).
- **Competitor warnings (Abmahnungen) under UWG §§ 3, 3a:** being sent since July 2025. No published court decision yet on whether the BFSG is a "Marktverhaltensregel" (market conduct rule).
- **Transition:** old contracts until 27-06-2030.
- **Public sector:** BITV 2.0, via EN 301 549 v3.2.1 (WCAG 2.1 AA).

### 2.5 Selling across EU borders

**Which law applies?** In principle the law of **every EU country where you sell to consumers**, in parallel with the law of your home country.
- The EAA defines the service provider by the market it offers to (Art. 3(4): "provides a service on the Union market or makes offers … to consumers in the Union").
- In case of non-compliance, the provider must inform "the competent national authorities of the Member States in which the service is provided" (Art. 13(4)).
- Every member state must check the compliance of services (Art. 23).
- National laws copy this scope: BFSG § 2, and § 14 (notify the authorities of all member states "in denen er die Dienstleistung anbietet"); Austria's BaFG § 3; Italy's AgID guideline 2026.
- **ACM:** "Bent u actief in meerdere EU-landen? Dan moet u zich melden bij de toezichthouder van elk land waar u actief bent. Toezichthouders werken ook onderling samen. U blijft zelf verantwoordelijk voor de meldingen in elk land."

**The e-Commerce Directive's country-of-origin principle: open question.**
- Directive 2000/31/EC Art. 3(2) bars other states from restricting an online service from another member state for reasons in the "coordinated field". Arguments exist that this limits how far a foreign authority can act against a Dutch webshop.
- Arguments against:
  - the e-Commerce Directive leaves consumer protection under EU acts unaffected (Art. 1(3));
  - the EAA gives a role to every country where the service is provided;
  - EAA Art. 6 (free movement) protects only services that *do* comply.
- No Commission, AccessibleEU or national authority statement settles this, and there is no case law yet. **Present it as unresolved.** Practical advice: assume the authorities of each country you sell to may act.

**Technical level:** the same everywhere. All countries transpose the same Annex I and use the same harmonised standard (EN 301 549). A webshop that meets WCAG 2.1 AA (today) or WCAG 2.2 AA (soon) meets the technical requirements in every EU country.

**What differs per country:** procedure, enforcement, fines, micro-enterprise treatment and national extras.

| Country | Law | Authority (e-commerce) | Max fine (primary source unless marked) | Micro-enterprise | Notable |
|---|---|---|---|---|---|
| NL | Implementatiewet, Stb. 2024, 87; BW 6:230fa–fd | ACM | Whc: €900,000 or 1% turnover (fineability of art. 8.15 **[niet geverifieerd]**) | Exempt | Duty to report to ACM within 1 week or 1 month, with a plan |
| BE | Wet 5-11-2023 (WER Book VIII) | FOD Economie, Economische Inspectie | Guideline 07-10-2026: admin fine €260–€100,000 or 4% turnover; in bad faith up to €250,000 or 6%. A FOD news item says "tot maximum 200.000 euro of 6 %", so the sources differ. | **Not exempt**; extra time until 28-06-2030 | Exception must be notified in advance via a portal; collective action possible |
| DE | BFSG (2021), in force 28-06-2025 | MLBF, Magdeburg | €100,000; information failures €10,000 | Exempt | Info in the AGB or "deutlich wahrnehmbar"; Abmahnungen are being sent, with no case law yet |
| FR | Loi 2023-171 art. 16, Décret 2023-931; Code de la consommation | DGCCRF | €7,500 per breach for a legal person (€15,000 repeat), cumulative per service and per obligation, plus daily penalties | Exempt | Existing RGAA and statement duties for companies with turnover above €250m **[secundair]**; associations have gone to court against large retailers **[secundair]** |
| AT | BaFG | Sozialministeriumservice | €80,000 / €40,000; SMEs €25,000 for certain offences | Exempt | Stricter national requirements stay in force (§ 7) |
| IT | D.Lgs. 82/2022 | AgID | €5,000–40,000 **[secundair]**; up to 5% turnover for providers above €500m (Legge Stanca) | Exempt | Legge Stanca duties, including a statement, for large companies |
| ES | Ley 11/2023 | **[niet geverifieerd]** | up to €1m **[secundair]** | Exempt **[secundair]** | Cognitive accessibility rules **[niet gelezen]** |
| IE | S.I. 636/2023 | CCPC | €60,000 and/or 18 months on indictment **[secundair]** | **[niet geverifieerd]** | Criminal sanctions possible |
| LU | Loi du 8 mars 2023 | OSAPS | **[niet geverifieerd]** | guide exists **[inhoud niet geverifieerd]** | |

**Language of the accessibility information:** the EAA sets no language rule for the service information (Annex V refers to the general terms and conditions "or equivalent document"). National consumer and language rules (for example France's Loi Toubon) and plain comprehensibility point to **the language of the consumer**. Recommend it; do not present it as an EAA duty.

**Transposition:** almost every member state was late (deadline 28-06-2022). In January 2026 the Commission (INF/26/115) sent reasoned opinions to BE, CZ, FR, LV and FI, and additional ones to CY, **NL**, SI and SE, for incomplete transposition (gaps mainly in emergency communications, scope, definitions and enforcement). National laws may still change; check the current text.

**Practical advice for a Dutch webshop selling in the EU:**
1. Meet WCAG 2.2 AA everywhere: one technical level covers all countries.
2. Publish the accessibility information in the language of each target market, linked from the general terms and conditions of each language version.
3. A micro-enterprise selling to **Belgium** must be compliant there by 28-06-2030 at the latest.
4. On non-compliance, report to the authority of **each** country where the shop sells (ACM: "U blijft zelf verantwoordelijk voor de meldingen in elk land"). Know the national procedure, for example Belgium's prior notification of exceptions.
5. Germany carries the highest practical risk of private warning letters (Abmahnungen).

## 3. Public sector (Web Accessibility Directive (EU) 2016/2102)

- **Covers:** websites and apps of public sector bodies. Excluded: public broadcasters, and NGOs without essential services. Schools are optional.
- **Excluded content:** similar to the EAA, plus live media and older intranets.
- **Standard:** EN 301 549 v3.2.1 (WCAG 2.1 AA).
- **Accessibility statement (Art. 7):** must name the non-accessible content and why, offer a feedback mechanism, and link to the enforcement procedure. Monitoring follows the EU methodology.
- **Overlap with the EAA:** a public body that runs e-commerce or transport services must also comply with the EAA (EAA recital 46).

### 3.1 Netherlands
- **Tijdelijk besluit digitale toegankelijkheid overheid** (BWBR0040936, in force since 01-07-2018; still titled "Tijdelijk"). digitoegankelijk.nl calls it "Bdto"; digitaleoverheid.nl says it is now structurally embedded in the Wet digitale overheid.
- **Requirements:** apply EN 301 549 (WCAG 2.1 A + AA, "50 eisen"), publish a statement using the model, register it on toegankelijkheidsverklaring.nl, and show the toegankelijkheidslabel.
- **Statuses (digitoegankelijk.nl):**

  | Status | Meaning | Complies with the law? |
  |---|---|---|
  | A | Meets all 50 requirements; complete research less than 3 years old | Yes |
  | B | Research less than 3 years old, meets fewer than 50 | Yes, if measures are described and there is improvement every year |
  | C | No proper research, but research planned within 6 months | Yes, for at most 6 months from publication |
  | D | Statement without research or plan | No |
  | E | No statement | No |

  Statements with status A or B must be updated at least once a year. When a term expires the statement falls back to D.
- **Research valid for A or B:** at most 3 years old, done with the **WCAG-EM** method, covering all 50 requirements and the whole site (including PDFs and pages behind a login), and the report must meet the checklist. **No requirement of an independent party was found.** An audit with this skill can support that research when done per WCAG-EM; say clearly where manual checks are still open.

## 4. Template: toegankelijkheidsverklaring for a webshop (EAA / Annex V)

Place it on its own page, link it from the footer on every page and from the general terms and conditions, and also offer it orally (an audio fragment, or reading it out on request).

```markdown
# Toegankelijkheidsverklaring

[Organisatie] wil dat iedereen [domein] kan gebruiken, ook mensen met een beperking.

## Onze dienst
[Algemene beschrijving van de dienst: wat je verkoopt, hoe bestellen, betalen,
inloggen en klantenservice werken.]

## Hoe we aan de toegankelijkheidseisen voldoen
We toetsen aan WCAG 2.2 niveau AA (de wettelijke maatstaf is nu WCAG 2.1 AA via
EN 301 549). Op [datum] hebben we [aantal] pagina's en de bestel- en betaalstappen
onderzocht met geautomatiseerde tests, toetsenbord- en zoomtests en een handmatige
beoordeling. [Wat er goed werkt: navigeren met toetsenbord, schermlezer, contrast,
inloggen en betalen, productinformatie over toegankelijkheid.]

## Bekende problemen
| Probleem | Waar | WCAG | Opgelost uiterlijk |
|---|---|---|---|
| [...] | [...] | [...] | [maand jaar] |

## Hulp en contact
Loop je ergens tegenaan? Mail [e-mail] of bel [telefoon]. Onze klantenservice
kan deze informatie ook voorlezen. We reageren binnen [5] werkdagen.
Je kunt ook een melding doen bij de Autoriteit Consument & Markt (ACM).

Opgesteld op [datum], laatst bijgewerkt op [datum].
```

**Writing rules:**
- Only claim what the audit shows.
- Write at language level B1.
- Name known problems with a realistic date.
- Re-check after every major site change and at least once a year.
- For customers in other countries, see 2.5 for language and other requirements.

## 5. United Kingdom (not EU; the EAA does not apply in Great Britain)

- **Public sector:** Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018 (SI 2018/952).
  - Reg 9 (as amended by SI 2022/1097) refers to WCAG A + AA "as amended from time to time", so **WCAG 2.2 AA** applies; GDS has monitored against it since October 2024.
  - An accessibility statement following the model is required (reg 8).
  - Monitoring: GDS/CDDO. Enforcement: EHRC (GB) and ECNI (NI).
- **Private sector:** Equality Act 2010, s.29 (services) and s.20 (reasonable adjustments). The duty is anticipatory: Schedule 2 para 2 refers to "disabled persons generally". There is no statutory WCAG level; the risk is a discrimination claim, and WCAG AA is the de facto benchmark.
- **Northern Ireland:** the Disability Discrimination Act 1995 applies instead. According to ECNI, NI law need not keep pace with the EAA under the Windsor Framework. The position for products under Annex 2 is **[niet geverifieerd]**.
- **EU customers:** a UK business selling to consumers in the EU falls under the EAA (Art. 3(4)).

## 6. United States (brief)

- **ADA Title III (businesses):** the DOJ says the ADA applies to the web, but there is no technical regulation; WCAG is "helpful guidance". Case law **[niet geverifieerd]**.
- **ADA Title II (state and local government):** WCAG 2.1 AA (rule of April 2024). Deadlines were moved by an Interim Final Rule of 20-04-2026: **26-04-2027** for populations of 50,000 or more, **26-04-2028** for smaller ones.
- **Section 508 (federal agencies):** WCAG 2.0 AA.
