#!/usr/bin/env python3
"""Builds the site: templates/ + content/ -> the HTML files at the repo root.

Runs on Netlify on every commit (see netlify.toml) and locally with: python3 build/build.py
Standard library only, Python 3.8+.

  content/site.json          business facts ({{site.*}} tokens) + footer/popup texts ("chrome")
  content/shared.json        sections that appear on many pages (trust strip, $200 offer, prices...)
  content/pages/<page>.json  every text and photo of that page, keyed by section
  content/projects/*.json    one file per job; becomes /projects/<slug> + cards across the site
  content/services.json      the service cards used on project pages
"""
import datetime, glob, html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE_URL = "https://northmark-chimney.ca"
ADMIN_DIR = "office-k7m3x9"
TODAY = datetime.date.today().isoformat()


def load(path):
    with open(path, encoding="utf-8") as f: return json.load(f)


def esc_text(v):
    return html.escape(str(v), quote=False)


def esc_html(v):
    """Values that contain markup: keep the tags, escape bare ampersands only."""
    return re.sub(r"&(?![a-zA-Z][a-zA-Z0-9]*;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", str(v))


def value(v):
    if v is None: return ""
    v = str(v)
    return esc_html(v) if re.search(r"<[a-zA-Z/]", v) else esc_text(v)


def get(d, dotted):
    for p in dotted.split("."):
        if not isinstance(d, dict) or p not in d: return None
        d = d[p]
    return d


site = load("content/site.json")
shared = load("content/shared.json")
services = load("content/services.json")
ICONS = {"house": '<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/>', "drop": '<path d="M12 2.7C8 7.5 5 10.3 5 14a7 7 0 0 0 14 0c0-3.7-3-6.5-7-11.3z"/>',
         "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
         "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>', "check": '<path d="M20 6 9 17l-5-5"/>'}


def _slug(f, d):
    s = re.sub(r"[^a-z0-9-]", "", str(d.get("url_slug") or "").lower().strip())
    return s or os.path.basename(f)[:-5]


projects = sorted([dict(load(f), slug=_slug(f, load(f))) for f in glob.glob("content/projects/*.json")],
                  key=lambda p: (p.get("order", 999), p["slug"]))
projects = [p for p in projects if p.get("published", True)]
guides = sorted([dict(load(f), slug=_slug(f, load(f))) for f in glob.glob("content/guides/*.json")], key=lambda g: (g.get("order", 999), g["slug"]))
guides = [g for g in guides if g.get("published", True)]

PHONE_SVG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 '
             '19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 '
             '1.8.7 2.6a2 2 0 0 1-.5 2.1L8 9.7a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.8.3 1.7.5 2.6.7a2 2 0 0 1 1.7 2z"/></svg>')
TICK = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')
TICK_SM = TICK.replace('width="20" height="20"', 'width="16" height="16"')


# ----------------------------------------------------------------------------- slots
def fill_slots(tpl, page_values):
    """Replace {{key}} slots and data-cms-img photos. Lookup order: page -> shared -> site.chrome."""
    def lookup(key):
        if key.startswith("shared."): return get(shared, key[7:])
        if key.startswith("chrome."): return get(site["chrome"], key[7:]) if get(site["chrome"], key[7:]) is not None else get(page_values, key)
        return get(page_values, key)

    def slot(m):
        key = m.group(1)
        if key.startswith("site."): return m.group(0)  # tokens are done later
        if key.startswith(("cards:", "project_link", "guide_links")): return m.group(0)
        v = lookup(key)
        if v is None:
            print("  missing slot", key); return ""
        return value(v)
    tpl = re.sub(r"\{\{([a-zA-Z0-9_.:-]+)\}\}", slot, tpl)

    def img(m):
        tag = m.group(0); key = m.group(1); orig = m.group(2)
        v = lookup(key)
        if not isinstance(v, dict): return tag
        src = v.get("src") or orig; alt = v.get("alt", "")
        tag = re.sub(r' src="[^"]*"', ' src="%s"' % html.escape(src, quote=True), tag, count=1)
        if re.search(r' alt="[^"]*"', tag): tag = re.sub(r' alt="[^"]*"', ' alt="%s"' % html.escape(alt, quote=True), tag, count=1)
        else: tag = tag.replace("<img", '<img alt="%s"' % html.escape(alt, quote=True), 1)
        if src != orig:  # a new photo: the responsive variants of the old one no longer apply
            tag = re.sub(r' srcset="[^"]*"', "", tag); tag = re.sub(r' sizes="[^"]*"', "", tag)
        return tag
    tpl = re.sub(r'<img data-cms-img="([^"]+)" data-orig="([^"]*)"[^>]*>', img, tpl)
    return tpl


def fill_tokens(s):
    def tok(m):
        v = site.get(m.group(1))
        if v is None: print("  missing site token", m.group(1)); return ""
        return esc_text(v) if m.group(1) != "google_profile" else v
    return re.sub(r"\{\{site\.([a-zA-Z0-9_]+)\}\}", tok, s)


# ----------------------------------------------------------------------------- project cards
def cs_card(q, feat=False):
    return ('<a class="cs%s" href="/projects/%s"><img src="%s" alt="%s" width="1200" height="900" loading="lazy" decoding="async">'
            '<div class="cs-b"><span class="cs-k">%s</span><h3>%s</h3><p>%s</p><span class="go">Read the case study</span></div></a>'
            % (" feat" if feat else "", q["slug"], html.escape(q["card"]["src"], True), html.escape(q["card"].get("alt", ""), True),
               value(q.get("tag", "")), value(q.get("card_title", q["h1"])), value(q.get("card_text", ""))))


def cards_block(kind, page):
    if not projects: return ""
    if kind == "home":
        ps = projects[:3]
        return ('<div class="head" style="margin-top:56px" data-cs="home"><div><h3 style="font-size:clamp(22px,2.4vw,28px)">Three Jobs, Start To Finish</h3></div>'
                '<p class="lead">What we found, what we did and the finished photo — written up the way we explain work to the homeowner.</p></div>'
                '<div class="cs-grid">' + "".join(cs_card(q) for q in ps) + '</div>')
    if kind == "ourwork":
        return ('<section class="sec" id="cases" aria-labelledby="cs-h"><div class="wrap"><div class="head"><div><h2 id="cs-h">Project Case Studies</h2></div>'
                '<p class="lead">Recent jobs written up start to finish: what we found, what we did, and the photo of the finished chimney.</p></div>'
                '<div class="cs-grid hub">' + cs_card(projects[0], True) + "".join(cs_card(q) for q in projects[1:]) + '</div>'
                '<div class="more-row"><p>Every case study ends with the same offer: a free inspection with photos and the price in writing.</p><a class="btn line" href="/projects/">All case studies</a></div></div></section>')
    if kind == "svc":
        key = next((k for k, s in services.items() if s["url"] == "/" + page[:-5]), None)
        ps = [q for q in projects if q.get("service") == key or key in q.get("related", [])][:2]
        if not ps: return ""
        n = len(ps)
        return ('<div class="head" style="margin-top:56px" data-cs="svc"><div><h3 style="font-size:clamp(22px,2.4vw,28px);color:#fff">Case ' + ("Study" if n == 1 else "Studies") + ': This Work, Start To Finish</h3></div>'
                '<p class="lead">What we found, what we did, and the finished photo.</p></div>'
                '<div class="cs-grid' + (" hub" if n == 1 else " two") + '">' + "".join(cs_card(q, feat=(n == 1)) for q in ps) + '</div>')
    return ""


def project_link(page):
    if not projects: return ""
    gta = page.endswith(("markham.html", "mississauga.html", "richmond-hill.html", "vaughan.html"))
    pool = [q for q in projects if ("GTA" in q.get("where", "")) == gta] or projects
    q = pool[0]
    return '<p class="ask" data-cs="area">Want to see a whole job, start to finish? Read the case study: <a href="/projects/%s">%s</a>.</p>' % (q["slug"], value(q.get("card_title", q["h1"])))


# ----------------------------------------------------------------------------- project pages
EXTRA_CSS = open("build/project.css", encoding="utf-8").read()


def between(s, a, b, inclusive=False):
    i = s.index(a); j = s.index(b, i + len(a))
    return s[i:j + len(b)] if inclusive else s[i + len(a):j]


def project_pages(ourwork_html):
    src = ourwork_html
    GTM = between(src, "<!-- Google Tag Manager -->", "<!-- End Google Tag Manager -->", True)
    CSS = between(src, "<style>", "</style>").split("/* project case studies */")[0]
    FONTS = between(src, '<link rel="icon"', "<style>")
    FONTS = '<link rel="icon"' + FONTS
    TAIL = src[src.index('<script src="/seo-hook.js"'):src.index("</head>")]
    HEADER = between(src, "<body>", '<main id="main">').replace(' aria-current="page"', "")
    FOOTER = src[src.index("</main>") + len("</main>"):]
    FORM = between(src, '<form class="form two-step"', "</form>", True)
    TRUST = between(src, '<section class="trust"', "</section>", True)
    PH = site["phone"]; TEL = "tel:" + site["phone_tel"]

    def head(p, url, title, desc, og, kind="article"):
        return ('<!DOCTYPE html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                + GTM + '<title>%s</title><meta name="description" content="%s">' % (esc_text(title), html.escape(desc, True))
                + '<link rel="canonical" href="%s"><meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">' % url
                + '<meta name="theme-color" content="#F5F2EC"><meta property="og:site_name" content="Northmark Chimney"><meta property="og:locale" content="en_CA">'
                + '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:type" content="%s">' % (html.escape(title, True), html.escape(desc, True), kind)
                + '<meta property="og:url" content="%s"><meta property="og:image" content="%s"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' % (url, SITE_URL + og)
                + '<meta name="twitter:card" content="summary_large_image">' + FONTS + "<style>" + CSS + EXTRA_CSS + "</style>"
                + '<script type="application/ld+json">%s</script>' % json.dumps(schema(p, url, title, desc), ensure_ascii=False) + TAIL + "</head><body>")

    def schema(p, url, title, desc):
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Our Work", "item": SITE_URL + "/our-work"},
            {"@type": "ListItem", "position": 3, "name": "Projects", "item": SITE_URL + "/projects/"}]}
        if p is None:
            return [crumbs, {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": url, "description": desc,
                             "isPartOf": {"@id": SITE_URL + "/#website"}, "about": {"@id": SITE_URL + "/#business"},
                             "hasPart": [{"@type": "Article", "headline": q["h1"], "url": SITE_URL + "/projects/" + q["slug"], "image": SITE_URL + q["hero"]["src"]} for q in projects]}]
        crumbs["itemListElement"].append({"@type": "ListItem", "position": 4, "name": p.get("crumb", p["h1"]), "item": url})
        svc = services.get(p.get("service"), {})
        art = {"@context": "https://schema.org", "@type": "Article", "@id": url + "#article", "headline": p["h1"], "description": desc, "url": url,
               "mainEntityOfPage": url, "datePublished": p.get("date", TODAY), "dateModified": p.get("date", TODAY), "inLanguage": "en-CA",
               "image": [{"@type": "ImageObject", "contentUrl": SITE_URL + f["src"], "caption": f.get("alt", "")} for f in [p["hero"]] + p.get("figs", [])],
               "author": {"@type": "Organization", "name": "Northmark Chimney", "@id": SITE_URL + "/#business"},
               "publisher": {"@type": "Organization", "name": "Northmark Chimney", "@id": SITE_URL + "/#business", "logo": {"@type": "ImageObject", "url": SITE_URL + "/logo.png"}},
               "about": {"@type": "Service", "name": svc.get("name", ""), "url": SITE_URL + svc.get("url", "/"), "provider": {"@id": SITE_URL + "/#business"},
                         "areaServed": {"@type": "City", "name": "Toronto", "containedInPlace": {"@type": "AdministrativeArea", "name": "Ontario"}}},
               "locationCreated": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": re.sub(r"\s*&.*", "", p.get("where", "Toronto")), "addressRegion": "ON", "addressCountry": "CA"}}}
        out = [crumbs, art]
        if p.get("faq"):
            out.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": html.unescape(q["q"]), "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", html.unescape(q["a"]))}} for q in p["faq"]]})
        return out

    def acts():
        return '<div class="acts"><a class="btn lg" href="#book">Book my free inspection</a><a class="btn line lg" href="%s">%sCall %s</a></div>' % (TEL, PHONE_SVG, PH)

    def hero(p):
        specs = "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (value(s["label"]), value(s["value"])) for s in p.get("specs", []))
        h = p["hero"]["src"]; base = h[:-4] if h.endswith(".jpg") else None
        srcset = ' srcset="%s-480.jpg 480w, %s-800.jpg 800w, %s 1200w" sizes="(max-width:1000px) 92vw, 46vw"' % (base, base, h) if base and os.path.exists(base.lstrip("/") + "-800.jpg") else ""
        return ('<main id="main"><section class="hero"><div class="wrap"><div class="hcopy">'
                '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/our-work">Our Work</a> / <a href="/projects/">Projects</a> / <span aria-current="page">%s</span></nav>'
                '<span class="tag">%s</span><h1>%s</h1><p class="lead">%s</p>%s<dl class="specs" aria-label="Job summary">%s</dl></div>'
                '<figure class="shot tall"><img src="%s"%s alt="%s" width="1200" height="1600" fetchpriority="high" decoding="async">'
                '<figcaption><b>Photo from the job.</b> %s</figcaption></figure></div></section>'
                % (value(p.get("crumb", p["h1"])), value(p.get("tag", "")), value(p["h1"]), value(p.get("lead", "")), acts(), specs,
                   html.escape(h, True), srcset, html.escape(p["hero"].get("alt", ""), True), value(p.get("hero_caption", ""))))

    def fig(f):
        s = f["src"]; base = s[:-4] if s.endswith(".jpg") else None
        srcset = ' srcset="%s-800.jpg 800w, %s 1200w" sizes="(max-width:1000px) 46vw, 40vw"' % (base, s) if base and os.path.exists(base.lstrip("/") + "-800.jpg") else ""
        return ('<figure><img src="%s"%s alt="%s" width="1200" height="900" loading="lazy" decoding="async"><figcaption><b>%s</b> %s</figcaption></figure>'
                % (html.escape(s, True), srcset, html.escape(f.get("alt", ""), True), value(f.get("label", "")), value(f.get("caption", ""))))

    def story(p):
        steps = "".join('<li><div><b>%s</b><p>%s</p></div></li>' % (value(s["title"]), value(s["text"])) for s in p.get("steps", []))
        notice = ('<div class="notice"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                  '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/></svg><p>%s</p></div>' % value(p["notice"])) if p.get("notice") else ""
        return ('<section class="sec" aria-labelledby="job-h"><div class="wrap"><div class="head"><div><h2 id="job-h">%s</h2></div><p class="lead">%s</p></div>'
                '<div class="story"><div><div class="prose"><h3>%s</h3>%s<h3>What we did</h3></div><ol class="jobsteps">%s</ol>%s</div><div class="figs">%s</div></div></div></section>'
                % (value(p.get("job_heading", "The Job: What We Found, What We Did")), value(p.get("job_lead", "")), value(p.get("found_heading", "What we found")),
                   "".join("<p>%s</p>" % value(x["text"]) for x in p.get("found", [])), steps, notice, "".join(fig(f) for f in p.get("figs", []))))

    def pillars(p):
        if not p.get("pillars"): return ""
        cards = "".join('<div class="pillar"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg><h3>%s</h3><p>%s</p></div>'
                        % (ICONS.get(c.get("icon", "house"), ICONS["house"]), value(c["title"]), value(c["text"])) for c in p["pillars"])
        return ('<section class="sec stone" aria-labelledby="why-h"><div class="wrap"><div class="head"><div><h2 id="why-h">%s</h2></div><p class="lead">%s</p></div><div class="pillars">%s</div></div></section>'
                % (value(p.get("why_heading", "")), value(p.get("why_lead", "")), cards))

    def related(p):
        cards = ""
        for key in p.get("related", []):
            s = services.get(key)
            if not s: continue
            cards += ('<a class="svc" href="%s"><div class="svc-img"><img src="%s" alt="%s" width="1200" height="900" loading="lazy" decoding="async"></div>'
                      '<div class="svc-b"><h3>%s</h3><p class="svc-pr"><b>Fixes</b>%s</p><p class="svc-bn">%s</p><span class="go">Learn More</span></div></a>'
                      % (s["url"], html.escape(s["image"], True), html.escape(s["alt"], True), value(s["name"]), value(s["fixes"]), value(s["benefit"])))
        others = [q for q in projects if q["slug"] != p["slug"]]
        more = ""
        if others:
            more = ('<section class="sec navy" aria-labelledby="more-h"><div class="wrap"><div class="head"><div><h2 id="more-h">More Northmark Projects</h2></div><p class="lead">Other recent jobs, photographed by us.</p></div>'
                    '<div class="cs-grid%s">%s</div><div class="more-row"><p>Before-and-after photos and recent jobs by area.</p><a class="btn line-w" href="/our-work">See all our work</a></div></div></section>'
                    % (" two" if len(others) == 2 else "", "".join(cs_card(q) for q in others[:3])))
        rel = ('<section class="sec" aria-labelledby="rel-h"><div class="wrap"><div class="head"><div><h2 id="rel-h">The Services Behind This Job</h2></div><p class="lead">What we did here is what we do every week across Toronto and the GTA. Read about the service, or book the free inspection and we will tell you what your chimney needs.</p></div>'
               '<div class="svcs">%s</div></div></section>' % cards) if cards else ""
        return rel + more

    def faq(p):
        if not p.get("faq"): return ""
        items = "".join('<details class="faq"><summary>%s</summary><p>%s</p></details>' % (value(q["q"]), value(q["a"])) for q in p["faq"])
        return ('<section class="sec stone" id="faq" aria-labelledby="faq-h"><div class="wrap"><div class="faqwrap"><div><h2 id="faq-h">%s</h2>'
                '<p class="lead" style="margin-top:14px">Straight answers. If yours is not here, call %s — every day %s.</p></div><div class="faqs">%s</div></div></div></section>'
                % (value(p.get("faq_heading", "Questions")), PH, site["hours"], items))

    def cta(h2, lead):
        checks = "".join("<li>%s%s</li>" % (TICK, c) for c in ["No obligation", "Photos included", "Price before any work starts"])
        return ('<section class="cta" id="book" aria-labelledby="book-h"><div class="wrap"><div><h2 id="book-h">%s</h2><p class="lead">%s</p>'
                '<ul class="checks">%s</ul><a class="big" href="%s">%s%s</a><p class="sub">Every Day %s. If we miss your call, we call right back.</p></div>%s</div></section></main>'
                % (value(h2), value(lead), checks, TEL, PHONE_SVG, PH, site["hours"], FORM))

    out = {}
    for p in projects:
        url = SITE_URL + "/projects/" + p["slug"]
        body = hero(p) + TRUST + story(p) + pillars(p) + related(p) + faq(p) + cta(p.get("cta_heading", "Want This For Your Chimney?"), p.get("cta_lead", "Book the free inspection. We photograph what we find and give you the price in writing before any work starts."))
        out[p["slug"] + ".html"] = head(p, url, p["title"], p["description"], p.get("og") or p["hero"]["src"]) + HEADER + body + FOOTER
    # hub
    hub = site.get("projects_hub", {})
    title = hub.get("title", "Chimney Projects In Toronto & The GTA | Northmark Chimney")
    desc = hub.get("description", "Real Northmark chimney jobs, start to finish, with our own photos.")
    first = next((q for q in projects if q["slug"] == hub.get("hero_project")), projects[0] if projects else None)
    cards = (cs_card(projects[0], True) + "".join(cs_card(q) for q in projects[1:])) if projects else "<p>No projects published yet.</p>"
    heroimg = first["hero"]["src"] if first else "/og-image.jpg"
    body = ('<main id="main"><section class="hero"><div class="wrap"><div class="hcopy">'
            '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/our-work">Our Work</a> / <span aria-current="page">Projects</span></nav>'
            '<span class="tag">Project case studies</span><h1>%s</h1><p class="lead">%s</p>%s'
            '<ul class="hpoints"><li>%s<span><b>Our own photos</b> — taken on the job, not bought from a library</span></li>'
            '<li>%s<span><b>What was wrong, what we did, what it fixed</b> — in plain language</span></li>'
            '<li>%s<span><b>The same process</b> you get: free inspection, photos, price in writing first</span></li></ul></div>'
            '<figure class="shot tall"><img src="%s" alt="%s" width="1200" height="1600" fetchpriority="high" decoding="async"><figcaption><b>Photo from the job.</b> %s</figcaption></figure></div></section>%s'
            '<section class="sec" aria-labelledby="list-h"><div class="wrap"><div class="head"><div><h2 id="list-h">Recent Jobs, Start To Finish</h2></div><p class="lead">Each case study walks through one chimney: what we found, the steps we took, and the photo of the finished work.</p></div>'
            '<div class="cs-grid hub">%s</div><div class="more-row"><p>Looking for before-and-after pairs and jobs by neighbourhood?</p><a class="btn line" href="/our-work">See all our work</a></div></div></section>'
            '<section class="sec stone" aria-labelledby="how-h"><div class="wrap"><div class="head"><div><h2 id="how-h">How Every Northmark Job Runs</h2></div><p class="lead">The projects above all followed the same four steps. Yours would too.</p></div>'
            '<div class="steps"><div class="step"><span class="n">Step 1</span><h3>Free inspection</h3><p>A technician comes to your home, looks at the chimney top to bottom and photographs what he finds.</p></div>'
            '<div class="step"><span class="n">Step 2</span><h3>Price in writing</h3><p>You get the photos and the exact price before anything starts. No work without your go-ahead.</p></div>'
            '<div class="step"><span class="n">Step 3</span><h3>The work</h3><p>Materials matched to your home, floors and roof protected, the area left the way we found it.</p></div>'
            '<div class="step"><span class="n">Step 4</span><h3>Photos of the result</h3><p>You see the finished work the same way we do — in photos, including the parts of the chimney you cannot see from the ground.</p></div></div></div></section>'
            % (value(hub.get("h1", "Chimney Projects: Real Jobs In Toronto & The GTA, Start To Finish")),
               value(hub.get("lead", "Recent Northmark jobs, each written up the way we explain work to the homeowner: what we found, what we did, and the photo of the finished chimney. No stock images — every photo here was taken on the job.")),
               acts(), TICK_SM, TICK_SM, TICK_SM, html.escape(heroimg, True), html.escape(first["hero"].get("alt", "") if first else "", True),
               value(first.get("hero_caption", "") if first else ""), TRUST, cards))
    body += cta("Want This For Your Chimney?", "Book the free inspection. We photograph what we find and give you the price in writing before any work starts.")
    out["projects.html"] = head(None, SITE_URL + "/projects/", title, desc, (first.get("og") or first["hero"]["src"]) if first else "/og-image.jpg", "website") + HEADER + body + FOOTER
    return out


# ----------------------------------------------------------------------------- guides
GUIDE_CSS = """
/* guides */
.guide{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:56px;align-items:start}
.guide .prose{max-width:72ch}
.guide .prose h2{font-size:clamp(24px,2.4vw,30px);line-height:1.15;margin:40px 0 14px;letter-spacing:-.02em}
.guide .prose h2:first-child{margin-top:0}
.guide .prose p{font-size:17.5px;line-height:1.7;color:var(--ink-2);margin:0 0 16px}
.guide .prose p b{color:var(--ink)}
.guide .prose ul{margin:0 0 18px;padding-inline-start:22px;display:grid;gap:10px}
.guide .prose li{font-size:17px;line-height:1.6;color:var(--ink-2)}
.guide .prose li b{color:var(--ink)}
.guide .prose a{color:var(--copper-2);font-weight:600;text-decoration:underline;text-underline-offset:3px;text-decoration-color:rgba(169,63,19,.35)}
.gaside{position:sticky;top:98px;display:grid;gap:18px}
.gcard{background:var(--card);border:1px solid var(--rule);border-radius:var(--r-card);padding:22px;box-shadow:var(--shadow)}
.gcard h3{font-size:19px;margin:0 0 6px}
.gcard p{color:var(--ink-2);font-size:15px;line-height:1.5;margin:0 0 14px}
.gcard .btn{width:100%}
.gcard ul{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.gcard li a{color:var(--ink);text-decoration:none;font-weight:600;font-size:15px;line-height:1.4;display:block;padding:10px 12px;border:1px solid var(--rule-2);border-radius:10px;background:var(--field)}
.gcard li a:hover{border-color:var(--copper)}
.gcard .ph{display:block;text-align:center;margin-top:10px;color:var(--ink);font-weight:700;text-decoration:none;font-size:17px}
.gread{margin-top:34px;padding-top:22px;border-top:1px solid var(--rule);display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;font-size:15px;color:var(--mut)}
.gread a{color:var(--copper-2);font-weight:600;text-decoration:underline;text-underline-offset:3px;text-decoration-color:rgba(169,63,19,.35)}
.sec.stone .gread{border-top-color:var(--rule)}
.gcards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
@media(max-width:1000px){.guide{grid-template-columns:1fr}.gaside{position:static}.gcards{grid-template-columns:1fr 1fr}}
@media(max-width:720px){.gcards{grid-template-columns:1fr}}
"""


def guide_links(page):
    """'Read the guide' row for a service page or the home page."""
    if not guides: return ""
    key = next((k for k, s in services.items() if s["url"] == "/" + page[:-5]), None)
    gs = guides if page == "index.html" else [g for g in guides if g.get("service") == key or key in g.get("related", [])]
    if not gs: return ""
    links = " · ".join('<a href="/guides/%s">%s</a>' % (g["slug"], value(g.get("short_title") or re.sub(r"[:—].*$", "", g["h1"]))) for g in gs[:3])
    return '<div class="wrap"><div class="gread"><span>Read the guide:</span> %s</div></div>' % links


def guide_pages(src):
    GTM = between(src, "<!-- Google Tag Manager -->", "<!-- End Google Tag Manager -->", True)
    CSS = between(src, "<style>", "</style>").split("/* project case studies */")[0]
    FONTS = '<link rel="icon"' + between(src, '<link rel="icon"', "<style>")
    TAIL = src[src.index('<script src="/seo-hook.js"'):src.index("</head>")]
    HEADER = between(src, "<body>", '<main id="main">').replace(' aria-current="page"', "")
    FOOTER = src[src.index("</main>") + len("</main>"):]
    FORM = between(src, '<form class="form two-step"', "</form>", True)
    TRUST = between(src, '<section class="trust"', "</section>", True)
    PH = site["phone"]; TEL = "tel:" + site["phone_tel"]

    def head(g, url, title, desc, og, kind="article"):
        return ('<!DOCTYPE html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                + GTM + '<title>%s</title><meta name="description" content="%s">' % (esc_text(title), html.escape(desc, True))
                + '<link rel="canonical" href="%s"><meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">' % url
                + '<meta name="theme-color" content="#F5F2EC"><meta property="og:site_name" content="Northmark Chimney"><meta property="og:locale" content="en_CA">'
                + '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:type" content="%s">' % (html.escape(title, True), html.escape(desc, True), kind)
                + '<meta property="og:url" content="%s"><meta property="og:image" content="%s">' % (url, SITE_URL + og)
                + '<meta name="twitter:card" content="summary_large_image">' + FONTS + "<style>" + CSS + EXTRA_CSS + GUIDE_CSS + "</style>"
                + '<script type="application/ld+json">%s</script>' % json.dumps(schema(g, url, title, desc), ensure_ascii=False) + TAIL + "</head><body>")

    def schema(g, url, title, desc):
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE_URL + "/guides/"}]}
        if g is None:
            return [crumbs, {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": url, "description": desc, "isPartOf": {"@id": SITE_URL + "/#website"},
                             "hasPart": [{"@type": "Article", "headline": x["h1"], "url": SITE_URL + "/guides/" + x["slug"]} for x in guides]}]
        crumbs["itemListElement"].append({"@type": "ListItem", "position": 3, "name": re.sub(r"[:—].*$", "", g["h1"]).strip(), "item": url})
        art = {"@context": "https://schema.org", "@type": "Article", "@id": url + "#article", "headline": g["h1"], "description": desc, "url": url, "mainEntityOfPage": url,
               "datePublished": g.get("date", TODAY), "dateModified": g.get("date", TODAY), "inLanguage": "en-CA", "image": SITE_URL + g["hero"]["src"],
               "author": {"@type": "Organization", "name": "Northmark Chimney", "@id": SITE_URL + "/#business"},
               "publisher": {"@type": "Organization", "name": "Northmark Chimney", "@id": SITE_URL + "/#business", "logo": {"@type": "ImageObject", "url": SITE_URL + "/logo.png"}},
               "about": {"@type": "Service", "name": services.get(g.get("service"), {}).get("name", ""), "url": SITE_URL + services.get(g.get("service"), {}).get("url", "/")}}
        out = [crumbs, art]
        if g.get("faq"):
            out.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": html.unescape(q["q"]), "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", html.unescape(fill_tokens(q["a"])))}} for q in g["faq"]]})
        return out

    def acts():
        return '<div class="acts"><a class="btn lg" href="#book">Book my free inspection</a><a class="btn line lg" href="%s">%sCall %s</a></div>' % (TEL, PHONE_SVG, PH)

    def hero(g):
        h = g["hero"]["src"]
        return ('<main id="main"><section class="hero"><div class="wrap"><div class="hcopy">'
                '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / <span aria-current="page">%s</span></nav>'
                '<span class="tag">%s</span><h1>%s</h1><p class="lead">%s</p>%s</div>'
                '<figure class="shot land"><img src="%s" alt="%s" width="1200" height="800" fetchpriority="high" decoding="async"><figcaption>%s</figcaption></figure></div></section>'
                % (value(re.sub(r"[:—].*$", "", g["h1"]).strip()), value(g.get("tag", "Guide")), value(g["h1"]), value(g.get("lead", "")), acts(),
                   html.escape(h, True), html.escape(g["hero"].get("alt", ""), True), value(g.get("hero_caption", ""))))

    def body(g):
        secs = "".join("<h2>%s</h2>%s" % (value(s["h2"]), esc_html(s["body"])) for s in g.get("sections", []))
        others = [x for x in guides if x["slug"] != g["slug"]]
        more = "".join('<li><a href="/guides/%s">%s</a></li>' % (x["slug"], value(re.sub(r"[:—].*$", "", x["h1"]).strip())) for x in others[:4])
        rel = "".join('<li><a href="%s">%s</a></li>' % (services[k]["url"], value(services[k]["name"])) for k in g.get("related", []) if k in services)
        aside = ('<div class="gaside"><div class="gcard"><h3>Free inspection, photos included</h3><p>A WETT-certified technician checks 19 points, photographs what he finds and gives you the price in writing before anything starts.</p>'
                 '<a class="btn" href="#book">Book my free inspection</a><a class="ph" href="%s">%s</a></div>' % (TEL, PH))
        if more: aside += '<div class="gcard"><h3>More guides</h3><ul>%s</ul></div>' % more
        if rel: aside += '<div class="gcard"><h3>Related services</h3><ul>%s</ul></div>' % rel
        proj = next((q for q in projects if q.get("service") == g.get("service") or g.get("service") in q.get("related", [])), None)
        if proj:
            aside += ('<a class="cs" href="/projects/%s"><img src="%s" alt="%s" width="1200" height="900" loading="lazy" decoding="async"><div class="cs-b"><span class="cs-k">From our work</span><h3>%s</h3><span class="go">Read the case study</span></div></a>'
                      % (proj["slug"], html.escape(proj["card"]["src"], True), html.escape(proj["card"].get("alt", ""), True), value(proj.get("card_title", proj["h1"]))))
        aside += "</div>"
        return '<section class="sec" aria-label="Guide"><div class="wrap"><div class="guide"><article class="prose">%s</article>%s</div></div></section>' % (secs, aside)

    def faq(g):
        if not g.get("faq"): return ""
        items = "".join('<details class="faq"><summary>%s</summary><p>%s</p></details>' % (value(q["q"]), value(q["a"])) for q in g["faq"])
        return ('<section class="sec stone" id="faq" aria-labelledby="faq-h"><div class="wrap"><div class="faqwrap"><div><h2 id="faq-h">%s</h2>'
                '<p class="lead" style="margin-top:14px">Straight answers. If yours is not here, call %s — every day %s.</p></div><div class="faqs">%s</div></div></div></section>'
                % (value(g.get("faq_heading", "Questions")), PH, site["hours"], items))

    def cta(h2, lead):
        checks = "".join("<li>%s%s</li>" % (TICK, c) for c in ["No obligation", "Photos included", "Price before any work starts"])
        return ('<section class="cta" id="book" aria-labelledby="book-h"><div class="wrap"><div><h2 id="book-h">%s</h2><p class="lead">%s</p>'
                '<ul class="checks">%s</ul><a class="big" href="%s">%s%s</a><p class="sub">Every Day %s. If we miss your call, we call right back.</p></div>%s</div></section></main>'
                % (value(h2), value(lead), checks, TEL, PHONE_SVG, PH, site["hours"], FORM))

    def gcard(g):
        return ('<a class="cs" href="/guides/%s"><img src="%s" alt="%s" width="1200" height="900" loading="lazy" decoding="async"><div class="cs-b"><span class="cs-k">%s</span><h3>%s</h3><p>%s</p><span class="go">Read the guide</span></div></a>'
                % (g["slug"], html.escape(g["hero"]["src"], True), html.escape(g["hero"].get("alt", ""), True), value(g.get("tag", "Guide")), value(g["h1"]), value(g.get("description", ""))))

    out = {}
    for g in guides:
        url = SITE_URL + "/guides/" + g["slug"]
        out[g["slug"] + ".html"] = (head(g, url, g["title"], g["description"], g.get("og") or g["hero"]["src"]) + HEADER + hero(g) + TRUST + body(g) + faq(g)
                                    + cta(g.get("cta_heading", "Book The Free Inspection"), g.get("cta_lead", "Pick a day and a window and we confirm by phone.")) + FOOTER)
    hub = site.get("guides_hub", {})
    title = hub.get("title", "Chimney Guides For Toronto Homeowners | Northmark Chimney")
    desc = hub.get("description", "Plain-language guides from a WETT-certified Toronto chimney technician: what things cost, what inspections involve, and how to read the signs of a problem.")
    hb = ('<main id="main"><section class="hero"><div class="wrap"><div class="hcopy"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">Guides</span></nav>'
          '<span class="tag">Guides</span><h1>%s</h1><p class="lead">%s</p>%s</div></div></section>%s'
          '<section class="sec" aria-labelledby="gl-h"><div class="wrap"><div class="head"><div><h2 id="gl-h">Start Here</h2></div><p class="lead">Written the way we explain things on a job: what it is, what it costs, what to do about it.</p></div><div class="gcards">%s</div></div></section>'
          % (value(hub.get("h1", "Chimney Guides: Straight Answers For Toronto Homeowners")),
             value(hub.get("lead", "What a sweep should cost, what a WETT inspection involves, how to read a water stain near the chimney. No sales pitch — the free inspection is at the end if you want it.")),
             acts(), TRUST, "".join(gcard(g) for g in guides)))
    out["guides.html"] = head(None, SITE_URL + "/guides/", title, desc, guides[0]["hero"]["src"] if guides else "/og-image.jpg", "website") + HEADER + hb + cta("Want A Technician To Look?", "Book the free inspection. Photos of what we find, the price in writing, no obligation.") + FOOTER
    return out


# ----------------------------------------------------------------------------- site files
STATIC_REDIRECTS = [l for l in open("build/redirects.txt", encoding="utf-8").read().splitlines() if l.strip()]


def write_site_files(pages):
    lines = STATIC_REDIRECTS + ["/projects  /projects.html  200", "/projects/  /projects.html  200"]
    lines += ["/projects/%s  /%s.html  200" % (p["slug"], p["slug"]) for p in projects]
    lines += ["/guides  /guides.html  200", "/guides/  /guides.html  200"] + ["/guides/%s  /%s.html  200" % (g["slug"], g["slug"]) for g in guides]
    lines += ["/build/*  /404.html  404", "/templates/*  /404.html  404", "/content/*  /404.html  404", "/netlify/*  /404.html  404", "/*  /404.html  404"]
    open("_redirects", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    # sitemap
    prio = {"index.html": "1.0", "our-work.html": "0.8", "about.html": "0.6", "chimney-service-prices-toronto.html": "0.8"}
    urls = []
    for pg in pages:
        if pg in ("404.html", "thanks.html"): continue
        u = "/" if pg == "index.html" else "/" + pg[:-5]
        pr = prio.get(pg, "0.7" if pg.startswith("chimney-services-") else "0.9")
        urls.append((u, pr))
    urls.append(("/projects/", "0.8")); urls += [("/projects/" + p["slug"], "0.8") for p in projects]
    urls.append(("/guides/", "0.8")); urls += [("/guides/" + g["slug"], "0.8") for g in guides]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += ["  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (SITE_URL, u, TODAY, pr) for u, pr in urls]
    sm.append("</urlset>")
    open("sitemap.xml", "w", encoding="utf-8").write("\n".join(sm) + "\n")
    # llms.txt: keep the hand-written part, regenerate the projects list
    llms = open("llms.txt", encoding="utf-8").read()
    llms = llms.split("\n## Projects")[0].rstrip("\n")
    llms += "\n\n## Projects (case studies, our own photos)\n- [Chimney Projects In Toronto & The GTA](%s/projects/)\n" % SITE_URL
    llms += "".join("- [%s](%s/projects/%s)\n" % (re.sub("<[^>]+>", "", p["h1"]), SITE_URL, p["slug"]) for p in projects)
    llms += "\n## Guides (plain-language explainers)\n- [Chimney Guides](%s/guides/)\n" % SITE_URL
    llms += "".join("- [%s](%s/guides/%s)\n" % (re.sub("<[^>]+>", "", g["h1"]), SITE_URL, g["slug"]) for g in guides)
    open("llms.txt", "w", encoding="utf-8").write(llms)


def responsive_images(h):
    """Give every photo that has an -800 variant a srcset, so phones download the small one."""
    def fix(m):
        tag = m.group(0)
        if "srcset=" in tag or "/logo." in tag: return tag
        src = re.search(r' src="(/[^"]+)\.jpg"', tag)
        if not src or not os.path.exists(src.group(1).lstrip("/") + "-800.jpg"): return tag
        base = src.group(1)
        sizes = "100vw" if "hero-bg" in tag else "(max-width:1000px) 92vw, 50vw"
        return tag.replace(' src="%s.jpg"' % base, ' src="%s.jpg" srcset="%s-800.jpg 800w, %s.jpg 1200w" sizes="%s"' % (base, base, base, sizes), 1)
    return re.sub(r"<img\b[^>]*>", fix, h)


def main():
    pages = sorted(os.path.basename(f) for f in glob.glob("templates/*.html"))
    for pg in pages:
        tpl = open(os.path.join("templates", pg), encoding="utf-8").read()
        vals = load(os.path.join("content/pages", pg[:-5] + ".json"))
        out = fill_slots(tpl, vals)
        out = out.replace("{{cards:home}}", cards_block("home", pg)).replace("{{cards:ourwork}}", cards_block("ourwork", pg)).replace("{{cards:svc}}", cards_block("svc", pg))
        out = out.replace("{{project_link}}", project_link(pg)).replace("{{guide_links}}", guide_links(pg))
        out = fill_tokens(out)
        out = re.sub(r' data-cms(?:-img)?="[^"]*"| data-orig="[^"]*"', "", out)  # editor hooks stay in the templates only
        out = responsive_images(out)
        if "/booking.js" not in out:  # availability from the admin calendar
            out = out.replace("</body>", '<script src="/booking.js" defer></script></body>', 1)
        if 'class="twoup"' in out and "/compare.js" not in out:  # before/after slider
            out = out.replace("</body>", '<script src="/compare.js" defer></script></body>', 1)
        if pg == "index.html":  # Netlify Identity invite / recovery links land on the home page: send them to the admin
            out = out.replace("<body>", "<body><script>if(/^#(invite|recovery|confirmation|email_change)_token=/.test(location.hash))location.replace('/%s/'+location.hash)</script>" % ADMIN_DIR, 1)
        open(pg, "w", encoding="utf-8").write(out)
    chrome_src = open("our-work.html", encoding="utf-8").read()
    for name, h in list(project_pages(chrome_src).items()) + list(guide_pages(chrome_src).items()):
        open(name, "w", encoding="utf-8").write(fill_tokens(h))
    write_site_files(pages)
    if os.path.exists("build/gen_config.py"):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gen_config", "build/gen_config.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.main()
    print("built %d pages + %d projects" % (len(pages), len(projects)))


if __name__ == "__main__":
    main()
