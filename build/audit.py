#!/usr/bin/env python3
"""Static SEO audit of every HTML page. Run from the repo root: python3 tools/seo-audit.py"""
import glob, json, os, re, html as H
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
pages = sorted(glob.glob("*.html"))  # built output at the repo root
PROJECT_SLUGS = {"chimney-tuckpointing-toronto", "stone-chimney-restoration", "gas-fireplace-burner-installation"}
titles, descs, h1s, issues = {}, {}, {}, []
existing = set(os.path.splitext(p)[0] for p in pages)
redirects = open("_redirects").read()
sitemap = open("sitemap.xml").read()

def url_of(p):
    if p == "index.html": return "/"
    if p == "projects.html": return "/projects/"
    if p[:-5] in PROJECT_SLUGS: return "/projects/" + p[:-5]
    return "/" + p[:-5]

for p in pages:
    s = open(p, encoding="utf-8").read()
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    t = re.search(r"<title>(.*?)</title>", s)
    d = re.search(r'name="description" content="(.*?)"', s)
    c = re.search(r'rel="canonical" href="(.*?)"', s)
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S)
    t = H.unescape(t.group(1)) if t else ""; d = H.unescape(d.group(1)) if d else ""
    titles.setdefault(t, []).append(p); descs.setdefault(d, []).append(p)
    h1t = H.unescape(re.sub("<[^>]+>", "", h1[0])).strip() if h1 else ""
    h1s.setdefault(h1t, []).append(p)
    noindex = 'name="robots" content="noindex' in s
    if not t: issues.append((p, "no title"))
    elif len(t) > 62: issues.append((p, f"title {len(t)} chars: {t}"))
    if not d: issues.append((p, "no description"))
    elif len(d) > 165 or len(d) < 70: issues.append((p, f"description {len(d)} chars"))
    if len(h1) != 1: issues.append((p, f"{len(h1)} h1"))
    if not c: issues.append((p, "no canonical"))
    elif c.group(1) != "https://northmark-chimney.ca" + url_of(p) and not noindex: issues.append((p, f"canonical {c.group(1)} != {url_of(p)}"))
    if 'property="og:image"' not in s: issues.append((p, "no og:image"))
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, flags=re.S):
        try: json.loads(m.group(1))
        except Exception as e: issues.append((p, f"bad JSON-LD: {e}"))
    for m in re.finditer(r"<img\b[^>]*>", body):
        tag = m.group(0)
        if 'alt=' not in tag: issues.append((p, "img without alt: " + tag[:80]))
        if 'loading="lazy"' not in tag and 'fetchpriority="high"' not in tag and 'class="plate"' not in tag and "/logo.png" not in tag: issues.append((p, "img not lazy/priority: " + re.search(r'src="([^"]+)"', tag).group(1)))
        if 'width=' not in tag or 'height=' not in tag: issues.append((p, "img without dimensions: " + re.search(r'src="([^"]+)"', tag).group(1)))
    for src in set(re.findall(r'(?:src|href)="(/[^"#?]+\.(?:jpg|png|js|css|json|mp4|webp|svg))"', s)) | set(re.findall(r'(/[^ ,"]+\.jpg) \d+w', s)):
        if not os.path.exists(src.lstrip("/")): issues.append((p, "missing asset " + src))
    for href in set(re.findall(r'href="(/[^"#?]*)"', body)):
        tgt = href.rstrip("/") or "/"
        if tgt == "/" or tgt == "/projects" or tgt[len("/projects/"):] in PROJECT_SLUGS and tgt.startswith("/projects/"): continue
        if tgt.lstrip("/") not in existing and not os.path.exists(tgt.lstrip("/")) and not os.path.exists(tgt.lstrip("/") + "/index.html") and not re.search(r"\.\w+$", tgt):
            issues.append((p, "dead internal link " + href))
    if re.search(r"\(416\) 000-0000", body) is None and "000-0000" in body: issues.append((p, "odd placeholder"))
    for ph in set(re.findall(r"\(\d{3}\) \d{3}-\d{4}", body)) - {"(289) 514-5267", "(416) 000-0000"}: issues.append((p, "stray phone " + ph))
    if not noindex and f"<loc>https://northmark-chimney.ca{url_of(p)}</loc>" not in sitemap and p not in ("404.html", "thanks.html"): issues.append((p, "not in sitemap"))
    if p not in ("index.html", "404.html") and f"{url_of(p).rstrip('/') or '/'}  /{p}  200" not in redirects: issues.append((p, "no pretty-url redirect"))
    words = len(re.sub("<[^>]+>", " ", body).split())
    if words < 500: issues.append((p, f"thin: {words} words"))

for k, v in titles.items():
    if len(v) > 1: issues.append(("dup title", f"{k!r}: {v}"))
for k, v in descs.items():
    if len(v) > 1: issues.append(("dup description", f"{k[:60]!r}: {v}"))
for k, v in h1s.items():
    if len(v) > 1: issues.append(("dup h1", f"{k!r}: {v}"))
for p, m in issues: print(f"{p:55s} {m}")
print(f"\n{len(pages)} pages, {len(issues)} findings")
