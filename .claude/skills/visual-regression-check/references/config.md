# config.yaml reference

Location: `<root>/<client>/config.yaml`, created by `vrc.py init`. Every key is optional except `base_url` and `pages`.

```yaml
name: hairsalon-pro
base_url: https://hairsalonpro.nl
widths: [375, 768, 1440]        # viewport widths in px
browsers: [chromium]            # chromium | firefox | webkit (install them first)
full_page: true                 # false = only the first viewport
max_height: 15000               # long pages are cut off at this height
threshold: 0.1                  # per-pixel colour tolerance 0..1 (higher = more lenient)
ignore_antialiasing: true       # ignore 1px shifts and anti-aliased edges
shift_compensation: true        # ignore content pushed down/up by a change above it
max_diff_ratio: 0.0005          # a shot is "changed" above 0.05% changed pixels
min_region_px: 24               # ignore specks smaller than this
max_regions: 12                 # crops generated per shot
wait_ms: 800                    # extra settle time after load and scrolling
timeout_ms: 45000
locale: nl-NL
timezone: Europe/Amsterdam
ignore_https_errors: false      # true for staging with a self-signed certificate
http_credentials_env: [STAGING_USER, STAGING_PASS]   # basic auth, read from env vars

hide:                           # display:none; adds to the built-in list
  - ".announcement-bar"
mask:                           # covered with a solid magenta box; adds to the built-in list
  - ".trustindex-widget"        # Google reviews widget
  - ".swiper"                   # sliders
  - "#latest-posts"
css: |                          # extra CSS injected before capture
  .countdown { visibility: hidden !important; }
replace_default_selectors: false  # true = ignore the built-in hide/mask lists

pages:
  - name: home
    path: /
  - name: contact
    path: /contact/
    mask: ["#map"]
  - name: shop-product
    url: https://shop.hairsalonpro.nl/product/x/   # full URL instead of path
    widths: [375, 1440]                            # override per page
```

## Built-in defaults

- **Hidden:** Complianz, CookieYes, Cookiebot, Borlabs, CookieLawInfo, Moove GDPR, Real Cookie Banner, Tidio, Crisp, HubSpot chat, the WP admin bar, the reCAPTCHA badge.
- **Masked:** `video`, `iframe` (YouTube, Maps, booking widgets).
- **Stabilised:** CSS animations and transitions are frozen, and reveal-on-scroll content (AOS, Elementor `elementor-invisible`, Divi `et_animated`, WOW) is forced visible. The page is scrolled once so lazy images load, and capture waits for web fonts.

## Choosing hide or mask

- `hide` removes the element, and the layout may reflow. Use it for overlays (banners, popups, chat bubbles).
- `mask` keeps the layout and paints over the element. Use it for content that changes inside a stable box (sliders, review widgets, dates, maps).

## Typical noise on WordPress sites, and the fix

| Noise | Fix |
|---|---|
| Hero slider (Revolution, Smart Slider, Swiper, Divi slider) | mask `.swiper, .rev_slider_wrapper, .n2-section-smartslider, .et_pb_slider` |
| Google reviews or Trustindex widget | mask `.ti-widget, .trustindex-widget` |
| "Latest posts" or random testimonials | mask the module's selector |
| Popups (Elementor Popup, OptinMonster, Bloom) | hide `.elementor-popup-modal, .om-holder, .et_bloom_popup` |
| Countdown timers, dates | mask, or use `css` to hide the element |
| Instagram feed | mask `#sb_instagram` |
