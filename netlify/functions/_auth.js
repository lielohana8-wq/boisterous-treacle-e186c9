/* Shared helpers for the admin functions. Requests from the admin pages carry the Netlify
   Identity JWT; Netlify verifies it and exposes the user on context.clientContext.user. */
const { getStore, connectLambda } = require("@netlify/blobs");

function user(context) {
  const u = context && context.clientContext && context.clientContext.user;
  return u && u.email ? u : null;
}

function json(status, body, extra) {
  return { statusCode: status, headers: Object.assign({ "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }, extra || {}), body: JSON.stringify(body) };
}

function store() { return getStore({ name: "northmark-admin", consistency: "strong" }); }

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
