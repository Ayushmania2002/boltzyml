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
| `GET`  | `/status?id=<id>` | Forward a status/retrieve call. |
| `POST` | `/template` | Store a cleaned CIF (raw body), returns `{ url }`. |
| `GET`  | `/t/<id>` | Serve a stored template — this is the URL Boltz fetches (public). |
| `GET`  | `/fetch?url=<u>` | Proxy a Boltz/S3 result file back with CORS. |
| `GET`  | `/health` | `{ ok: true, templateStore: bool }`. |

## Deploy (one time, ~3 minutes, free — no payment method needed)

Requires Node.js. From this `worker/` directory:

```bash
# 1. Log in to Cloudflare (opens a browser)
npx wrangler login

# 2. Create the KV namespace used for transient template hosting.
#    This prints an id — copy it.
npx wrangler kv namespace create TEMPLATES

# 3. Paste that id into wrangler.toml, replacing PASTE_KV_NAMESPACE_ID_HERE:
#       [[kv_namespaces]]
#       binding = "TEMPLATES"
#       id = "<the id from step 2>"

# 4. Deploy
npx wrangler deploy
```

`wrangler deploy` prints your Worker URL, e.g.
`https://boltzyml-proxy.<your-subdomain>.workers.dev`. Paste that into the
**Proxy URL** box in the BoltzYML v2.0 app.

### Verify

```bash
curl https://boltzyml-proxy.<your-subdomain>.workers.dev/health
# {"ok":true,"service":"boltzyml-proxy","templateStore":true}
```

If `templateStore` is `false`, the KV binding is missing — re-check that you
pasted the id from step 2 into the `[[kv_namespaces]]` block in `wrangler.toml`.

## Notes

- **No secrets in the Worker.** It holds no API key of its own; each request
  carries the user's key. Nothing is persisted except uploaded templates in KV.
- **Template cleanup is automatic.** Templates are stored with a 2-hour TTL
  (`worker.js`), so KV deletes them on its own — no lifecycle config needed.
- **Consistency note.** KV is eventually consistent; in the rare case Boltz
  fetches a template a second before it propagates, just re-submit. (For
  strong read-after-write, switch the binding to R2 — requires enabling R2.)
- **Open-proxy guard.** `/fetch` only retrieves `*.amazonaws.com` and
  `*.boltz.bio` hosts.
