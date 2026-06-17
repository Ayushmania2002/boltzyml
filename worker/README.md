# BoltzYML v2.0 — submission proxy

A tiny **stateless** Cloudflare Worker that lets the browser app submit jobs to
the hosted Boltz API. It exists for one reason: `api.boltz.bio` sends no CORS
headers, so a static site (GitHub Pages) cannot call it directly.

```
browser  ──X-Boltz-Key──▶  Worker  ──X-Api-Key──▶  api.boltz.bio
```

Your Boltz API key travels in a request header, is forwarded to Boltz once, and
is **never logged or stored**. The Worker also hosts cleaned CIF templates (so
Boltz can fetch them by URL) and proxies result downloads.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/submit` | Forward a prediction. Body `{ input, idempotency_key?, model? }`, header `X-Boltz-Key`. |
| `POST` | `/estimate` | Forward to Boltz `estimate-cost`. Body `{ input, model? }`, header `X-Boltz-Key`; returns the USD estimate. |
| `GET`  | `/status?id=<id>` | Forward a status/retrieve call. |
| `POST` | `/template` | Store a cleaned CIF (raw body) in a Durable Object, returns `{ url }`. |
| `GET`  | `/t/<id>` | Serve a stored template — this is the URL Boltz fetches (public). |
| `GET`  | `/hit?page=<id>` | Increment + return the shared visit counter (Durable Object). |
| `GET`  | `/fetch?url=<u>` | Proxy a Boltz/S3 result file back with CORS. |
| `GET`  | `/health` | `{ ok, store, templateStore, counter }`. |

## Deploy (one time, ~3 minutes, free — no payment method needed)

Requires Node.js. From this `worker/` directory:

```bash
# 1. Log in to Cloudflare (opens a browser)
npx wrangler login

# 2. Deploy. The Durable Object migrations in wrangler.toml create the
#    template store and visit counter automatically — no manual setup.
npx wrangler deploy
```

`wrangler deploy` prints your Worker URL, e.g.
`https://boltzyml-proxy.<your-subdomain>.workers.dev`. Set that as the hardcoded
`PROXY_URL` constant in `v2.html` (the app has no runtime proxy override, by design).

### Verify

```bash
curl https://boltzyml-proxy.<your-subdomain>.workers.dev/health
# {"ok":true,"service":"boltzyml-proxy","store":"durable-object","templateStore":true,"counter":true}
```

If `store` is not `"durable-object"`, the deploy did not apply the Durable Object
bindings — re-run `npx wrangler deploy` and check its output for migration errors.

## Notes

- **No secrets in the Worker.** It holds no API key of its own; each request
  carries the user's key. Nothing is persisted except transient templates.
- **Strong consistency.** Templates live in a per-id Durable Object, so an
  uploaded template is readable globally the instant it is written. This avoids
  the cross-region race that eventually-consistent KV hits when the upload and
  Boltz's fetch land in different regions.
- **Auto-cleanup.** Each template Durable Object sets a 2-hour alarm that
  self-destructs it — no lifecycle config needed.
- **Open-proxy guard.** `/fetch` only retrieves `*.amazonaws.com` and
  `*.boltz.bio` hosts.
