/* SEO hook: applies /seo.json (maintained by the SEO engine) to this page — title, description, JSON-LD, image alt text. */
(function () {
  var path = location.pathname.replace(/\/index\.html$/, "/").replace(/\.html$/, "").replace(/\/+$/, "") || "/";
  fetch("/seo.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
    var p = data && data.pages && data.pages[path]; if (!p) return;
    if (p.title) document.title = p.title;
    if (p.description) { var m = document.querySelector('meta[name="description"]'); if (!m) { m = document.createElement("meta"); m.name = "description"; document.head.appendChild(m); } m.content = p.description; }
    if (p.schema && p.schema.length) { var s = document.createElement("script"); s.type = "application/ld+json"; s.textContent = JSON.stringify(p.schema.length === 1 ? p.schema[0] : p.schema); document.head.appendChild(s); }
    if (p.images) Object.keys(p.images).forEach(function (src) { document.querySelectorAll('img[src="' + src + '"]').forEach(function (img) { img.alt = p.images[src]; }); });
  }).catch(function () {});
})();
