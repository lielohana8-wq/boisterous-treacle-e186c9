#!/usr/bin/env python3
"""ONE-OFF migration: turns the hand-built HTML pages into CMS templates + content JSON.

For every page it
  * swaps the generated case-study blocks for {{cards:...}} placeholders,
  * swaps business facts (phone, email, hours, offer price...) for {{site.*}} tokens,
  * marks every editable text element with data-cms="section.key" and every photo with
    data-cms-img="section.key", and writes the current values to content/pages/<page>.json.
Sections whose markup is identical on every page (trust strip, $200 offer, prices, 19-point
check...) are keyed as shared.* and live once in content/shared.json; the footer and the
popup live in content/site.json under "chrome".

Run once from the repo root: python3 build/annotate.py   (writes templates/ and content/)
After that, build/build.py is the only thing that writes HTML.
"""
import html, json, os, re, sys, hashlib
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
GENERATED = {"projects.html", "chimney-tuckpointing-toronto.html", "stone-chimney-restoration.html", "gas-fireplace-burner-installation.html"}
PAGES = sorted(f for f in os.listdir(ROOT) if f.endswith(".html") and f not in GENERATED)

TOKENS = [  # literal in the HTML -> site.json key
    ("(289) 514-5267", "phone"), ("+12895145267", "phone_tel"), ("14164502859", "whatsapp"),
    ("Northmarkchimney@gmail.com", "email"), ("7:00–22:00", "hours"),
    ("https://share.google/HRH623MMM2RBJ27UI", "google_profile"),
    ("2,000+", "count_chimneys"), ("3+ years", "years_text"), ("$200", "offer_price"),
]
SITE = {"phone": "(289) 514-5267", "phone_tel": "+12895145267", "whatsapp": "14164502859",
        "email": "Northmarkchimney@gmail.com", "hours": "7:00–22:00",
        "google_profile": "https://share.google/HRH623MMM2RBJ27UI",
        "count_chimneys": "2,000+", "years_text": "3+ years", "offer_price": "$200"}

TEXT_TAGS = {"h1", "h2", "h3", "h4", "p", "li", "dt", "dd", "summary", "figcaption", "span", "b", "em", "strong", "small", "a", "legend"}
BLOCK_TAGS = {"div", "ul", "ol", "li", "p", "h1", "h2", "h3", "h4", "figure", "img", "svg", "form", "input", "select", "button",
              "table", "section", "nav", "dl", "dt", "dd", "details", "summary", "label", "fieldset", "textarea", "picture", "iframe", "video", "article", "aside", "header", "footer", "main"}
SKIP_SUBTREE = {"form", "nav", "script", "style", "noscript", "svg", "select", "button", "iframe", "video", "template"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SHARED_SECTIONS = {"trust", "promise", "offer-form", "prices", "check", "trust2", "reviews"}  # verified identical across pages (trust2 = "What Every Visit Includes")


class Walker(HTMLParser):
    """Records byte spans of every element so we can rewrite the markup in place."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.lines = [0]
        for i, ch in enumerate(text):
            if ch == "\n": self.lines.append(i + 1)
        self.stack = []; self.elements = []
        self.feed(text); self.close()
    def off(self):
        l, c = self.getpos(); return self.lines[l - 1] + c
    def handle_starttag(self, tag, attrs):
        start = self.off(); raw = self.get_starttag_text(); el = {"tag": tag, "attrs": attrs, "start": start, "open_end": start + len(raw),
                                                                "parent": self.stack[-1] if self.stack else None, "depth": len(self.stack)}
        self.elements.append(el)
        if tag in VOID or raw.endswith("/>"): el["end"] = el["close_end"] = el["open_end"]; return
        self.stack.append(el)
    def handle_startendtag(self, tag, attrs):
        start = self.off(); raw = self.get_starttag_text()
        self.elements.append({"tag": tag, "attrs": attrs, "start": start, "open_end": start + len(raw), "end": start + len(raw), "close_end": start + len(raw),
                              "parent": self.stack[-1] if self.stack else None, "depth": len(self.stack)})
    def handle_endtag(self, tag):
        pos = self.off()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                for el in self.stack[i:]:
                    el["end"] = pos; el["close_end"] = pos
                el = self.stack[i]; el["close_end"] = self.text.find(">", pos) + 1
                del self.stack[i:]; return


def attr(el, name):
    for k, v in el["attrs"]:
        if k == name: return v or ""
    return None


def inner(text, el): return text[el["open_end"]:el["end"]]


def strip_tags(s): return re.sub(r"<[^>]+>", "", s)


def is_leaf_text(text, el):
    s = inner(text, el)
    if re.search(r"<(" + "|".join(BLOCK_TAGS) + r")\b", s): return False
    t = html.unescape(strip_tags(s)).strip()
    return len(t) >= 1 and t not in ("+", "–", "—", "&times;", "×")


def replace_blocks(h, page):
    """Generated case-study blocks become placeholders so the build regenerates them from the projects."""
    if 'data-cs="home"' in h:
        i = h.index('<div class="head" style="margin-top:56px" data-cs="home">'); j = h.index('<div class="more-row">', i)
        h = h[:i] + "{{cards:home}}" + h[j:]
    if 'id="cases"' in h:
        i = h.index('<section class="sec" id="cases"'); j = h.index("</section>", i) + len("</section>")
        h = h[:i] + "{{cards:ourwork}}" + h[j:]
    if 'data-cs="svc"' in h:
        i = h.index('<div class="head" style="margin-top:56px" data-cs="svc">'); j = h.index('<div class="more-row">', i)
        h = h[:i] + "{{cards:svc}}" + h[j:]
    h = re.sub(r'<p class="ask" data-cs="area">.*?</p>', "{{project_link}}", h, count=1, flags=re.S)
    return h


def tokenize(h):
    for lit, key in TOKENS:
        h = h.replace(lit, "{{site.%s}}" % key)
    return h


def section_name(el, text):
    sid = attr(el, "id"); al = attr(el, "aria-labelledby"); cls = (attr(el, "class") or "").split()
    for cand in [sid, al.replace("-h", "") if al else None] + cls:
        if cand and cand not in ("sec", "stone", "navy", "wrap"): return re.sub(r"[^a-z0-9]+", "-", cand.lower()).strip("-")
    return "sec"


INDEX_CHROME = {}
def chrome_hash(h, el): return hashlib.md5(re.sub(r' aria-current="page"', "", h[el["start"]:el["close_end"]]).encode()).hexdigest()
def same_as_index(h, el, what):
    if what not in INDEX_CHROME:
        ih = tokenize(replace_blocks(open("index.html", encoding="utf-8").read(), "index.html")); iw = Walker(ih)
        INDEX_CHROME["footer"] = chrome_hash(ih, next(e for e in iw.elements if e["tag"] == "footer"))
        INDEX_CHROME["popup"] = chrome_hash(ih, next(e for e in iw.elements if attr(e, "id") == "pmwrap"))
    return chrome_hash(h, el) == INDEX_CHROME[what]


def annotate(page):
    h = open(page, encoding="utf-8").read()
    h = tokenize(replace_blocks(h, page))
    w = Walker(h)
    main = next((e for e in w.elements if e["tag"] == "main"), None)
    footer = next((e for e in w.elements if e["tag"] == "footer"), None)
    popup = next((e for e in w.elements if attr(e, "id") == "pmwrap"), None)
    # top-level containers to key: sections inside main (+ hero etc.), footer, popup
    groups = []
    if main:
        secs = [e for e in w.elements if e["parent"] is main and e["tag"] in ("section", "div", "article")]
        names = {}
        for s in secs:
            n = section_name(s, h); names[n] = names.get(n, 0) + 1
            if names[n] > 1: n = f"{n}{names[n]}"
            s["key"] = ("shared." + n) if n in SHARED_SECTIONS else n
            groups.append(s)
    if footer: footer["key"] = "chrome.footer" if same_as_index(h, footer, "footer") else "footer"; groups.append(footer)
    if popup: popup["key"] = "chrome.popup" if same_as_index(h, popup, "popup") else "popup"; groups.append(popup)

    chosen = []  # (el, key, kind)
    for g in groups:
        counters = {}
        inside = [e for e in w.elements if g["start"] < e["start"] < g["end"]]
        skip_until = []  # end offsets of subtrees to skip
        for e in inside:
            if any(e["start"] < s for s in skip_until): continue
            if e["tag"] in SKIP_SUBTREE: skip_until.append(e["end"]); continue
            if e["tag"] == "img":
                if "/logo.png" in (attr(e, "src") or ""): continue
                counters["img"] = counters.get("img", 0) + 1
                chosen.append((e, f'{g["key"]}.img' + ("" if counters["img"] == 1 else f'-{counters["img"]}'), "img")); continue
            if e["tag"] in TEXT_TAGS and is_leaf_text(h, e):
                cls = attr(e, "class") or ""
                if e["tag"] == "a" and not re.search(r"\b(btn|go|xl|gbp|big|ph|fphone|map-load)\b", cls): continue
                if e["tag"] == "span" and re.search(r"\b(sr|hide)\b", cls): continue
                if attr(e, "aria-hidden") == "true": continue
                name = {"h1": "h1", "h2": "h2", "h3": "h3", "h4": "h4", "p": "p", "li": "li", "dt": "dt", "dd": "dd", "summary": "q", "figcaption": "cap",
                        "span": "t", "b": "b", "em": "em", "strong": "b", "small": "small", "a": "btn", "legend": "lt"}[e["tag"]]
                counters[name] = counters.get(name, 0) + 1
                key = f'{g["key"]}.{name}' + ("" if counters[name] == 1 else f"-{counters[name]}")
                chosen.append((e, key, "text")); skip_until.append(e["end"])
    # title / description
    values = {}
    def put(key, val):
        d = values; parts = key.split(".")
        for p in parts[:-1]: d = d.setdefault(p, {})
        d[parts[-1]] = val
    t = re.search(r"<title>(.*?)</title>", h, re.S); d = re.search(r'<meta name="description" content="(.*?)"', h)
    put("meta.title", html.unescape(t.group(1)) if t else ""); put("meta.description", html.unescape(d.group(1)) if d else "")
    # rewrite from the end so offsets stay valid
    edits = []
    for e, key, kind in chosen:
        if kind == "img":
            src = attr(e, "src") or ""; alt = html.unescape(attr(e, "alt") or "")
            put(key, {"src": src, "alt": alt})
            tag = h[e["start"]:e["open_end"]]
            edits.append((e["start"], e["open_end"], tag[:4] + f' data-cms-img="{key}" data-orig="{src}"' + tag[4:]))
        else:
            raw = inner(h, e)
            val = html.unescape(raw) if "<" not in raw else raw
            put(key, val)
            tag = h[e["start"]:e["open_end"]]
            edits.append((e["start"], e["open_end"], tag[:len(e["tag"]) + 1] + f' data-cms="{key}"' + tag[len(e["tag"]) + 1:]))
            edits.append((e["open_end"], e["end"], "{{" + key + "}}"))
    for a, b, rep in sorted(edits, key=lambda x: -x[0]):
        h = h[:a] + rep + h[b:]
    # head substitutions last: they change the length of the text ahead of every span above
    h = re.sub(r"<title>.*?</title>", "<title>{{meta.title}}</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content=".*?"', '<meta name="description" content="{{meta.description}}"', h, count=1)
    h = re.sub(r'<meta property="og:title" content=".*?"', '<meta property="og:title" content="{{meta.title}}"', h, count=1)
    h = re.sub(r'<meta property="og:description" content=".*?"', '<meta property="og:description" content="{{meta.description}}"', h, count=1)
    return h, values


def main():
    os.makedirs("templates", exist_ok=True); os.makedirs("content/pages", exist_ok=True)
    shared, chrome = {}, {}
    for page in PAGES:
        tpl, values = annotate(page)
        name = page[:-5]
        open(os.path.join("templates", page), "w", encoding="utf-8").write(tpl)
        sh = values.pop("shared", {}); ch = values.pop("chrome", {})
        for k, v in sh.items(): shared.setdefault(k, v)
        if page == "index.html": chrome = ch
        json.dump(values, open(os.path.join("content/pages", name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{page:48s} {sum(len(v) for v in values.values() if isinstance(v, dict)):4d} fields")
    site = json.load(open("content/site.json", encoding="utf-8")) if os.path.exists("content/site.json") else {}
    for k, v in SITE.items(): site.setdefault(k, v)
    site["chrome"] = chrome
    json.dump(site, open("content/site.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(shared, open("content/shared.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("shared sections:", list(shared))


if __name__ == "__main__":
    main()
