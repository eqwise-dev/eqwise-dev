"""WCAG 2.2 level A + AA success criteria (the EN 301 549 / EAA target).

auto    = reliably tested by axe-core or wcag.py
partial = tooling finds some failures; a human/Claude check is still required
manual  = needs human/Claude judgement (wcag.py may collect evidence)

4.1.1 Parsing is obsolete in WCAG 2.2 and omitted.
"""

CRITERIA = {
    # id: (level, english name, dutch name, automation, how to check)
    "1.1.1": ("A", "Non-text Content", "Niet-tekstuele content", "partial",
              "Every informative image has an alt that conveys its purpose; decorative images have alt=\"\"; icons and image links have an accessible name. Review the image crops: is each alt text accurate and useful?"),
    "1.2.1": ("A", "Audio-only and Video-only (Prerecorded)", "Louter-geluid en louter-video (vooraf opgenomen)", "manual",
              "Audio-only content has a transcript; video-only content has a transcript or audio track."),
    "1.2.2": ("A", "Captions (Prerecorded)", "Ondertitels voor doven en slechthorenden (vooraf opgenomen)", "manual",
              "Every video with speech has accurate captions (not only auto-generated YouTube captions)."),
    "1.2.3": ("A", "Audio Description or Media Alternative (Prerecorded)", "Audiodescriptie of media-alternatief (vooraf opgenomen)", "manual",
              "Visual information in video that is not spoken is available as audio description or a text alternative."),
    "1.2.4": ("AA", "Captions (Live)", "Ondertitels voor doven en slechthorenden (live)", "manual",
              "Live streams have live captions."),
    "1.2.5": ("AA", "Audio Description (Prerecorded)", "Audiodescriptie (vooraf opgenomen)", "manual",
              "Prerecorded video has audio description where visuals carry information that is not spoken."),
    "1.3.1": ("A", "Info and Relationships", "Info en relaties", "partial",
              "Headings, lists, tables, form labels and landmarks are marked up in code, not only visually. Review the heading outline and the ARIA snapshot."),
    "1.3.2": ("A", "Meaningful Sequence", "Betekenisvolle volgorde", "manual",
              "DOM/reading order matches the visual order (check the ARIA snapshot against the screenshot, especially in builder columns)."),
    "1.3.3": ("A", "Sensory Characteristics", "Zintuiglijke eigenschappen", "manual",
              "Instructions do not rely only on shape, colour, size, position or sound (\"klik op de groene knop rechts\")."),
    "1.3.4": ("AA", "Orientation", "Weergavestand", "partial",
              "Content works in both portrait and landscape; nothing forces one orientation."),
    "1.3.5": ("AA", "Identify Input Purpose", "Identificeer het doel van de input", "partial",
              "Personal data fields (name, email, phone, address) have the correct autocomplete attribute."),
    "1.4.1": ("A", "Use of Color", "Gebruik van kleur", "partial",
              "Colour is not the only way to convey information: links in text are underlined or otherwise distinguishable; errors are not only red."),
    "1.4.2": ("A", "Audio Control", "Geluidsbediening", "partial",
              "Audio that plays automatically for more than 3 seconds can be paused or muted."),
    "1.4.3": ("AA", "Contrast (Minimum)", "Contrast (minimum)", "auto",
              "Text contrast is at least 4.5:1 (3:1 for large text: 24px, or 18.66px bold). Text on images and gradients needs a visual check (review crops)."),
    "1.4.4": ("AA", "Resize Text", "Herschalen van tekst", "partial",
              "At 200% browser zoom all text is readable and nothing is cut off or overlaps."),
    "1.4.5": ("AA", "Images of Text", "Afbeeldingen van tekst", "manual",
              "No images of text where real text could be used (banners with baked-in text, text in sliders)."),
    "1.4.10": ("AA", "Reflow", "Reflow", "auto",
               "At 320 CSS px width (400% zoom) there is no horizontal scrolling and no loss of content or functions."),
    "1.4.11": ("AA", "Non-text Contrast", "Contrast van niet-tekstuele content", "manual",
               "Input borders, focus indicators, icons and graphical controls have at least 3:1 contrast against their surroundings."),
    "1.4.12": ("AA", "Text Spacing", "Tekstafstand", "auto",
               "With increased line height, letter, word and paragraph spacing no text is clipped or overlaps."),
    "1.4.13": ("AA", "Content on Hover or Focus", "Content bij hover of focus", "manual",
               "Tooltips, mega menus and popovers that appear on hover/focus can be dismissed (Esc), can be hovered themselves and stay visible."),
    "2.1.1": ("A", "Keyboard", "Toetsenbord", "partial",
              "Everything works with the keyboard alone: menus and submenus, mobile menu toggle, sliders, tabs, accordions, forms, cookie banner, popups."),
    "2.1.2": ("A", "No Keyboard Trap", "Geen toetsenbordval", "auto",
              "Keyboard focus never gets stuck (embedded widgets, video players, chat widgets, modals)."),
    "2.1.4": ("A", "Character Key Shortcuts", "Enkel teken sneltoetsen", "manual",
              "Single-key shortcuts can be turned off or remapped, or only work when the component has focus."),
    "2.2.1": ("A", "Timing Adjustable", "Timing aanpasbaar", "manual",
              "Time limits (session timeouts, auto-advancing content, reservation timers) can be turned off, adjusted or extended."),
    "2.2.2": ("A", "Pause, Stop, Hide", "Pauzeren, stoppen, verbergen", "partial",
              "Moving, auto-playing or auto-updating content longer than 5 seconds (sliders, carousels, tickers, background video) has a pause/stop control."),
    "2.3.1": ("A", "Three Flashes or Below Threshold", "Drie flitsen of beneden drempelwaarde", "manual",
              "Nothing flashes more than three times per second."),
    "2.4.1": ("A", "Bypass Blocks", "Blokken omzeilen", "partial",
              "A working skip link to the main content, and/or proper landmarks (header, nav, main, footer)."),
    "2.4.2": ("A", "Page Titled", "Paginatitel", "auto",
              "Every page has a unique, descriptive <title>."),
    "2.4.3": ("A", "Focus Order", "Focusvolgorde", "partial",
              "Tab order follows a logical order matching the visual layout. Review the focus order map."),
    "2.4.4": ("A", "Link Purpose (In Context)", "Linkdoel (in context)", "partial",
              "Link purpose is clear from the link text (plus context). Avoid many identical \"Lees meer\" links to different pages."),
    "2.4.5": ("AA", "Multiple Ways", "Meerdere manieren", "manual",
              "Pages can be found in more than one way: menu plus search, sitemap or related links."),
    "2.4.6": ("AA", "Headings and Labels", "Koppen en labels", "partial",
              "Headings and form labels describe their topic or purpose."),
    "2.4.7": ("AA", "Focus Visible", "Focus zichtbaar", "auto",
              "Every focusable element has a clearly visible focus indicator."),
    "2.4.11": ("AA", "Focus Not Obscured (Minimum)", "Focus niet bedekt (minimum)", "auto",
               "A focused element is never completely hidden behind sticky headers, cookie banners or chat widgets."),
    "2.5.1": ("A", "Pointer Gestures", "Aanwijzergebaren", "manual",
              "Multipoint or path-based gestures (pinch, swipe) have a single-pointer alternative (buttons/arrows)."),
    "2.5.2": ("A", "Pointer Cancellation", "Aanwijzerannulering", "manual",
              "Actions fire on release (up-event), not on press, or can be aborted."),
    "2.5.3": ("A", "Label in Name", "Label in naam", "partial",
              "The accessible name contains the visible label text (an aria-label must not replace the visible words)."),
    "2.5.4": ("A", "Motion Actuation", "Bewegingsactivering", "manual",
              "Functions triggered by shaking or tilting the device have a UI alternative and can be disabled."),
    "2.5.7": ("AA", "Dragging Movements", "Sleepbewegingen", "manual",
              "Drag interactions (range sliders, sortable lists, before/after sliders, maps) have a single-pointer alternative."),
    "2.5.8": ("AA", "Target Size (Minimum)", "Grootte van het aanwijsgebied (minimum)", "auto",
              "Click targets are at least 24×24 CSS px or have enough spacing (inline links in text are exempt)."),
    "3.1.1": ("A", "Language of Page", "Taal van de pagina", "auto",
              "The <html lang> attribute matches the page language (nl for Dutch pages)."),
    "3.1.2": ("AA", "Language of Parts", "Taal van onderdelen", "manual",
              "Passages in another language are marked with lang (for example an English quote on a Dutch page)."),
    "3.2.1": ("A", "On Focus", "Bij focus", "manual",
              "Receiving focus does not trigger a change of context (no automatic popups or navigation on focus)."),
    "3.2.2": ("A", "On Input", "Bij input", "manual",
              "Changing a form control does not unexpectedly change context (a select menu that navigates on change)."),
    "3.2.3": ("AA", "Consistent Navigation", "Consistente navigatie", "partial",
              "Navigation repeated across pages appears in the same relative order."),
    "3.2.4": ("AA", "Consistent Identification", "Consistente identificatie", "manual",
              "Components with the same function are labelled consistently across pages (search, cart, contact)."),
    "3.2.6": ("A", "Consistent Help", "Consistente hulp", "manual",
              "Help mechanisms (contact details, chat, FAQ link) appear in the same relative place on every page."),
    "3.3.1": ("A", "Error Identification", "Foutidentificatie", "manual",
              "Form errors are identified in text and linked to the field (not only a red border). Test on staging, never submit live forms."),
    "3.3.2": ("A", "Labels or Instructions", "Labels of instructies", "partial",
              "Form fields have visible labels (a placeholder alone is not enough) and required fields are indicated."),
    "3.3.3": ("AA", "Error Suggestion", "Foutsuggestie", "manual",
              "Error messages suggest how to fix the input (\"Vul een geldig e-mailadres in, bijvoorbeeld naam@domein.nl\")."),
    "3.3.4": ("AA", "Error Prevention (Legal, Financial, Data)", "Foutpreventie (wettelijk, financieel, gegevens)", "manual",
              "Orders, payments and legal submissions are reversible, checked, or confirmed before final submission."),
    "3.3.7": ("A", "Redundant Entry", "Overbodige invoer", "manual",
              "Information already entered in the same process is auto-filled or selectable (for example billing = shipping address)."),
    "3.3.8": ("AA", "Accessible Authentication (Minimum)", "Toegankelijke authenticatie (minimum)", "manual",
              "Login does not require a cognitive test (allow paste and password managers; no puzzle CAPTCHA without an alternative)."),
    "4.1.2": ("A", "Name, Role, Value", "Naam, rol, waarde", "partial",
              "Custom controls (menus, toggles, tabs, accordions, sliders) expose the correct name, role and state (aria-expanded and so on). Review the ARIA snapshot."),
    "4.1.3": ("AA", "Status Messages", "Statusberichten", "manual",
              "Status messages (\"Toegevoegd aan winkelwagen\", form success, search result count) are announced without moving focus (role=status / aria-live)."),
}


def sc_from_axe_tag(tag: str) -> str | None:
    """'wcag143' -> '1.4.3', 'wcag2411' -> '2.4.11', 'wcag412' -> '4.1.2'."""
    if not tag.startswith("wcag") or not tag[4:].isdigit() or len(tag) < 7:
        return None
    digits = tag[4:]
    return f"{digits[0]}.{digits[1]}.{digits[2:]}"


def name(sc: str, lang: str = "nl") -> str:
    c = CRITERIA.get(sc)
    if not c:
        return sc
    return f"{sc} {c[2] if lang == 'nl' else c[1]} ({c[0]})"
