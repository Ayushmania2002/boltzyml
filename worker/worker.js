/**
 * BoltzYML v2.0 — stateless submission proxy for the hosted Boltz API.
 *
 * Why this exists: api.boltz.bio sends no CORS headers, so a browser on
 * GitHub Pages cannot call it directly. This Worker is a thin passthrough:
 *   browser  ──X-Boltz-Key──▶  Worker  ──X-Api-Key──▶  api.boltz.bio
 * The user's API key travels in a request header, is forwarded once, and is
 * never logged or stored. The Worker also hosts cleaned CIF templates (so the
 * Boltz API can fetch them by URL) and proxies result downloads (the result
 * S3 URLs are likewise CORS-blocked for browsers).
 *
 * Endpoints (all CORS-enabled):
 *   OPTIONS *              → preflight 204
 *   POST /submit           → forward prediction to Boltz; body {input, idempotency_key?, model?}
 *   GET  /status?id=<id>   → forward retrieve
 *   POST /template         → store CIF text in KV (2h TTL), return { url }
 *   GET  /t/<id>           → serve a stored CIF (the URL the Boltz API fetches)
 *   GET  /fetch?url=<u>    → proxy a Boltz/S3 result URL back with CORS
 *
 * Bindings (see wrangler.toml):
 *   TEMPLATES  Workers KV namespace for transient template hosting
 */

const BOLTZ_BASE = "https://api.boltz.bio";
const PRED_PATH = "/compute/v1/predictions/structure-and-binding";
// Hosts the /fetch proxy is allowed to retrieve, so this isn't an open proxy.
const FETCH_ALLOW = [/\.amazonaws\.com$/, /\.boltz\.bio$/, /(^|\.)boltz\.bio$/];

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,X-Boltz-Key",
  "Access-Control-Max-Age": "86400",
};

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS, ...extra },
  });
}

function getKey(request) {
  return request.headers.get("X-Boltz-Key") || "";
}

function randId(n = 20) {
  const b = new Uint8Array(n);
  crypto.getRandomValues(b);
  return [...b].map((x) => "abcdefghijklmnopqrstuvwxyz0123456789"[x % 36]).join("");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    try {
      // ── Submit a prediction ─────────────────────────────────────────────
      if (path === "/submit" && request.method === "POST") {
        const key = getKey(request);
        if (!key) return json({ error: "Missing X-Boltz-Key header." }, 401);
        const payload = await request.json();
        const body = {
          model: payload.model || "boltz-2.1",
          input: payload.input,
        };
        if (payload.idempotency_key) body.idempotency_key = payload.idempotency_key;
        const upstream = await fetch(BOLTZ_BASE + PRED_PATH, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            "X-Api-Key": key,
          },
          body: JSON.stringify(body),
        });
        const text = await upstream.text();
        return new Response(text, {
          status: upstream.status,
          headers: { "Content-Type": "application/json", ...CORS },
        });
      }

      // ── Poll a prediction's status ──────────────────────────────────────
      if (path === "/status" && request.method === "GET") {
        const key = getKey(request);
        if (!key) return json({ error: "Missing X-Boltz-Key header." }, 401);
        const id = url.searchParams.get("id");
        if (!id) return json({ error: "Missing id query param." }, 400);
        const upstream = await fetch(BOLTZ_BASE + PRED_PATH + "/" + encodeURIComponent(id), {
          method: "GET",
          headers: { Accept: "application/json", "X-Api-Key": key },
        });
        const text = await upstream.text();
        return new Response(text, {
          status: upstream.status,
          headers: { "Content-Type": "application/json", ...CORS },
        });
      }

      // ── Host a cleaned CIF template (so Boltz can fetch it by URL) ───────
      if (path === "/template" && request.method === "POST") {
        if (!env.TEMPLATES) {
          return json(
            { error: "No template store bound. Add a KV namespace binding TEMPLATES (see worker/README.md)." },
            501
          );
        }
        const cif = await request.text();
        if (!cif || cif.length < 10) return json({ error: "Empty template body." }, 400);
        if (cif.length > 8 * 1024 * 1024) return json({ error: "Template too large (>8 MB)." }, 413);
        const id = randId();
        // 2-hour TTL: a template is only needed briefly, between submission and
        // the Boltz API fetching it — KV then auto-deletes it.
        await env.TEMPLATES.put("tpl/" + id, cif, { expirationTtl: 7200 });
        // URL must end in .cif so the Boltz API can infer the template format.
        const served = `${url.origin}/t/${id}.cif`;
        return json({ url: served, id });
      }

      // ── Serve a stored template (public; this is what Boltz GETs) ────────
      if (path.startsWith("/t/") && request.method === "GET") {
        if (!env.TEMPLATES) return json({ error: "No template store bound." }, 501);
        const id = path.slice(3).replace(/\.cif$/, "");
        if (!/^[a-z0-9]+$/.test(id)) return json({ error: "Bad template id." }, 400);
        const cif = await env.TEMPLATES.get("tpl/" + id);
        if (cif == null) return json({ error: "Template not found or expired." }, 404);
        return new Response(cif, {
          status: 200,
          headers: {
            "Content-Type": "chemical/x-cif",
            "Content-Disposition": `inline; filename="${id}.cif"`,
            ...CORS,
          },
        });
      }

      // ── Proxy a result file download (S3 URLs are CORS-blocked) ─────────
      if (path === "/fetch" && request.method === "GET") {
        const target = url.searchParams.get("url");
        if (!target) return json({ error: "Missing url query param." }, 400);
        let host;
        try {
          host = new URL(target).hostname;
        } catch {
          return json({ error: "Bad url." }, 400);
        }
        if (!FETCH_ALLOW.some((re) => re.test(host))) {
          return json({ error: "Host not allowed for fetch proxy: " + host }, 403);
        }
        const upstream = await fetch(target, { method: "GET" });
        return new Response(upstream.body, {
          status: upstream.status,
          headers: {
            "Content-Type": upstream.headers.get("Content-Type") || "application/octet-stream",
            ...CORS,
          },
        });
      }

      // ── Page-visit counter (Durable Object; keeps KV free for templates) ─
      //   GET /hit?page=<v1|v2>   → increments that page + the project total,
      //   returns { page, total }. Counts live in a Durable Object, so they
      //   don't consume the KV write budget that template hosting needs.
      if (path === "/hit" && request.method === "GET") {
        if (!env.COUNTER) return json({ page: null, total: null });
        const id = env.COUNTER.idFromName("global");
        const page = (url.searchParams.get("page") || "all").replace(/[^a-z0-9_]/gi, "").slice(0, 16);
        return env.COUNTER.get(id).fetch("https://do/?page=" + page);
      }

      // ── Health check ────────────────────────────────────────────────────
      if (path === "/" || path === "/health") {
        return json({ ok: true, service: "boltzyml-proxy", templateStore: !!env.TEMPLATES, counter: !!env.COUNTER });
      }

      return json({ error: "Not found: " + path }, 404);
    } catch (err) {
      return json({ error: "Proxy error: " + (err && err.message ? err.message : String(err)) }, 502);
    }
  },
};

// Durable Object: a single global visit counter. One instance ("global") holds
// a per-page tally plus a project-wide total. Storage ops here don't count
// against the KV write limit, so page views never starve template hosting.
export class Counter {
  constructor(state) { this.state = state; }
  async fetch(request) {
    const url = new URL(request.url);
    const page = (url.searchParams.get("page") || "all").replace(/[^a-z0-9_]/gi, "").slice(0, 16);
    const s = this.state.storage;
    let total = (await s.get("total")) || 0;
    let pageCount = (await s.get("p:" + page)) || 0;
    total += 1; pageCount += 1;
    await s.put("total", total);
    await s.put("p:" + page, pageCount);
    return new Response(JSON.stringify({ page: pageCount, total }), {
      headers: { "Content-Type": "application/json", ...CORS },
    });
  }
}
