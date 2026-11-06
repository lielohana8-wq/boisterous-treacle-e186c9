/* Shared helpers for the admin functions. Requests from the admin pages carry the GitHub token
   the owner signed in with (same token Decap CMS uses). A request is accepted only if that token
   can push to the site's repository. */
const { getStore, connectLambda } = require("@netlify/blobs");

const REPO = process.env.ADMIN_REPO || "lielohana8-wq/boisterous-treacle-e186c9";
const cache = new Map(); // token -> { user, until }

async function user(event) {
  const h = (event && event.headers) || {};
  const m = String(h.authorization || h.Authorization || "").match(/^Bearer\s+(.+)$/i);
  if (!m) return null;
  const token = m[1].trim();
  const hit = cache.get(token);
  if (hit && hit.until > Date.now()) return hit.user;
  try {
    const r = await fetch("https://api.github.com/repos/" + REPO, { headers: { authorization: "token " + token, accept: "application/vnd.github+json", "user-agent": "northmark-admin" } });
    if (!r.ok) return null;
    const repo = await r.json();
    if (!repo.permissions || !repo.permissions.push) return null;
    const u = { ok: true };
    cache.set(token, { user: u, until: Date.now() + 5 * 60 * 1000 });
    return u;
  } catch (e) { return null; }
}

function json(status, body, extra) {
  return { statusCode: status, headers: Object.assign({ "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }, extra || {}), body: JSON.stringify(body) };
}

function store() { return getStore("northmark-admin"); }

async function siteId(token) {
  if (process.env.SITE_ID) return process.env.SITE_ID;
  if (process.env.NETLIFY_SITE_ID) return process.env.NETLIFY_SITE_ID;
  const r = await fetch("https://api.netlify.com/api/v1/sites?filter=all", { headers: { authorization: "Bearer " + token } });
  if (!r.ok) throw new Error("sites " + r.status);
  const sites = await r.json();
  const s = sites.find(x => (x.custom_domain || "").includes("northmark-chimney")) || sites[0];
  if (!s) throw new Error("no site");
  return s.id;
}

module.exports = { user, json, store, siteId, connectLambda };
