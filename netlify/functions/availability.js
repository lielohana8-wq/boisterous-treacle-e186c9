/* Which days / time windows the booking form may offer.
   GET  (public)  -> { blocked: { "2026-11-12": ["all"] | ["Morning (7:00 – 11:00)", ...] }, closed_weekdays: [6], max_days: 60, lead_days: 0 }
   PUT  (admin)   -> replaces the whole object */
const { user, json, store, connectLambda } = require("./_auth");
const DEFAULT = { blocked: {}, closed_weekdays: [], max_days: 60, lead_days: 0 };

exports.handler = async (event, context) => {
  connectLambda(event);
  const s = store();
  if (event.httpMethod === "GET") {
    const v = (await s.get("availability", { type: "json" })) || DEFAULT;
    return json(200, Object.assign({}, DEFAULT, v), { "cache-control": "public, max-age=60", "access-control-allow-origin": "*" });
  }
  if (event.httpMethod === "PUT") {
    if (!user(context)) return json(401, { error: "login required" });
    let body; try { body = JSON.parse(event.body || "{}"); } catch (e) { return json(400, { error: "bad json" }); }
    const clean = {
      blocked: {}, closed_weekdays: (body.closed_weekdays || []).map(Number).filter(n => n >= 0 && n <= 6),
      max_days: Math.min(365, Math.max(1, parseInt(body.max_days, 10) || 60)), lead_days: Math.min(30, Math.max(0, parseInt(body.lead_days, 10) || 0)),
    };
    for (const [day, wins] of Object.entries(body.blocked || {})) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Array.isArray(wins) || !wins.length) continue;
      clean.blocked[day] = wins.map(String).slice(0, 10);
    }
    await s.setJSON("availability", clean);
    return json(200, clean);
  }
  return json(405, { error: "method" });
};
