# Fixing WCAG findings on WordPress sites

Always: ask first, fix through the website AI-agent in the builder's own format (Divi, Elementor, Bricks, Gutenberg, Oxygen and so on), work on a draft duplicate for live pages, and re-run `wcag.py audit` plus `wcag.py diff` afterwards.

## Global fixes first (one change, every page)

| Finding | Global fix | Website AI-agent route |
|---|---|---|
| `axe:color-contrast` on brand colours | Darken the brand or text colour in the global palette: text 4.5:1, large text and UI parts 3:1. Propose the nearest compliant shade of the brand colour, not a new colour. | `update_elementor_global_colors`, `update_bricks_color_palette`, `upsert_divi_presets`, `update_design_token` / theme.json |
| `kbd:focus-not-visible` | One site-wide style: `:focus-visible{outline:3px solid #XXXXXX;outline-offset:2px}`. Remove theme rules like `*:focus{outline:none}`. The outline colour needs 3:1 against the backgrounds. | Customizer > Additional CSS, the builder's custom CSS, or a design token |
| `kbd:no-skip-link` / `kbd:skip-link-broken` | Enable the theme's skip link (Astra, GeneratePress, Kadence, Blocksy and block themes have one), or add `<a class="skip-link" href="#main">Naar de inhoud</a>` as the first element with a visible-on-focus style; make sure `<main id="main">` exists | theme or header template |
| `struct:no-main` | Wrap the content in `<main id="main">` in the page or theme template (Divi: Theme Builder body layout; Elementor: Site Settings > Layout > Content wrapper HTML tag = main) | theme builder template |
| `kbd:focus-on-hidden` (mobile menu, off-canvas) | A closed menu must be `display:none` / `visibility:hidden`, or use the `inert` attribute; do not just move it off-screen. In Elementor use the Nav Menu widget toggle, not custom off-canvas HTML. | header template |
| `kbd:focus-obscured` (sticky header) | `html{scroll-padding-top:<header height + 10px>}`; keep the cookie bar from covering content, or let it close easily | custom CSS |
| `axe:html-has-lang` / `struct:lang-invalid` | Settings > General > Site language = Nederlands; for WPML or Polylang, check each language | `update_option` (WPLANG) |
| `axe:target-size` | Icon buttons, social icons, slider dots and menu toggles at least 24×24 (44×44 is better): add padding, not a bigger icon | global button or icon styles |
| `motion:auto-moving` | Turn off slider autoplay (best for usability and conversion), or enable the slider's pause-on-hover plus a visible pause button. Background video: add a pause button or stop it after 5s. | slider module settings |
| Cookie banner findings | Complianz, CookieYes and Cookiebot have accessibility settings (colours, focus, the banner position); the "accept" and "reject" buttons need equal visibility and keyboard access | plugin settings |

## Content fixes

| Finding | Fix |
|---|---|
| `axe:image-alt`, `img:suspicious-alt` | Write the alt in the media library (`update_media_batch` for bulk). Informative image: describe its purpose in 5 to 15 words. Linked image: describe the destination. Decorative image: alt="" (empty, not missing). Logo: "<Bedrijfsnaam>" (plus "– naar home" if it links to home). Never "afbeelding van". |
| `axe:link-name`, `axe:button-name` | Icon-only links and buttons (social icons, hamburger, search, cart) need an accessible name: builder field "aria-label" or screen-reader text. |
| `struct:ambiguous-links` | Make the visible text specific ("Lees meer over balayage"). If the design forces "Lees meer", add visually hidden text; an aria-label must *start with* the visible text (2.5.3 Label in naam). |
| `struct:heading-skip`, `struct:no-h1` | Change the heading **level** (H2/H3 tag setting) in the builder and keep the look through typography settings. Exactly one h1 per page. |
| `axe:empty-heading` | Remove the empty heading module or use a text module for spacing. |
| `form:placeholder-as-label`, `axe:label` | Form plugin settings: Contact Form 7 (wrap `[text]` in `<label>`), Gravity Forms ("Field label visibility: visible"), WPForms, Fluent Forms, Elementor Form ("Show labels" on). Mark required fields in text, not only with a colour. |
| `form:autocomplete-missing` | Gravity Forms: Enable autocomplete per field. Elementor Form: Advanced > autocomplete attribute. CF7: `autocomplete:email` option. Tokens: name, given-name, family-name, email, tel, organization, street-address, postal-code, address-level2, country-name. |
| `axe:link-in-text-block` | Underline links in body text (do not rely on colour alone). |
| `media:*` | Upload proper captions to YouTube or Vimeo (not only auto-generated ones), offer a transcript, and never autoplay sound. |
| `spacing:text-clipped` | Replace fixed heights with min-height and padding on buttons, cards and menu items; remove `overflow:hidden` from text containers. |
| `reflow:horizontal-scroll` | Look at the offenders list: fixed px widths, wide tables (wrap them in `overflow-x:auto`), long URLs (`overflow-wrap:anywhere`), iframes or embeds (`max-width:100%`), full-width rows with negative margins. |
| `axe:aria-*`, `axe:nested-interactive` | Usually a theme or plugin bug: update the plugin or theme, configure the widget differently, or report it to the vendor. Avoid custom ARIA unless you know the pattern (use the WAI-ARIA Authoring Practices). |

## Builder notes

- **Divi:** the Accessibility toggle in Theme Options; the Divi Accessibility plugin (Campaign Edge) fixes the skip link, focus and the mobile menu ARIA; check its options instead of adding custom code. Toggle and accordion modules need the plugin for proper ARIA.
- **Elementor:** Site Settings > Accessibility (Elementor 3.x+); for the Nav Menu widget, enable "Toggle button" ARIA; use the "Image Box" alt from the media library; the HTML tag setting for headings.
- **Gutenberg and block themes:** core blocks are mostly accessible; check the custom colours in theme.json and the Navigation block's overlay menu.
- **Bricks:** element "HTML tag" and "Attributes" controls for aria-label; Bricks has built-in skip link settings.

## Don'ts
- No accessibility overlays or widgets (accessiBe, UserWay, EqualWeb, AudioEye's toolbar): they do not fix the source, they often conflict with screen readers, and they are not accepted as compliance.
- Do not hide content from everyone with `aria-hidden` to silence an error.
- Do not set `tabindex` greater than 0.
- Do not change the visual design beyond what the fix needs without asking. Propose brand-safe colour shades and show a before/after.
