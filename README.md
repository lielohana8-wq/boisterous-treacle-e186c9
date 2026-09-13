# Northmark Chimney — northmark-chimney.ca

Static site. Deploy the contents of this folder as the publish directory.

## Netlify (recommended)
- Connect this repo → Build command: *(none)* → Publish directory: `/` (repo root)
- Forms: enable **Form detection**, then add an email notification for `inspection-request`.
- `_redirects` and `_headers` are picked up automatically.

## Structure
- `index.html` — homepage
- `about.html`
- `chimney-*-toronto.html` — 8 service pages
- `assets-lite/` — images
- `sitemap.xml`, `robots.txt`
