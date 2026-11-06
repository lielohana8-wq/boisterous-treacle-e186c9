# How this site is built

`python3 build/build.py` turns `templates/` + `content/` into the HTML files at the repo root.
Netlify runs it on every commit (see `netlify.toml`), so editing anything in `content/` — by hand
or through the admin panel at `/office-k7m3x9/` — republishes the site.

- `content/site.json` — phone, WhatsApp, email, hours, offer price, counters; footer and popup texts.
- `content/shared.json` — sections that appear on many pages (trust strip, $200 offer, prices, 19-point check...).
- `content/pages/<page>.json` — every text and photo of one page, grouped by section.
- `content/projects/<slug>.json` — one job = one case-study page at `/projects/<slug>` plus cards on the home page, Our Work and the related service pages.
- `templates/*.html` — the page markup with `{{section.key}}` slots. Never edit the root HTML files directly; the build overwrites them.
- `build/annotate.py` — the one-off migration that created the templates from the old hand-built pages. Not needed again.
- `build/gen_config.py` — generates the admin panel's field list (`office-k7m3x9/config.json`).
- `build/audit.py` — static SEO checks over the built pages.
- `netlify/functions/` — `availability` (which days/windows the booking form may offer) and `leads` (the form submissions + the owner's notes). Both keep their data in Netlify Blobs.
- `booking.js` — loaded by every page; hides blocked days/windows on the booking form.
