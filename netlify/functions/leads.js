/* Booking requests: the Netlify Forms submissions of "inspection-request", merged with the
   status / note the owner keeps per lead.
   GET   (admin) -> [{ id, created_at, name, phone, visit_date, visit_time, address, service, message, status, note, ... }]
   PATCH (admin) -> { id, status?, note?, visit_date?, visit_time? } updates the owner's notes */
const { user, json, store, siteId, connectLambda } = require("./_auth");
const FORM = "inspection-request";

exports.handler = async (event, context) => {
  connectLambda(event);
  if (!(await user(event))) return json(401, { error: "login required" });
  const s = store();
  if (event.httpMethod === "PATCH") {
    let body; try { body = JSON.parse(event.body || "{}"); } catch (e) { return json(400, { error: "bad json" }); }
    if (!body.id) return json(400, { error: "id" });
    const meta = (await s.get("leads-meta", { type: "json" })) || {};
    const m = meta[body.id] || {};
    for (const k of ["status", "note", "visit_date", "visit_time", "contractor"]) if (k in body) m[k] = String(body[k] || "").slice(0, 500);
    m.updated_at = new Date().toISOString(); meta[body.id] = m;
    await s.setJSON("leads-meta", meta);
    return json(200, m);
  }
  if (event.httpMethod !== "GET") return json(405, { error: "method" });
  const byId = {};
  // 1. Leads saved by submission-created.js (no token needed).
  const { blobs } = await s.list({ prefix: "lead/" });
  const saved = await Promise.all(blobs.map(b => s.get(b.key, { type: "json" })));
  for (const l of saved) if (l && l.id) byId[l.id] = l;
  // 2. Optional: older submissions straight from Netlify Forms, if an API token is configured.
  const token = process.env.NETLIFY_API_TOKEN;
  if (token) {
    try {
      const site = await siteId(token);
      const h = { authorization: "Bearer " + token };
      const forms = await (await fetch(`https://api.netlify.com/api/v1/sites/${site}/forms`, { headers: h })).json();
      const form = (forms || []).find(f => f.name === FORM);
      for (let page = 1; form && page <= 5; page++) {
        const r = await fetch(`https://api.netlify.com/api/v1/forms/${form.id}/submissions?per_page=100&page=${page}`, { headers: h });
        if (!r.ok) break;
        const batch = await r.json();
        for (const x of batch) {
          if (byId[x.id]) continue;
          const d = x.data || {};
          byId[x.id] = { id: x.id, created_at: x.created_at, name: d.name || x.name || "", phone: d.phone || "", email: d.email || "",
            visit_date: d.visit_date || "", visit_time: d.visit_time || "", address: d.address || "", service: d.service || "",
            message: d.message || "", page: d.referrer || x.referrer || "" };
        }
        if (batch.length < 100) break;
      }
    } catch (e) { /* the saved leads are still returned */ }
  }
  const meta = (await s.get("leads-meta", { type: "json" })) || {};
  const out = Object.values(byId)
    .map(l => Object.assign({ status: "new", note: "" }, l, meta[l.id] || {}))
    .sort((x, y) => String(y.created_at).localeCompare(String(x.created_at)));
  return json(200, out);
};
