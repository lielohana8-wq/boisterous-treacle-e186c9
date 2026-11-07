/* Runs automatically on every verified Netlify Forms submission (event-triggered function).
   Copies "inspection-request" submissions into Netlify Blobs so the admin calendar can list
   them without a Netlify API token. */
import { getStore } from "@netlify/blobs";

const FORM = "inspection-request";

export default async (req) => {
  let payload;
  try { payload = (await req.json()).payload; } catch (e) { return new Response("bad body", { status: 400 }); }
  if (!payload || payload.form_name !== FORM) return new Response("ignored");
  const d = payload.data || {};
  const lead = {
    id: payload.id || String(Date.now()),
    created_at: payload.created_at || new Date().toISOString(),
    name: d.name || payload.name || "", phone: d.phone || "", email: d.email || payload.email || "",
    visit_date: d.visit_date || "", visit_time: d.visit_time || "", address: d.address || "", service: d.service || "",
    message: d.message || "", page: d.referrer || payload.referrer || "",
  };
  await getStore("northmark-admin").setJSON("lead/" + lead.id, lead);
  return new Response("ok");
};
