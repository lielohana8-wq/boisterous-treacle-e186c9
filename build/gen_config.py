#!/usr/bin/env python3
"""Generates the Decap CMS config (JSON) for the admin panel from the content files.

Field labels are built from the current text, so the editor sees "Paragraph 2 — The brick itself was..."
rather than an opaque key. Runs at the end of every build.
"""
import glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_DIR = "office-k7m3x9"   # the admin lives at /office-k7m3x9/ — keep this in sync with the folder name
BRANCH = "main"

KIND = {"h1": "Main heading", "h2": "Heading", "h3": "Subheading", "h4": "Small heading", "p": "Paragraph", "li": "List item", "t": "Text", "b": "Bold text",
        "btn": "Button", "q": "Question", "cap": "Photo caption", "dt": "Label", "dd": "Value", "em": "Emphasis", "small": "Note", "lt": "Label"}
SERVICES_HE = {}
ICONS = {"house": "House", "drop": "Water drop", "clock": "Clock", "camera": "Camera", "shield": "Shield", "check": "Checkmark"}
PAGE_LABELS = {"index": "Home page", "about": "About", "our-work": "Our Work", "thanks": "Thank-you page (after the form)", "404": "Page not found (404)",
               "chimney-service-prices-toronto": "Prices", "free-chimney-inspection-toronto": "Landing page — free inspection", "chimney-sweep-toronto": "Chimney Sweep"}


def snippet(v, n=46):
    t = html.unescape(re.sub(r"<[^>]+>", "", str(v))).strip()
    t = re.sub(r"\s+", " ", t)
    return t if len(t) <= n else t[:n].rstrip() + "…"


def text_field(name, v):
    key = re.sub(r"-\d+$", "", name); n = re.search(r"-(\d+)$", name)
    kind = KIND.get(key, key); idx = (" " + n.group(1)) if n else ""
    label = "%s%s — %s" % (kind, idx, snippet(v))
    f = {"name": name, "label": label, "required": False}
    if re.search(r"<[a-zA-Z/]", str(v)) or len(str(v)) > 110:
        f["widget"] = "text"
        if re.search(r"<[a-zA-Z/]", str(v)): f["hint"] = "Basic HTML is fine: <b>, <a href>, <br>"
    else:
        f["widget"] = "string"
    return f


def img_field(name, v):
    n = re.search(r"-(\d+)$", name)
    return {"name": name, "label": "Photo%s — %s" % ((" " + n.group(1)) if n else "", snippet(v.get("alt", ""), 40)), "widget": "object", "collapsed": True, "fields": [
        {"name": "src", "label": "Image file", "widget": "image", "required": False, "allow_multiple": False},
        {"name": "alt", "label": "Image description (alt text, for Google and accessibility)", "widget": "string", "required": False}]}


def section_fields(sec):
    out = []
    for k, v in sec.items():
        if isinstance(v, dict): out.append(img_field(k, v))
        else: out.append(text_field(k, v))
    return out


def section_label(key, sec):
    for k in ("h1", "h2", "h3"):
        if k in sec: return snippet(sec[k], 60)
    for k, v in sec.items():
        if isinstance(v, str): return snippet(v, 60)
    return key


def page_entry(name, data):
    label = PAGE_LABELS.get(name)
    if not label:
        if name.startswith("chimney-services-"): label = "Area: " + name[len("chimney-services-"):].replace("-", " ").title()
        else: label = "Service: " + snippet(data.get("meta", {}).get("title", name), 50).split("|")[0].strip()
    fields = [{"name": "meta", "label": "Google title & description (SEO)", "widget": "object", "collapsed": True, "fields": [
        {"name": "title", "label": "Title in Google (up to 60 characters)", "widget": "string", "required": False},
        {"name": "description", "label": "Description in Google (up to 160 characters)", "widget": "text", "required": False}]}]
    for key, sec in data.items():
        if key == "meta" or not isinstance(sec, dict): continue
        fields.append({"name": key, "label": section_label(key, sec), "widget": "object", "collapsed": True, "fields": section_fields(sec)})
    return {"name": "page-" + name, "label": label, "file": "content/pages/%s.json" % name, "fields": fields}


def project_fields(services):
    svc_opts = [{"label": v["name"], "value": k} for k, v in services.items()]
    img = lambda name, label: {"name": name, "label": label, "widget": "object", "fields": [
        {"name": "src", "label": "Image file", "widget": "image", "allow_multiple": False},
        {"name": "alt", "label": "Image description (alt text)", "widget": "string", "required": False}]}
    return [
        {"name": "title", "label": "Title in Google (title tag)", "widget": "string", "hint": "Up to 60 characters"},
        {"name": "url_slug", "label": "Page address (slug)", "widget": "string", "pattern": ["^[a-z0-9-]+$", "Lowercase letters, digits and hyphens only"], "hint": "e.g. chimney-rebuild-north-york — the page will live at /projects/<slug>"},
        {"name": "published", "label": "Published", "widget": "boolean", "default": True},
        {"name": "order", "label": "Order (1 = first)", "widget": "number", "value_type": "int", "default": 99, "required": False},
        {"name": "date", "label": "Job date", "widget": "datetime", "format": "YYYY-MM-DD", "date_format": "YYYY-MM-DD", "time_format": False, "required": False},
        {"name": "description", "label": "Description in Google", "widget": "text", "hint": "Up to 160 characters"},
        {"name": "tag", "label": "Small tag (e.g. Tuckpointing · Toronto)", "widget": "string"},
        {"name": "crumb", "label": "Short name for the breadcrumb", "widget": "string", "required": False},
        {"name": "h1", "label": "Page heading (H1)", "widget": "string"},
        {"name": "lead", "label": "Opening paragraph", "widget": "text"},
        {"name": "where", "label": "Where (Toronto / Toronto & GTA / North York...)", "widget": "string", "default": "Toronto & GTA"},
        {"name": "service", "label": "Main service", "widget": "select", "options": svc_opts},
        {"name": "related", "label": "Related services (cards at the bottom)", "widget": "select", "multiple": True, "options": svc_opts, "required": False},
        img("hero", "Main photo (portrait, after the work)"),
        {"name": "hero_caption", "label": "Caption for the main photo", "widget": "string", "required": False},
        {"name": "og", "label": "Share image for Facebook/WhatsApp (1200×630, optional)", "widget": "image", "required": False, "allow_multiple": False},
        img("card", "Card photo (landscape 4:3)"),
        {"name": "card_title", "label": "Card title", "widget": "string"},
        {"name": "card_text", "label": "Card text (2 lines)", "widget": "text"},
        {"name": "specs", "label": "Job summary (4 rows: Service / Where / Scope / Result)", "widget": "list", "collapsed": True, "fields": [
            {"name": "label", "label": "Label", "widget": "string"}, {"name": "value", "label": "Value", "widget": "string", "hint": "A link is fine: <a href=\"/chimney-repair-toronto\">Chimney Repair</a>"}]},
        {"name": "job_heading", "label": "Story heading", "widget": "string", "default": "The Job: What We Found, What We Did"},
        {"name": "job_lead", "label": "Story intro line", "widget": "string", "required": False},
        {"name": "found_heading", "label": "'What we found' heading", "widget": "string", "default": "What we found"},
        {"name": "found", "label": "What we found (paragraphs)", "widget": "list", "fields": [{"name": "text", "label": "Paragraph", "widget": "text"}]},
        {"name": "steps", "label": "What we did (steps)", "widget": "list", "fields": [{"name": "title", "label": "Step title", "widget": "string"}, {"name": "text", "label": "Description", "widget": "text"}]},
        {"name": "notice", "label": "Highlighted note box (e.g. about TSSA for gas) — optional", "widget": "text", "required": False},
        {"name": "figs", "label": "Detail photos (up to 3)", "widget": "list", "collapsed": True, "fields": [
            {"name": "src", "label": "Image file", "widget": "image", "allow_multiple": False}, {"name": "alt", "label": "Description (alt text)", "widget": "string", "required": False},
            {"name": "label", "label": "Bold label (e.g. Detail: the joints.)", "widget": "string", "required": False}, {"name": "caption", "label": "Caption", "widget": "string", "required": False}]},
        {"name": "why_heading", "label": "'Why' heading", "widget": "string", "required": False},
        {"name": "why_lead", "label": "'Why' intro line", "widget": "string", "required": False},
        {"name": "pillars", "label": "3 'why' points", "widget": "list", "collapsed": True, "fields": [
            {"name": "icon", "label": "Icon", "widget": "select", "options": [{"label": v, "value": k} for k, v in ICONS.items()], "default": "house"},
            {"name": "title", "label": "Title", "widget": "string"}, {"name": "text", "label": "Text", "widget": "text"}]},
        {"name": "faq_heading", "label": "FAQ heading", "widget": "string", "required": False},
        {"name": "faq", "label": "Questions and answers", "widget": "list", "collapsed": True, "fields": [{"name": "q", "label": "Question", "widget": "string"}, {"name": "a", "label": "Answer", "widget": "text"}]},
        {"name": "cta_heading", "label": "Call-to-action heading (bottom)", "widget": "string", "required": False},
        {"name": "cta_lead", "label": "Call-to-action text", "widget": "text", "required": False},
    ]


def guide_fields(services):
    svc_opts = [{"label": v["name"], "value": k} for k, v in services.items()]
    return [
        {"name": "title", "label": "Title in Google (title tag)", "widget": "string", "hint": "Up to 60 characters"},
        {"name": "url_slug", "label": "Page address (slug)", "widget": "string", "pattern": ["^[a-z0-9-]+$", "Lowercase letters, digits and hyphens only"], "hint": "The page will live at /guides/<slug>"},
        {"name": "published", "label": "Published", "widget": "boolean", "default": True},
        {"name": "order", "label": "Order (1 = first)", "widget": "number", "value_type": "int", "default": 99, "required": False},
        {"name": "date", "label": "Date", "widget": "datetime", "format": "YYYY-MM-DD", "date_format": "YYYY-MM-DD", "time_format": False, "required": False},
        {"name": "description", "label": "Description in Google", "widget": "text", "hint": "Up to 160 characters"},
        {"name": "tag", "label": "Small tag (e.g. Guide · Pricing)", "widget": "string", "default": "Guide"},
        {"name": "h1", "label": "Heading (H1)", "widget": "string"},
        {"name": "lead", "label": "Opening paragraph", "widget": "text"},
        {"name": "hero", "label": "Photo (landscape)", "widget": "object", "fields": [{"name": "src", "label": "Image file", "widget": "image", "allow_multiple": False}, {"name": "alt", "label": "Image description (alt text)", "widget": "string", "required": False}]},
        {"name": "hero_caption", "label": "Photo caption", "widget": "string", "required": False},
        {"name": "service", "label": "Main service", "widget": "select", "options": svc_opts},
        {"name": "related", "label": "Related services", "widget": "select", "multiple": True, "options": svc_opts, "required": False},
        {"name": "sections", "label": "Sections", "widget": "list", "fields": [{"name": "h2", "label": "Heading", "widget": "string"}, {"name": "body", "label": "Text (HTML: <p>, <ul><li>, <b>, <a href>)", "widget": "text"}]},
        {"name": "faq_heading", "label": "FAQ heading", "widget": "string", "required": False},
        {"name": "faq", "label": "Questions and answers", "widget": "list", "collapsed": True, "fields": [{"name": "q", "label": "Question", "widget": "string"}, {"name": "a", "label": "Answer", "widget": "text"}]},
        {"name": "cta_heading", "label": "Call-to-action heading (bottom)", "widget": "string", "required": False},
        {"name": "cta_lead", "label": "Call-to-action text", "widget": "text", "required": False},
    ]


def site_fields(site):
    chrome = site.get("chrome", {})
    return [
        {"name": "phone", "label": "Phone (as displayed)", "widget": "string"},
        {"name": "phone_tel", "label": "Phone for dialing (+1 then 10 digits)", "widget": "string", "pattern": ["^\\+1\\d{10}$", "Format: +12895145267"]},
        {"name": "whatsapp", "label": "WhatsApp (digits only, starting with 1)", "widget": "string", "pattern": ["^1\\d{10}$", "Format: 14164502859"]},
        {"name": "email", "label": "Email", "widget": "string"},
        {"name": "hours", "label": "Hours (e.g. 7:00–22:00)", "widget": "string"},
        {"name": "google_profile", "label": "Google Business Profile link", "widget": "string"},
        {"name": "count_chimneys", "label": "Chimneys counter (e.g. 2,000+)", "widget": "string"},
        {"name": "years_text", "label": "Years in business (e.g. 3+ years)", "widget": "string"},
        {"name": "offer_price", "label": "Offer price (e.g. $200)", "widget": "string"},
        {"name": "projects_hub", "label": "Projects page (/projects/)", "widget": "object", "collapsed": True, "fields": [
            {"name": "title", "label": "Title in Google", "widget": "string"}, {"name": "description", "label": "Description in Google", "widget": "text"},
            {"name": "h1", "label": "Heading (H1)", "widget": "string"}, {"name": "lead", "label": "Opening paragraph", "widget": "text"},
            {"name": "hero_project", "label": "Which project in the main photo (slug)", "widget": "string", "required": False}]},
        {"name": "chrome", "label": "Footer and popup (on every page)", "widget": "object", "collapsed": True, "fields": [
            {"name": k, "label": {"footer": "Footer", "popup": "Offer popup"}.get(k, k), "widget": "object", "collapsed": True, "fields": section_fields(v)} for k, v in chrome.items()]},
    ]


def main():
    os.chdir(ROOT)
    site = json.load(open("content/site.json", encoding="utf-8"))
    shared = json.load(open("content/shared.json", encoding="utf-8"))
    services = json.load(open("content/services.json", encoding="utf-8"))
    pages = []
    order = ["index", "our-work", "about", "chimney-service-prices-toronto", "free-chimney-inspection-toronto"]
    names = sorted(os.path.basename(f)[:-5] for f in glob.glob("content/pages/*.json"))
    names = [n for n in order if n in names] + [n for n in names if n not in order and not n.startswith("chimney-services-")] + [n for n in names if n.startswith("chimney-services-")]
    for n in names:
        pages.append(page_entry(n, json.load(open("content/pages/%s.json" % n, encoding="utf-8"))))
    SHARED_HE = {"trust": "Trust strip (WETT, 2,000+, $0...)", "promise": "Promise band", "offer-form": "$200 offer block", "trust2": "What Every Visit Includes",
                 "check": "19-Point Chimney Check", "prices": "What It Costs (prices)", "reviews": "Check Us Before You Book (reviews)"}
    shared_fields = [{"name": k, "label": SHARED_HE.get(k, k), "widget": "object", "collapsed": True, "fields": section_fields(v)} for k, v in shared.items()]
    config = {
        "backend": {"name": "github", "repo": "lielohana8-wq/boisterous-treacle-e186c9", "base_url": "https://api.netlify.com", "branch": BRANCH, "commit_messages": {"create": "Content: add {{collection}} “{{slug}}”", "update": "Content: update {{collection}} “{{slug}}”", "delete": "Content: delete {{collection}} “{{slug}}”", "uploadMedia": "Photo: {{path}}", "deleteMedia": "Photo removed: {{path}}"}},
        "locale": "en",
        "site_url": "https://northmark-chimney.ca", "display_url": "https://northmark-chimney.ca", "logo_url": "/logo.png",
        "media_folder": "uploads", "public_folder": "/uploads",
        "editor": {"preview": False},
        "collections": [
            {"name": "projects", "label": "Jobs / Projects", "label_singular": "Job", "folder": "content/projects", "create": True, "delete": True,
             "extension": "json", "format": "json", "slug": "{{fields.url_slug}}", "identifier_field": "h1", "summary": "{{h1}}",
             "sortable_fields": ["order", "date", "h1"], "editor": {"preview": False}, "fields": project_fields(services)},
            {"name": "guides", "label": "Guides (articles)", "label_singular": "Guide", "folder": "content/guides", "create": True, "delete": True,
             "extension": "json", "format": "json", "slug": "{{fields.url_slug}}", "identifier_field": "h1", "summary": "{{h1}}", "sortable_fields": ["order", "date", "h1"], "editor": {"preview": False},
             "fields": guide_fields(services)},
            {"name": "settings", "label": "Business details & settings", "editor": {"preview": False}, "files": [
                {"name": "site", "label": "Business details (phone, email, hours, offer)", "file": "content/site.json", "fields": site_fields(site)},
                {"name": "shared", "label": "Blocks that appear on many pages", "file": "content/shared.json", "fields": shared_fields}]},
            {"name": "pages", "label": "Site pages (texts & photos)", "editor": {"preview": False}, "files": pages},
        ]}
    os.makedirs(ADMIN_DIR, exist_ok=True)
    json.dump(config, open(os.path.join(ADMIN_DIR, "config.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("admin config: %d pages, %d bytes" % (len(pages), os.path.getsize(os.path.join(ADMIN_DIR, "config.json"))))


if __name__ == "__main__":
    main()
