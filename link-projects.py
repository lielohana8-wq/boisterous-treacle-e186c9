#!/usr/bin/env python3
"""Links the /projects/ case studies from the rest of the site. Idempotent: re-running is safe.

- footer "Northmark" column on every page gets a Projects link
- home #work, our-work and the related service pages get case-study cards (+ the card CSS)
- _redirects, sitemap.xml and llms.txt learn the new URLs
"""
import os, re, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("bp", os.path.join(ROOT, "tools", "build-projects.py"))
bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)
P = {q["slug"]: q for q in bp.PROJECTS}
TODAY = bp.TODAY
MARK = "/* project case studies */"

def rw(name, fn):
    path = os.path.join(ROOT, name); s = open(path, encoding="utf-8").read(); t = fn(s)
    if t != s: open(path, "w", encoding="utf-8").write(t); print("updated", name)

def add_css(s):
    """Append the card CSS, or refresh it in place if the page already carries a copy."""
    if MARK in s:
        i = s.index("\n" + MARK); j = s.index("</style>", i)
        return s[:i] + bp.EXTRA_CSS + s[j:]
    return s.replace("</style>", bp.EXTRA_CSS + "</style>", 1)

def cards(slugs, feat_first=False):
    out = ""
    for i, sl in enumerate(slugs):
        out += bp.cs_card(P[sl], feat=(feat_first and i == 0))
    return out

# 1. footer link everywhere
FOOT_OLD = '<p class="h4">Northmark</p><ul><li><a href="/our-work">Our Work</a></li>'
FOOT_NEW = FOOT_OLD + '<li><a href="/projects/">Project Case Studies</a></li>'
for f in sorted(os.listdir(ROOT)) + ["projects/" + x for x in sorted(os.listdir(os.path.join(ROOT, "projects")))]:
    if f.endswith(".html"):
        rw(f, lambda s: s if '/projects/">Project Case Studies' in s else s.replace(FOOT_OLD, FOOT_NEW))

# 2. home: case-study cards inside #work, before the more-row
def home(s):
    if 'data-cs="home"' in s: return add_css(s)
    s = add_css(s)
    block = ('<div class="head" style="margin-top:56px" data-cs="home"><div><h3 style="font-size:clamp(22px,2.4vw,28px)">Three Jobs, Start To Finish</h3></div>'
             '<p class="lead">What we found, what we did and the finished photo — written up the way we explain work to the homeowner.</p></div>'
             '<div class="cs-grid">' + cards(["chimney-tuckpointing-toronto", "stone-chimney-restoration", "gas-fireplace-burner-installation"]) + '</div>')
    i = s.index('id="work"'); j = s.index('<div class="more-row">', i)
    s = s[:j] + block + s[j:]
    s = s.replace('<div class="more-row"><p>More before-and-after photos and recent jobs by area.</p><a class="btn" href="/our-work">See all our work</a>',
                  '<div class="more-row"><p>More before-and-after photos, recent jobs by area and all project case studies.</p><div class="acts2" style="margin-top:0"><a class="btn" href="/our-work">See all our work</a><a class="btn line-w" href="/projects/">All case studies</a></div>', 1)
    return s
rw("index.html", home)

# 3. our-work: a case-study section right after the trust strip
def ourwork(s):
    if 'id="cases"' in s: return add_css(s)
    s = add_css(s)
    sec = ('<section class="sec" id="cases" aria-labelledby="cs-h"><div class="wrap"><div class="head"><div><h2 id="cs-h">Project Case Studies</h2></div>'
           '<p class="lead">Three recent jobs written up start to finish: what we found, what we did, and the photo of the finished chimney.</p></div>'
           '<div class="cs-grid hub">' + cards(["chimney-tuckpointing-toronto", "stone-chimney-restoration", "gas-fireplace-burner-installation"], feat_first=True) + '</div>'
           '<div class="more-row"><p>Every case study ends with the same offer: a free inspection with photos and the price in writing.</p><a class="btn line" href="/projects/">All case studies</a></div></div></section>')
    i = s.index('<section class="sec navy" aria-labelledby="ba-h">')
    return s[:i] + sec + s[i:]
rw("our-work.html", ourwork)

# 4. service pages: cards in the proof section
REL = {"chimney-masonry-repair-toronto.html": ["chimney-tuckpointing-toronto", "stone-chimney-restoration"],
       "chimney-flashing-toronto.html": ["chimney-tuckpointing-toronto", "stone-chimney-restoration"],
       "chimney-repair-toronto.html": ["stone-chimney-restoration", "chimney-tuckpointing-toronto"],
       "chimney-cap-installation-toronto.html": ["stone-chimney-restoration"],
       "fireplace-repair-toronto.html": ["gas-fireplace-burner-installation"],
       "chimney-inspection-toronto.html": ["gas-fireplace-burner-installation", "stone-chimney-restoration"],
       "chimney-services-north-york.html": [], }
def svc(slugs):
    def fn(s):
        if 'data-cs="svc"' in s: return add_css(s)
        s = add_css(s)
        n = len(slugs)
        block = ('<div class="head" style="margin-top:56px" data-cs="svc"><div><h3 style="font-size:clamp(22px,2.4vw,28px);color:#fff">Case ' + ("Study" if n == 1 else "Studies") + ': This Work, Start To Finish</h3></div>'
                 '<p class="lead">What we found, what we did, and the finished photo.</p></div>'
                 '<div class="cs-grid' + (" hub" if n == 1 else " two") + '">' + cards(slugs, feat_first=(n == 1)) + '</div>')
        i = s.index('aria-labelledby="proof-h"'); j = s.index('<div class="more-row">', i)
        return s[:j] + block + s[j:]
    return fn
for f, slugs in REL.items():
    if slugs: rw(f, svc(slugs))

# 5. redirects
def redirects(s):
    lines = [f"/projects/{q['slug']}  /projects/{q['slug']}.html  200" for q in bp.PROJECTS]
    add = [l for l in lines if l not in s]
    if not add: return s
    i = s.index("/*  /404.html")
    return s[:i] + "\n".join(add) + "\n" + s[i:]
rw("_redirects", redirects)

# 6. sitemap
def sitemap(s):
    urls = ["https://northmark-chimney.ca/projects/"] + [bp.SITE + q["url"] for q in bp.PROJECTS]
    add = "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>\n" for u in urls if f"<loc>{u}</loc>" not in s)
    s = s.replace("</urlset>", add + "</urlset>")
    # pages touched today
    for path in ["/", "/our-work", "/chimney-masonry-repair-toronto", "/chimney-flashing-toronto", "/chimney-repair-toronto", "/chimney-cap-installation-toronto", "/fireplace-repair-toronto", "/chimney-inspection-toronto"]:
        s = re.sub(rf"(<loc>https://northmark-chimney\.ca{re.escape(path)}</loc><lastmod>)[^<]+", rf"\g<1>{TODAY}", s)
    return s
rw("sitemap.xml", sitemap)

# 7. llms.txt
def llms(s):
    if "## Projects" in s: return s
    block = ("\n## Projects (case studies, our own photos)\n"
             "- [Chimney Projects In Toronto & The GTA](https://northmark-chimney.ca/projects/)\n"
             + "".join(f"- [{re.sub('<[^>]+>', '', q['h1'])}]({bp.SITE}{q['url']})\n" for q in bp.PROJECTS))
    return s.rstrip("\n") + "\n" + block
rw("llms.txt", llms)
