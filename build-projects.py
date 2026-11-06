#!/usr/bin/env python3
"""Builds the /projects/ case-study pages from the shared page chrome in our-work.html.

Run from the repo root:  python3 tools/build-projects.py

Header, footer, inline CSS, booking form and scripts are copied from our-work.html so the
project pages never drift from the rest of the site. Only the content in PROJECTS below is
page-specific. Re-run after editing the chrome on our-work.html.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://northmark-chimney.ca"
PHONE = "(289) 514-5267"
TEL = "tel:+12895145267"
TODAY = "2026-11-06"

src = open(os.path.join(ROOT, "our-work.html"), encoding="utf-8").read()

def between(s, a, b, inclusive=False):
    i = s.index(a); j = s.index(b, i + len(a))
    return s[i:j + len(b)] if inclusive else s[i + len(a):j]

GTM_HEAD = between(src, "<!-- Google Tag Manager -->", "<!-- End Google Tag Manager -->", True)
CSS = between(src, "<style>", "</style>")
CSS = CSS.split("/* project case studies */")[0]  # the card CSS is re-appended below; never duplicate it
FONTS = between(src, '<link rel="icon"', "<style>")
FONTS = '<link rel="icon"' + FONTS  # icon + fonts
TAIL_HEAD = src[src.index('<script src="/seo-hook.js"'):src.index("</head>")]
HEADER = between(src, "<body>", '<main id="main">').replace(' aria-current="page"', "")
FOOTER = src[src.index("</main>") + len("</main>"):]
FORM = between(src, '<form class="form two-step"', "</form>", True)

PHONE_SVG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 '
             '19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 '
             '1.8.7 2.6a2 2 0 0 1-.5 2.1L8 9.7a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.8.3 1.7.5 2.6.7a2 2 0 0 1 1.7 2z"/></svg>')
TICK = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')
TICK_SM = TICK.replace('width="20" height="20"', 'width="16" height="16"')

EXTRA_CSS = """
/* project case studies */
.shot.tall img{aspect-ratio:3/4}
.shot figcaption b{color:var(--ink);font-weight:600}
.specs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:30px;border:1px solid var(--rule);background:var(--card);border-radius:var(--r-card);overflow:hidden;box-shadow:var(--shadow)}
.specs div{padding:16px 20px;border-top:1px solid var(--rule-2);min-width:0}
.specs div:nth-child(-n+2){border-top:0}
.specs div:nth-child(odd){border-inline-end:1px solid var(--rule-2)}
.specs dt{font-size:13px;font-weight:600;color:var(--mut)}
.specs dd{font-weight:600;color:var(--ink);font-size:15.5px;margin-top:4px;line-height:1.4}
.story{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.9fr);gap:56px;align-items:start}
.story .prose p{font-size:17px;line-height:1.66;color:var(--ink-2)}
.story h3{font-size:22px;margin:30px 0 12px}
.story h3:first-child{margin-top:0}
.figs{display:grid;gap:18px;position:sticky;top:98px}
.figs figure{margin:0;border:1px solid var(--rule);background:var(--card);padding:10px;border-radius:var(--r-card);box-shadow:var(--shadow)}
.figs img{aspect-ratio:4/3;object-fit:cover;width:100%;border-radius:8px}
.figs figcaption{padding:12px 4px 2px;font-size:13.5px;color:var(--mut);line-height:1.45}
.figs figcaption b{color:var(--ink);font-weight:600}
.jobsteps{counter-reset:s;display:grid;border-top:1px solid var(--rule);margin-top:10px}
.jobsteps li{counter-increment:s;display:grid;grid-template-columns:48px minmax(0,1fr);gap:14px;padding:20px 0;border-bottom:1px solid var(--rule)}
.jobsteps li::before{content:counter(s,decimal-leading-zero);font-family:Archivo,sans-serif;font-weight:800;font-size:24px;color:var(--copper);line-height:1.05;letter-spacing:-.04em}
.jobsteps b{display:block;font-size:16.5px;margin-bottom:4px;color:var(--ink)}
.jobsteps p{color:var(--ink-2);font-size:15.5px;line-height:1.55}
.notice{display:flex;gap:14px;align-items:flex-start;margin-top:26px;padding:18px 20px;border-radius:var(--r-field);background:var(--copper-soft);border:1px solid rgba(180,71,27,.28);border-inline-start:3px solid var(--copper);color:var(--ink-2);font-size:15px;line-height:1.55}
.notice svg{flex:none;color:var(--copper);margin-top:3px}
.notice b{color:var(--ink)}
.cs-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
.cs{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--rule-2);border-radius:var(--r-card);overflow:hidden;text-decoration:none;color:var(--ink);box-shadow:var(--shadow);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease}
.cs:hover{transform:translateY(-2px);box-shadow:var(--shadow-lift);border-color:rgba(192,74,24,.3)}
.cs img{width:100%;aspect-ratio:4/3;object-fit:cover}
.cs-b{padding:22px 22px 24px;display:grid;gap:8px;align-content:start;flex:1}
.cs-k{font-size:13px;font-weight:600;color:var(--copper)}
.cs h3{font-size:20px;color:var(--ink)}
.cs p{color:var(--ink-2);font-size:15px;line-height:1.5}
.cs .go{margin-top:auto;padding-top:12px}
.sec.navy .cs h3{color:var(--ink)}.sec.navy .cs p{color:var(--ink-2)}
.cs-grid.two,.cs-grid.hub{grid-template-columns:repeat(2,minmax(0,1fr))}.cs.feat{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr)}
.cs.feat img{aspect-ratio:auto;height:100%;min-height:300px;max-height:440px}
.cs.feat .cs-b{padding:34px 34px 32px;align-content:center;gap:12px}
.cs.feat h3{font-size:clamp(24px,2.6vw,32px)}
.cs.feat p{font-size:16.5px}
@media(max-width:1000px){.hero .specs{order:10}.shot.tall img{max-height:72vh}.story{grid-template-columns:1fr}.figs{position:static;grid-template-columns:1fr 1fr}.cs-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.cs.feat{grid-template-columns:1fr}.cs.feat img{min-height:0;aspect-ratio:4/3}}
@media(max-width:720px){.cs-grid,.specs,.figs{grid-template-columns:1fr}.specs div:nth-child(odd){border-inline-end:0}.specs div:nth-child(2){border-top:1px solid var(--rule-2)}}
"""

def esc(s): return html.escape(s, quote=True)

def head(p):
    url = SITE + p["url"]
    return (f'<!DOCTYPE html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'{GTM_HEAD}<title>{esc(p["title"])}</title><meta name="description" content="{esc(p["desc"])}">'
            f'<link rel="canonical" href="{url}"><meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">'
            f'<meta name="theme-color" content="#F5F2EC"><meta property="og:site_name" content="Northmark Chimney"><meta property="og:locale" content="en_CA">'
            f'<meta property="og:title" content="{esc(p["title"])}"><meta property="og:description" content="{esc(p["desc"])}"><meta property="og:type" content="{"website" if p.get("hub") else "article"}">'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/{p["og"]}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta name="twitter:card" content="summary_large_image">{FONTS}<style>{CSS}{EXTRA_CSS}</style>'
            f'<script type="application/ld+json">{json.dumps(schema(p), ensure_ascii=False)}</script>{TAIL_HEAD}</head><body>')

def schema(p):
    url = SITE + p["url"]
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Our Work", "item": SITE + "/our-work"},
        {"@type": "ListItem", "position": 3, "name": "Projects", "item": SITE + "/projects/"}]}
    if p.get("hub"):
        return [crumbs, {"@context": "https://schema.org", "@type": "CollectionPage", "name": p["title"], "url": url,
                         "description": p["desc"], "isPartOf": {"@id": SITE + "/#website"},
                         "about": {"@id": SITE + "/#business"},
                         "hasPart": [{"@type": "Article", "headline": q["h1"], "url": SITE + q["url"], "image": SITE + "/" + q["hero"]} for q in PROJECTS]}]
    crumbs["itemListElement"].append({"@type": "ListItem", "position": 4, "name": p["crumb"], "item": url})
    art = {"@context": "https://schema.org", "@type": "Article", "@id": url + "#article", "headline": p["h1"],
           "description": p["desc"], "url": url, "mainEntityOfPage": url, "datePublished": TODAY, "dateModified": TODAY,
           "inLanguage": "en-CA",
           "image": [{"@type": "ImageObject", "contentUrl": SITE + "/" + f["src"], "caption": f["cap_plain"]} for f in [dict(src=p["hero"], cap_plain=p["hero_alt"])] + p["figs"]],
           "author": {"@type": "Organization", "name": "Northmark Chimney", "@id": SITE + "/#business"},
           "publisher": {"@type": "Organization", "name": "Northmark Chimney", "@id": SITE + "/#business", "logo": {"@type": "ImageObject", "url": SITE + "/logo.png"}},
           "about": {"@type": "Service", "name": p["service_name"], "url": SITE + p["service_url"], "provider": {"@id": SITE + "/#business"},
                     "areaServed": {"@type": "City", "name": "Toronto", "containedInPlace": {"@type": "AdministrativeArea", "name": "Ontario"}}},
           "locationCreated": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": p["where_schema"], "addressRegion": "ON", "addressCountry": "CA"}}}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in p["faq"]]}
    return [crumbs, art, faq]

def hero(p):
    acts = (f'<div class="acts"><a class="btn lg" href="#book">Book my free inspection</a>'
            f'<a class="btn line lg" href="{TEL}">{PHONE_SVG}Call {PHONE}</a></div>')
    specs = "".join(f'<div><dt>{esc(k)}</dt><dd>{v}</dd></div>' for k, v in p["specs"])
    return (f'<main id="main"><section class="hero"><div class="wrap"><div class="hcopy">'
            f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/our-work">Our Work</a> / <a href="/projects/">Projects</a> / <span aria-current="page">{esc(p["crumb"])}</span></nav>'
            f'<span class="tag">{p["tag"]}</span><h1>{p["h1"]}</h1><p class="lead">{p["lead"]}</p>{acts}'
            f'<dl class="specs" aria-label="Job summary">{specs}</dl></div>'
            f'<figure class="shot tall"><img src="/{p["hero"]}" srcset="/{p["hero"].replace(".jpg","-480.jpg")} 480w, /{p["hero"].replace(".jpg","-800.jpg")} 800w, /{p["hero"]} 1200w" '
            f'sizes="(max-width:1000px) 92vw, 46vw" alt="{esc(p["hero_alt"])}" width="1200" height="1600" fetchpriority="high" decoding="async">'
            f'<figcaption><b>Photo from the job.</b> {esc(p["hero_cap"])}</figcaption></figure></div></section>')

TRUST = between(src, '<section class="trust"', "</section>", True)

def story(p):
    figs = "".join(f'<figure><img src="/{f["src"]}" srcset="/{f["src"].replace(".jpg","-800.jpg")} 800w, /{f["src"]} 1200w" sizes="(max-width:1000px) 46vw, 40vw" '
                   f'alt="{esc(f["alt"])}" width="1200" height="900" loading="lazy" decoding="async"><figcaption><b>{esc(f["k"])}</b> {esc(f["cap"])}</figcaption></figure>'
                   for f in p["figs"])
    steps = "".join(f'<li><div><b>{esc(t)}</b><p>{d}</p></div></li>' for t, d in p["steps"])
    notice = ""
    if p.get("notice"):
        notice = (f'<div class="notice"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                  f'<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/></svg><p>{p["notice"]}</p></div>')
    return (f'<section class="sec" aria-labelledby="job-h"><div class="wrap"><div class="head"><div><h2 id="job-h">{p["job_h2"]}</h2></div><p class="lead">{p["job_lead"]}</p></div>'
            f'<div class="story"><div><div class="prose"><h3>{esc(p["found_h"])}</h3>{"".join(f"<p>{x}</p>" for x in p["found"])}'
            f'<h3>What we did</h3></div><ol class="jobsteps">{steps}</ol>{notice}</div><div class="figs">{figs}</div></div></div></section>')

def pillars(p):
    cards = "".join(f'<div class="pillar"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ic}</svg><h3>{esc(t)}</h3><p>{d}</p></div>'
                    for ic, t, d in p["pillars"])
    return (f'<section class="sec stone" aria-labelledby="why-h"><div class="wrap"><div class="head"><div><h2 id="why-h">{p["why_h2"]}</h2></div><p class="lead">{p["why_lead"]}</p></div>'
            f'<div class="pillars">{cards}</div></div></section>')

def related(p):
    cards = "".join(f'<a class="svc" href="{u}"><div class="svc-img"><img src="/{img}" alt="{esc(alt)}" width="1200" height="900" loading="lazy" decoding="async"></div>'
                    f'<div class="svc-b"><h3>{t}</h3><p class="svc-pr"><b>Fixes</b>{fx}</p><p class="svc-bn">{bn}</p><span class="go">Learn More</span></div></a>'
                    for u, img, alt, t, fx, bn in p["related"])
    others = [q for q in PROJECTS if q is not p]
    more = "".join(cs_card(q) for q in others)
    return (f'<section class="sec" aria-labelledby="rel-h"><div class="wrap"><div class="head"><div><h2 id="rel-h">The Services Behind This Job</h2></div><p class="lead">What we did here is what we do every week across Toronto and the GTA. Read about the service, or book the free inspection and we will tell you what your chimney needs.</p></div>'
            f'<div class="svcs">{cards}</div></div></section>'
            f'<section class="sec navy" aria-labelledby="more-h"><div class="wrap"><div class="head"><div><h2 id="more-h">More Northmark Projects</h2></div><p class="lead">Other recent jobs, photographed by us.</p></div>'
            f'<div class="cs-grid two">{more}</div><div class="more-row"><p>Before-and-after photos and recent jobs by area.</p><a class="btn line-w" href="/our-work">See all our work</a></div></div></section>')

def cs_card(q, feat=False):
    return (f'<a class="cs{" feat" if feat else ""}" href="{q["url"]}"><img src="/{q["card"]}" alt="{esc(q["card_alt"])}" width="1200" height="900" loading="lazy" decoding="async">'
            f'<div class="cs-b"><span class="cs-k">{q["tag"]}</span><h3>{q["card_h"]}</h3><p>{q["card_p"]}</p><span class="go">Read the case study</span></div></a>')

def faq(p):
    items = "".join(f'<details class="faq"><summary>{esc(q)}</summary><p>{a}</p></details>' for q, a in p["faq"])
    return (f'<section class="sec stone" id="faq" aria-labelledby="faq-h"><div class="wrap"><div class="faqwrap"><div><h2 id="faq-h">{p["faq_h2"]}</h2>'
            f'<p class="lead" style="margin-top:14px">Straight answers. If yours is not here, call {PHONE} — every day 7:00–22:00.</p></div><div class="faqs">{items}</div></div></div></section>')

def cta(p):
    checks = "".join(f'<li>{TICK}{esc(c)}</li>' for c in ["No obligation", "Photos included", "Price before any work starts"])
    return (f'<section class="cta" id="book" aria-labelledby="book-h"><div class="wrap"><div><h2 id="book-h">{p["cta_h2"]}</h2><p class="lead">{p["cta_lead"]}</p>'
            f'<ul class="checks">{checks}</ul><a class="big" href="{TEL}">{PHONE_SVG}{PHONE}</a><p class="sub">Every Day 7:00–22:00. If we miss your call, we call right back.</p></div>{FORM}</div></section></main>')

def page(p):
    return head(p) + HEADER + hero(p) + TRUST + story(p) + pillars(p) + related(p) + faq(p) + cta(p) + FOOTER

def hub(p):
    cards = cs_card(PROJECTS[0], feat=True) + "".join(cs_card(q) for q in PROJECTS[1:])
    body = (f'<main id="main"><section class="hero"><div class="wrap"><div class="hcopy">'
            f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/our-work">Our Work</a> / <span aria-current="page">Projects</span></nav>'
            f'<span class="tag">Project case studies</span><h1>{p["h1"]}</h1><p class="lead">{p["lead"]}</p>'
            f'<div class="acts"><a class="btn lg" href="#book">Book my free inspection</a><a class="btn line lg" href="{TEL}">{PHONE_SVG}Call {PHONE}</a></div>'
            f'<ul class="hpoints"><li>{TICK_SM}<span><b>Our own photos</b> — taken on the job, not bought from a library</span></li>'
            f'<li>{TICK_SM}<span><b>What was wrong, what we did, what it fixed</b> — in plain language</span></li>'
            f'<li>{TICK_SM}<span><b>The same process</b> you get: free inspection, photos, price in writing first</span></li></ul></div>'
            f'<figure class="shot tall"><img src="/stone-chimney-restoration-gta.jpg" srcset="/stone-chimney-restoration-gta-480.jpg 480w, /stone-chimney-restoration-gta-800.jpg 800w, /stone-chimney-restoration-gta.jpg 1200w" sizes="(max-width:1000px) 92vw, 46vw" '
            f'alt="Restored stone chimney with a new concrete top and stainless steel cap, photographed by Northmark" width="1200" height="1600" fetchpriority="high" decoding="async">'
            f'<figcaption><b>Photo from the job.</b> Stone chimney restored, capped and sealed.</figcaption></figure></div></section>{TRUST}'
            f'<section class="sec" aria-labelledby="list-h"><div class="wrap"><div class="head"><div><h2 id="list-h">Three Recent Jobs, Start To Finish</h2></div><p class="lead">Each case study walks through one chimney: what we found, the steps we took, and the photo of the finished work.</p></div>'
            f'<div class="cs-grid hub">{cards}</div><div class="more-row"><p>Looking for before-and-after pairs and jobs by neighbourhood?</p><a class="btn line" href="/our-work">See all our work</a></div></div></section>'
            f'<section class="sec stone" aria-labelledby="how-h"><div class="wrap"><div class="head"><div><h2 id="how-h">How Every Northmark Job Runs</h2></div><p class="lead">The projects above all followed the same four steps. Yours would too.</p></div>'
            f'<div class="steps"><div class="step"><span class="n">Step 1</span><h3>Free inspection</h3><p>A technician comes to your home, looks at the chimney top to bottom and photographs what he finds.</p></div>'
            f'<div class="step"><span class="n">Step 2</span><h3>Price in writing</h3><p>You get the photos and the exact price before anything starts. No work without your go-ahead.</p></div>'
            f'<div class="step"><span class="n">Step 3</span><h3>The work</h3><p>Materials matched to your home, floors and roof protected, the area left the way we found it.</p></div>'
            f'<div class="step"><span class="n">Step 4</span><h3>Photos of the result</h3><p>You see the finished work the same way we do — in photos, including the parts of the chimney you cannot see from the ground.</p></div></div></div></section>'
            + cta(p) + FOOTER)
    return head(p) + HEADER + body

# ------------------------------------------------------------------ content
PROJECTS = [
 dict(
  slug="chimney-tuckpointing-toronto", url="/projects/chimney-tuckpointing-toronto", crumb="Chimney Tuckpointing, Toronto",
  title="Chimney Tuckpointing Toronto: Full Restoration | Northmark",
  desc="A Toronto brick chimney fully tuckpointed: old mortar cut out, every joint repointed, the roofline sealed. Photos from the job. Free inspection: (289) 514-5267.",
  tag="Tuckpointing · Toronto", h1="Chimney Tuckpointing In Toronto: Every Joint Repointed, Above The Roofline",
  lead="A full tuckpointing restoration on a brick chimney in Toronto. The weathered mortar was cut out of every joint above the roofline and replaced with fresh mortar, and the chimney was sealed where it meets the roof. The brick is original — only the mortar is new.",
  specs=[("Service", '<a href="/chimney-masonry-repair-toronto">Masonry &amp; Tuckpointing</a>'), ("Where", "Toronto"),
         ("Scope", "Full repoint above the roofline, roofline sealed"), ("Result", "Closed, weather-tight joints on the original brick")],
  hero="chimney-tuckpointing-toronto.jpg", hero_alt="Brick chimney in Toronto after full tuckpointing, with fresh mortar in every joint and sealed flashing at the roofline",
  hero_cap="The finished chimney: original brick, every joint repointed, flashing sealed at the roofline.",
  og="chimney-tuckpointing-toronto-og.jpg", card="chimney-tuckpointing-toronto-mortar-joints.jpg", card_alt="Close-up of freshly tuckpointed brick joints on a Toronto chimney",
  card_h="Chimney tuckpointing in Toronto", card_p="Every joint above the roofline cut out and repointed on a brick chimney, and the roofline sealed. The brick stayed; only the mortar is new.",
  service_name="Chimney Masonry & Tuckpointing", service_url="/chimney-masonry-repair-toronto", where_schema="Toronto",
  job_h2="The Job: What We Found, What We Did", job_lead="One chimney, start to finish. The detail photos are from the same chimney, taken when the work was done.",
  found_h="What we found",
  found=["The brick itself was sound. The mortar between the bricks was not: weathered back from the face of the brick, crumbling in places and open to water. That is the usual Toronto story. Freeze-thaw cycles work on the joints first, and once water can get into an open joint, every winter makes it worse.",
         "Left alone, open joints let water into the chimney and, eventually, into the roof structure around it. Bricks start to spall and shift, and a repair becomes a rebuild. Caught at this stage, tuckpointing restores the chimney for a fraction of what a rebuild costs."],
  steps=[("Inspection and photos", "The chimney was checked from the roof, joint by joint, and photographed. The homeowner got the photos and the price in writing before anything started."),
         ("The old mortar cut out", "Every joint above the roofline was ground back to sound material and the dust blown out, so the new mortar bonds to clean brick rather than to the weathered skin of the old joint."),
         ("Fresh mortar, packed and tooled", "The joints were filled in lifts, packed tight, and tooled to a consistent profile. The result in the photo: full, even joints across every face of the chimney."),
         ("The roofline sealed", "Where the chimney meets the shingles, the flashing was sealed tight to the brick — the point where most chimney leaks actually start."),
         ("Clean-up and final photos", "Roof cleared of debris, and a set of photos of the finished chimney for the homeowner — the one at the top of this page is from that set.")],
  figs=[dict(src="chimney-tuckpointing-toronto-mortar-joints.jpg", alt="Detail of fresh, full mortar joints on the repointed Toronto brick chimney", k="Detail: the joints.", cap="Full, even mortar in every joint. The brick was kept; only the mortar was replaced.", cap_plain="Fresh, full mortar joints on the repointed brick chimney"),
        dict(src="chimney-tuckpointing-toronto-roofline-flashing.jpg", alt="Corner of the tuckpointed chimney where the dark metal flashing meets the brick at the roofline", k="Detail: the roofline.", cap="Flashing sealed to the brick where the chimney meets the roof.", cap_plain="The chimney corner where the flashing meets the brick at the roofline")],
  why_h2="Why Tuckpoint Instead Of Rebuild?", why_lead="When the brick is sound, replacing the mortar is the right repair — and the one that keeps the look of the house.",
  pillars=[('<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/>', "The original brick stays", "Toronto brick from the 1920s to the 1980s is hard to match. Tuckpointing keeps it, so the chimney still looks like it belongs on the house."),
           ('<path d="M12 2.7C8 7.5 5 10.3 5 14a7 7 0 0 0 14 0c0-3.7-3-6.5-7-11.3z"/>', "Water stops getting in", "A closed joint is the whole point. Rain and melting snow run off the chimney instead of into it — and into the attic below."),
           ('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', "Done once, done early", "Mortar is the part of a chimney designed to wear first. Replacing it on time is routine work; waiting turns it into brick replacement or a rebuild.")],
  related=[("/chimney-masonry-repair-toronto", "ba-after.jpg", "Repointed brick chimney in Toronto", "Masonry &amp; Tuckpointing", "Crumbling mortar, loose or spalling brick, a leaning or leaking chimney.", "Repointing, brick replacement and rebuilds, matched to your home."),
           ("/chimney-flashing-toronto", "ba-flashing-after.jpg", "Chimney flashing sealed at the roofline", "Flashing &amp; Waterproofing", "Water stains near the chimney, leaks that show up after rain.", "Flashing resealed or replaced, and the masonry sealed against water."),
           ("/chimney-repair-toronto", "ba-repairs-after.jpg", "Repaired brick chimney above the roofline", "Chimney Repair", "Cracked crowns, damaged brick, water getting in.", "Fixed once, with materials matched to your home.")],
  faq_h2="Questions About Chimney Tuckpointing",
  faq=[("What is chimney tuckpointing?", "Tuckpointing (also called repointing) is cutting the old, weathered mortar out of the joints between the bricks and filling them with fresh mortar. The brick stays. It is the standard repair for a chimney whose mortar has worn before the brick has."),
       ("How do I know if my chimney needs tuckpointing?", "Look at the joints from the ground with a zoom lens or binoculars: mortar that has receded behind the face of the brick, gaps, or sandy mortar you can scrape out with a key are the signs. White staining on the brick and water marks near the fireplace are signs water is already getting in. Our free inspection checks every joint from the roof and photographs them for you."),
       ("Do you match the colour of the mortar?", "As closely as the original allows. Mortar colour depends on the sand and the mix; we match the mix to the age and style of the house so the new joints blend in once they have cured. Fresh mortar always looks lighter for the first few weeks."),
       ("Can tuckpointing be done in winter?", "Mortar needs to cure above freezing, so the work is done in the warmer months. If you notice open joints in winter, book the inspection now — we photograph and price the work, and schedule it for the first suitable weather."),
       ("What does tuckpointing cost in Toronto?", f"It depends on the size of the chimney and how much of it needs repointing — which is exactly what the free inspection establishes. You get the price in writing before any work starts. See <a href=\"/chimney-service-prices-toronto\">how we price the work</a>.")],
  cta_h2="Think Your Joints Are Going?", cta_lead="Book the free inspection. We photograph every joint from the roof, show you what is open, and give you the price in writing before any work starts.",
 ),
 dict(
  slug="stone-chimney-restoration", url="/projects/stone-chimney-restoration", crumb="Stone Chimney Restoration",
  title="Stone Chimney Restoration: Concrete Top & Cap | Northmark",
  desc="A GTA stone chimney restored: joints repointed, top rebuilt in concrete, stainless cap fitted. Photos from our job. Free inspection: (289) 514-5267.",
  tag="Chimney restoration · Toronto &amp; GTA", h1="Stone Chimney Restoration: Repointed, Rebuilt In Concrete, Capped",
  lead="An old fieldstone chimney restored and preserved instead of torn down. The stone joints were repointed, the failing upper section and crown were rebuilt in concrete to shed water, and a stainless steel cap was fitted over the flue. The photo is the finished chimney.",
  specs=[("Service", '<a href="/chimney-repair-toronto">Chimney Repair</a> &amp; <a href="/chimney-masonry-repair-toronto">Masonry</a>'), ("Where", "Toronto &amp; GTA"),
         ("Scope", "Stone repointed, concrete top and crown, stainless cap, roofline sealed"), ("Result", "A weather-tight chimney with the original stone preserved")],
  hero="stone-chimney-restoration-gta.jpg", hero_alt="Restored fieldstone chimney with repointed joints, a new concrete top and crown, and a stainless steel cap, on a cedar-shake roof",
  hero_cap="The finished chimney: original stone below, concrete top and crown above, stainless cap on the flue.",
  og="stone-chimney-restoration-og.jpg", card="stone-chimney-concrete-crown-stainless-cap.jpg", card_alt="New concrete top and stainless steel cap on a restored stone chimney",
  card_h="Stone chimney restored and preserved", card_p="Fieldstone joints repointed, the weather-beaten top rebuilt in concrete with a crown, and a stainless cap fitted. The stone was saved, not replaced.",
  service_name="Chimney Repair", service_url="/chimney-repair-toronto", where_schema="Toronto",
  job_h2="The Job: What We Found, What We Did", job_lead="A chimney that was worth saving. The detail photos are from the same chimney after the work.",
  found_h="What we found",
  found=["A fieldstone chimney on an older home, and the two problems stone chimneys almost always have. The joints between the irregular stones — far more joint area than a brick chimney — had washed out and were taking in water. And the top of the chimney, the part that takes every freeze-thaw cycle head-on, had deteriorated past the point where repointing alone would hold.",
         "Tearing it down and rebuilding in brick would have been the easy quote. It would also have thrown away the stone that makes the house what it is. The job was to preserve the stone where it was sound and rebuild in concrete only where the chimney was actually failing."],
  steps=[("Inspection and photos", "The chimney was checked from the roof and the flue checked from above. The homeowner got the photos and a written price for the restoration before anything started."),
         ("Stone joints repointed", "The loose, washed-out mortar was raked out between the stones and the joints packed with fresh mortar — worked into the irregular gaps and tooled, so the stone face stays exposed and the water path is closed."),
         ("The top rebuilt in concrete", "The failing upper section was encased in a new concrete coat and finished with a crown around the flue. Concrete here does what the weathered stone top could no longer do: take the weather and shed water away from the chimney."),
         ("Stainless steel cap fitted", "A stainless cap with mesh screen was fitted over the flue. It keeps rain and snow out of the flue, keeps birds and animals out, and will not rust."),
         ("Roofline sealed, site cleared", "The flashing where the chimney meets the roof was sealed, the roof cleared, and the finished chimney photographed for the homeowner.")],
  figs=[dict(src="stone-chimney-concrete-crown-stainless-cap.jpg", alt="Close-up of the new concrete top and stainless steel cap with mesh on the restored stone chimney", k="Detail: top and cap.", cap="Concrete top with a crown around the flue, stainless cap with mesh screen.", cap_plain="New concrete top and stainless steel cap on the restored stone chimney"),
        dict(src="stone-chimney-repointed-joints.jpg", alt="Close-up of repointed fieldstone joints on the restored chimney, with the stone face left exposed", k="Detail: the stone.", cap="Joints packed and tooled around the original stone — the stone stays visible.", cap_plain="Repointed fieldstone joints with the original stone left exposed")],
  why_h2="Why Restore A Stone Chimney Instead Of Replacing It?", why_lead="Stone is the hardest part of an old house to replace. Treat the stone and the top differently, and the chimney gets another long life.",
  pillars=[('<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/>', "The stone is irreplaceable", "Fieldstone chimneys were built from what was on the land. Repointing keeps the original stone and the look of the house; a brick rebuild never quite does."),
           ('<path d="M12 2.7C8 7.5 5 10.3 5 14a7 7 0 0 0 14 0c0-3.7-3-6.5-7-11.3z"/>', "Concrete where the weather hits", "The top of a chimney takes the worst of rain, snow and freeze-thaw. A solid concrete top and crown shed water instead of absorbing it."),
           ('<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>', "Capped and screened", "An open flue takes in rain, snow, leaves and animals. A stainless cap closes it off and never needs replacing for rust.")],
  related=[("/chimney-repair-toronto", "ba-repairs-after.jpg", "Repaired chimney above the roofline", "Chimney Repair", "Cracked crowns, failing tops, water getting in.", "Fixed once, with materials matched to your home."),
           ("/chimney-cap-installation-toronto", "ba-caps-after.jpg", "Stainless steel chimney cap fitted on a flue", "Chimney Caps", "Rain, snow, birds and animals getting into the flue.", "Caps measured to your flue, in stainless so they last."),
           ("/chimney-masonry-repair-toronto", "ba-after.jpg", "Repointed masonry chimney", "Masonry &amp; Tuckpointing", "Washed-out joints in brick or stone.", "Repointing that keeps the original masonry.")],
  faq_h2="Questions About Stone Chimney Restoration",
  faq=[("Why rebuild the top in concrete rather than in stone?", "The top of a chimney gets the most weather and the least protection. Where the stone top has deteriorated, a concrete top with a proper crown is the durable fix: it is solid, it sheds water, and it protects the stone below it. The stone that was still sound was repointed and kept exposed."),
       ("Does repointing stone work differently from brick?", "Yes. Stone joints are irregular and much wider, so there is more joint to rake out and fill, and the mortar has to be worked into the gaps around each stone rather than along a straight line. It takes longer than brick, and it is the reason washed-out joints are so common on stone chimneys."),
       ("Why a stainless steel cap?", "Galvanized caps rust and stain the masonry below them within a few years. A stainless cap does not, so it is the last cap the chimney should need. The mesh keeps birds and animals out; the lid keeps rain and snow out of the flue."),
       ("Can every old chimney be restored, or do some have to come down?", "Most can be restored, and the free inspection tells you which yours is. A chimney that is leaning, with stone or brick loose through the whole structure, may need a partial or full rebuild. We photograph what we find and price the options in writing."),
       ("Do you work on stone chimneys across the GTA?", "Yes — Toronto and the whole GTA, from Etobicoke to Scarborough and north through Vaughan, Richmond Hill and Markham. See <a href=\"/#areas\">where we work</a>.")],
  cta_h2="Have An Old Stone Or Brick Chimney?", cta_lead="Book the free inspection. We photograph the top, the joints and the flue, tell you what can be saved, and give you the price in writing before any work starts.",
 ),
 dict(
  slug="gas-fireplace-burner-installation", url="/projects/gas-fireplace-burner-installation", crumb="Gas Fireplace Burner Installation",
  title="Gas Fireplace Burner Installation, GTA | Northmark Chimney",
  desc="A new gas burner system installed in an existing GTA fireplace, electronic ignition, tested and running. Photo from the job. Call (289) 514-5267.",
  tag="Gas fireplace · Toronto &amp; GTA", h1="Gas Fireplace Burner Installation: A New Gas System In An Existing Fireplace",
  lead="A new gas burner system fitted into an existing fireplace in the GTA, with electronic ignition. The photo is the burner on its first test burn — the fireplace running on gas, checked and ready to hand over.",
  specs=[("Service", '<a href="/fireplace-repair-toronto">Fireplace Repair</a>, wood and gas'), ("Where", "Toronto &amp; GTA"),
         ("Scope", "Gas burner system installed in the existing firebox, ignition fitted, tested"), ("Result", "A fireplace running on gas, with the flue and firebox checked")],
  hero="gas-fireplace-burner-installation-gta.jpg", hero_alt="New gas burner system on its first test burn inside an existing fireplace firebox with light refractory brick panels",
  hero_cap="First test burn: the new burner running inside the existing firebox.",
  og="gas-fireplace-burner-installation-og.jpg", card="gas-fireplace-burner-test-burn.jpg", card_alt="Blue and yellow flames on a new gas fireplace burner during its test burn",
  card_h="Gas burner system installed in an existing fireplace", card_p="A new gas burner with electronic ignition set into an existing firebox in the GTA, connected, tested and running on its first burn.",
  service_name="Fireplace Repair", service_url="/fireplace-repair-toronto", where_schema="Toronto",
  job_h2="The Job: What We Found, What We Did", job_lead="The homeowner kept the fireplace and changed what burns in it. The detail photo is the burner on test.",
  found_h="What we found",
  found=["An existing fireplace in good condition, with a sound firebox, and a homeowner who wanted the convenience of gas: heat at the push of a button, no wood to store, no ash to clean out. The job was to set a new gas burner system into the firebox the house already had, rather than replace the fireplace.",
         "A gas install starts the same way every Northmark job does — with the chimney and firebox, not the appliance. A fireplace that will burn gas still vents through the flue, so the flue has to be clear and the firebox sound before anything is connected."],
  steps=[("Firebox and flue checked", "The firebox, damper and flue were inspected and photographed before the install, so the new system vents into a chimney that is actually ready for it."),
         ("Firebox prepared", "The firebox was cleared and prepared, and the burner position set so the flames sit where the log set and the venting expect them."),
         ("Burner system set", "The burner assembly, grate and electronic ignition module were set and secured in the firebox, with the ignition wiring routed clear of the heat."),
         ("Gas connected and commissioned", "In Ontario, the gas connection is regulated work: it is made by a TSSA-certified gas technician, with the connection checked for leaks before the appliance is lit."),
         ("Test burn and hand-over", "The system was run through a full test burn — the photo at the top of the page — and the homeowner was walked through lighting, shutting off and what to watch for.")],
  notice="<b>About gas work in Ontario.</b> Gas appliance connections must be made by a TSSA-certified gas technician. When you book, tell us what you have and what you want — we confirm how your job is handled, and who does what, before anything is scheduled.",
  figs=[dict(src="gas-fireplace-burner-test-burn.jpg", alt="Close-up of the new gas burner assembly with blue and yellow flames during the test burn", k="Detail: the burner.", cap="The burner on test, before the hand-over.", cap_plain="The new gas burner assembly during its test burn")],
  why_h2="Gas In An Existing Fireplace: What To Know", why_lead="The fireplace you have is usually the right place for gas. Three things decide whether it is a good fit.",
  pillars=[('<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/>', "The fireplace stays", "A gas burner or log set goes into the firebox you already have. The mantel, the surround and the room stay as they are — what changes is the fuel."),
           ('<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>', "Venting and safety first", "Gas still produces combustion gases. The flue, damper and firebox are checked before anything is connected, and the gas connection is made by a certified technician."),
           ('<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>', "The chimney still needs looking after", "A gas fireplace vents through the same chimney. A yearly inspection keeps the flue clear and catches moisture damage early — gas exhaust is wet.")],
  related=[("/fireplace-repair-toronto", "svc-cleaning.jpg", "Clean fireplace and hearth after a Northmark visit", "Fireplace Repair", "Fireboxes, dampers, smoke chambers, gas fireplaces that will not light or stay lit.", "Wood and gas, with safety issues explained in plain language."),
           ("/chimney-inspection-toronto", "report-sample.jpg", "Chimney inspection report with camera photos", "Chimney Inspection", "Not knowing what state the flue and firebox are in.", "Camera photos and a 19-point report, free at your home."),
           ("/chimney-liner-toronto", "liner.jpg", "Stainless chimney liner", "Chimney Liners", "A cracked, damaged or missing flue liner.", "Heat and exhaust vented the way they should be.")],
  faq_h2="Questions About Gas Fireplaces",
  faq=[("Can you put a gas burner into my wood-burning fireplace?", "Often, yes. It depends on the condition of the firebox and flue and on getting a gas line to the fireplace. Tell us what you have when you book; the free inspection confirms whether your fireplace is a fit and what the job involves."),
       ("Who connects the gas?", "In Ontario, gas appliance connections are regulated by the TSSA and must be made by a certified gas technician. We confirm how your job is handled, and who does what, when you book — before anything is scheduled."),
       ("Does a gas fireplace still need a chimney inspection?", "Yes. A gas fireplace in a masonry fireplace vents through the chimney, and gas exhaust carries a lot of moisture, which works on the flue over time. A yearly inspection keeps the flue clear and catches damage early."),
       ("My gas fireplace will not light or stay lit. Is that something you fix?", "Yes — tell us the make if you know it and what it is doing or not doing, and we confirm it is a fit before anything is booked. See <a href=\"/fireplace-repair-toronto\">fireplace repair</a>."),
       ("Do you install gas fireplaces across the GTA?", "Toronto and the GTA — Etobicoke to Scarborough, and north through Vaughan, Richmond Hill and Markham. See <a href=\"/#areas\">where we work</a>.")],
  cta_h2="Thinking About Gas?", cta_lead="Book the free inspection. We check the firebox and flue, tell you what your fireplace can take, and give you the price in writing before any work starts.",
 ),
]

HUB = dict(
  url="/projects/", hub=True, og="stone-chimney-restoration-og.jpg",
  title="Chimney Projects In Toronto & The GTA | Northmark Chimney",
  desc="Real Northmark chimney jobs, start to finish: tuckpointing in Toronto, a stone chimney restored in concrete, a gas burner installed. Our own photos.",
  h1="Chimney Projects: Real Jobs In Toronto &amp; The GTA, Start To Finish",
  lead="Three recent Northmark jobs, each written up the way we explain work to the homeowner: what we found, what we did, and the photo of the finished chimney. No stock images — every photo here was taken on the job.",
  cta_h2="Want This For Your Chimney?", cta_lead="Book the free inspection. We photograph what we find and give you the price in writing before any work starts.",
)

if __name__ == "__main__":
    out = os.path.join(ROOT, "projects"); os.makedirs(out, exist_ok=True)
    for p in PROJECTS:
        path = os.path.join(out, p["slug"] + ".html")
        open(path, "w", encoding="utf-8").write(page(p)); print("wrote", path, os.path.getsize(path) // 1024, "KB")
    path = os.path.join(out, "index.html")
    open(path, "w", encoding="utf-8").write(hub(HUB)); print("wrote", path, os.path.getsize(path) // 1024, "KB")
