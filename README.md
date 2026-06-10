<p align="center">
  <img src="https://raw.githubusercontent.com/Ayushmania2002/boltzyml/main/banner.png" alt="BoltzYML pipeline overview" width="780">
</p>

<h1 align="center">BoltzYML</h1>

<p align="center">
  <strong>Two browser tools for <a href="https://github.com/jwohlwend/boltz">Boltz-2</a> structure &amp; binding prediction —<br>
  <em>v1</em> generates local-CLI YAML for ternary complexes · <em>v2.0</em> builds &amp; submits hosted-API jobs for any complex.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/boltzyml/"><img src="https://img.shields.io/pypi/v/boltzyml.svg?color=2563eb&label=PyPI&v=1" alt="PyPI version"></a>
  <a href="https://pypi.org/project/boltzyml/"><img src="https://img.shields.io/pypi/pyversions/boltzyml.svg?color=2563eb&label=Python&v=1" alt="Python versions"></a>
  <a href="https://pypistats.org/packages/boltzyml"><img src="https://img.shields.io/pypi/dm/boltzyml.svg?color=2563eb&label=downloads" alt="PyPI downloads"></a>
  <a href="https://github.com/Ayushmania2002/boltzyml/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/boltzyml.svg?color=0e9f6e&label=license&v=1" alt="License"></a>
  <a href="https://github.com/Ayushmania2002/boltzyml/stargazers"><img src="https://img.shields.io/github/stars/Ayushmania2002/boltzyml.svg?color=f59e0b&label=stars&v=1" alt="GitHub stars"></a>
  <a href="https://ayushmania2002.github.io/boltzyml/"><img src="https://img.shields.io/badge/web%20app-live-0e9f6e.svg?v=1" alt="Web app"></a>
  <a href="https://doi.org/10.5281/zenodo.20397272"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20397272-3C7EBC.svg?v=1" alt="Zenodo DOI"></a>
</p>

<table align="center" width="100%">
<tr>
  <th width="50%">🧪&nbsp; BoltzYML v1</th>
  <th width="50%">🚀&nbsp; BoltzYML v2.0</th>
</tr>
<tr>
  <td align="center"><b><a href="https://ayushmania2002.github.io/boltzyml/">Open v1 web app →</a></b></td>
  <td align="center"><b><a href="https://ayushmania2002.github.io/boltzyml/v2.html">Open v2.0 web app →</a></b></td>
</tr>
<tr valign="top">
  <td>
    Ternary <b>Protein 1 + Ligand + Protein 2</b> preprocessing. Drop two CIFs → emits a ready-to-run
    <b>Boltz CLI YAML</b> (<code>version: 1</code>) with pocket constraints and an affinity block, for
    local <code>boltz predict</code>. Also shipped as a <a href="https://pypi.org/project/boltzyml/">PyPI CLI</a>.
    <br><br>→ <a href="#boltzyml-v1--ternary-cli-yaml-generator"><b>v1 details below</b></a>
  </td>
  <td>
    <b>Any</b> binary / ternary / N-body complex (protein · ligand · DNA · RNA). Builds the
    <b>hosted Boltz-2 API</b> payload, <b>auto-cleans template CIFs</b> in the browser, and
    <b>submits with your own API key</b> — then polls jobs and downloads results.
    <br><br>→ <a href="#boltzyml-v20--hosted-api-builder--submitter"><b>v2.0 details below</b></a>
  </td>
</tr>
</table>

<p align="center">
  <a href="#boltzyml-v1--ternary-cli-yaml-generator">v1 details</a>
  &nbsp;·&nbsp;
  <a href="#cli">v1 CLI</a>
  &nbsp;·&nbsp;
  <a href="#how-it-works">How v1 works</a>
  &nbsp;·&nbsp;
  <a href="#boltzyml-v20--hosted-api-builder--submitter">v2.0 details</a>
  &nbsp;·&nbsp;
  <a href="#using-boltzyml-v20--just-bring-your-boltz-api-key">How to use v2.0</a>
  &nbsp;·&nbsp;
  <a href="#getting-a-boltz-api-key--cost">Get an API key</a>
</p>

---

## BoltzYML v1 — ternary CLI-YAML generator

> **`index.html`** + **PyPI CLI** — the original tool. Live at **<https://ayushmania2002.github.io/boltzyml/>**.
> Generates the open-source **Boltz CLI** YAML (`version: 1`) for running `boltz predict` on your own machine.

## When to use BoltzYML v1

Use this tool **only** if you want to study how the interaction between **two proteins changes in the presence of a ligand**.

That is the one scenario it is built for: a small molecule sits in a pocket of Protein 1, and you want Boltz-2 to predict how Protein 1 and Protein 2 dock together while that ligand is bound (or absent, as a control). Typical use cases:

- ABA signaling: PYR/PYL/RCAR receptor + ABA + PP2C phosphatase
- Allosteric drug screens where a ligand is expected to enable or block partner binding
- Any ternary system where the ligand sits on Protein 1 and you care about the Protein 1 ↔ Protein 2 interface

If your problem is just protein–protein docking, just protein–ligand docking, or anything that is **not** a ternary Protein 1 + Ligand + Protein 2 complex, BoltzYML will not help — write the YAML directly or use the Boltz-2 examples.

---

## What it does

You hand BoltzYML two CIF files:

| Input | Contents | Role |
| --- | --- | --- |
| `protein1_ligand.cif` | Protein 1 bound to the ligand (docked structure, e.g. AlphaFill, Glide, AutoDock) | Source of Protein 1 sequence + ligand identity + pocket residues |
| `protein1_protein2.cif` | Protein 1 together with Protein 2 (e.g. AlphaFold3 prediction) | Source of Protein 2 sequence |

BoltzYML then runs entirely in your browser (or via the CLI) and produces a single Boltz-2 v1 YAML with:

1. Protein 1 sequence on chain `A`
2. The ligand on chain `B` (with its PDB CCD code)
3. Protein 2 sequence on chain `C`
4. A `pocket` constraint listing the Protein 1 CA atoms within a cutoff of the ligand
5. An `affinity` property block targeting the ligand

That YAML is then fed straight into the Boltz-2 CLI.

---

## Two ways to run it

### 1. Web app (recommended)

Open **<https://ayushmania2002.github.io/boltzyml/>**, drop in the two CIFs, click *Generate YAML*, download the file.

Everything happens in your browser — no uploads, no server, no telemetry. Works on any modern browser, no installation required.

### 2. <a id="cli"></a>Command-line interface

Install from PyPI:

```bash
pip install boltzyml
```

Then run:

```bash
boltzyml \
    --ligand   PYL2_ABA.cif \
    --complex  PYL2_PP2C30.cif \
    --output   PYL2_ABA_PP2C30.yaml
```

Pure Python 3.10+, **zero runtime dependencies** (no `gemmi`, no `numpy`, no `pyyaml` required).

You can also clone the repo and run it as a module without installing:

```bash
git clone https://github.com/Ayushmania2002/boltzyml.git
cd boltzyml
pip install -e .
boltzyml --ligand A.cif --complex B.cif -o out.yaml
```

#### CLI options

| Flag | Description | Default |
| --- | --- | --- |
| `--ligand` | CIF with Protein 1 + Ligand | required |
| `--complex` | CIF with Protein 1 + Protein 2 | required |
| `-o, --output` | Output YAML path | `{ligand-stem}__{complex-stem}.yaml` |
| `--job-name` | Job name used for the default output filename | derived |
| `--cutoff` | CA-to-ligand distance cutoff in Å | `6.0` |
| `--ccd` | Override the ligand CCD code (used verbatim in the YAML's `ccd:` field) | auto-detect |
| `--no-affinity` | Skip the affinity prediction block | off |
| `--no-pocket` | Skip the pocket constraints block | off |
| `--no-force` | Emit `force: false` on the pocket block | off |
| `-v, --verbose` | Print detected chains, ligand, and contacts | off |

---

## <a id="how-it-works"></a>How it works

1. **Parse both CIFs.** The parser handles two layouts seen in the wild: single-line atom records (AlphaFold3 style, 18 fields per line) and two-line records (some AlphaFill outputs, 21 fields split 17 + 4).
2. **Identify the ligand.** The first non-water HETATM whose comp ID is not a standard amino acid is taken as the ligand. If the CIF labels it generically (`LIG`, `UNL`, `UNK`), the tool warns and asks for a CCD override.
3. **Assign chains.** Protein 1 = the longest protein chain in the ligand CIF. The corresponding chain in the complex CIF is matched by 5-mer overlap similarity; the remaining chain is Protein 2.
4. **Compute pocket contacts.** CA atoms of Protein 1 within `--cutoff` Å of any ligand atom are emitted as `[A, residue_number]` entries, using the CIF's `auth_seq_id` so the numbers match Boltz-2's own residue numbering.
5. **Emit YAML.** A deterministic Boltz-2 v1 YAML is written out, in the field order Boltz-2 expects.

> **Why CA-only at 6 Å?** CA-to-ligand at 6 Å approximates all-atom contacts at ~4 Å, which is the right scale for the soft pocket constraint Boltz-2 applies as an inference-time potential.

---

## Example output

```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MEAHVERALREGLTEEERAALEPAVMAHHTFPPSTTTATTAAATCTSLVTQRVAAPVRAVWPIVRSFGNPQRYKHFVRTCALAAGDGASVGSVREVTVVSGLPASTSTERLEMLDDDRHIISFRVVGGQHRLRNYRSVTSVTEFQPPAAGPAPAPPYCVVVESYVVDVPDGNTAEDTRMFTDTVVKLNLQKLAAVAEDSSSASRRRD
  - ligand:
      id: B
      ccd: A8S
  - protein:
      id: C
      sequence: MAEICCEVVAGSSSEGKGPECDTGSRAARRRR...
constraints:
  - pocket:
      binder: B
      contacts:
        - [A, 76]    # PHE76
        - [A, 98]    # VAL98
        - [A, 103]   # PRO103
        - [A, 104]   # ALA104
        - [A, 107]   # SER107
        - [A, 130]   # HIS130
        - [A, 131]   # ARG131
        - [A, 132]   # LEU132
        - [A, 181]   # THR181
        - [A, 184]   # VAL184
        - [A, 185]   # VAL185
      max_distance: 6.0
      force: true
properties:
  - affinity:
      binder: B
```

---

## Running Boltz-2 on the output

```bash
pip install boltz

boltz predict job.yaml \
    --use_msa_server \
    --use_potentials \
    --diffusion_samples 3 \
    --recycling_steps  3 \
    --step_scale       1.638
```

Key result files:

| File | Contents |
| --- | --- |
| `*_model_0.pdb` | Predicted ternary structure |
| `confidence_*.json` | `iptm`, `ptm`, `ligand_iptm` |
| `affinity_*.json` | `affinity_pred_value` in kcal/mol |
| `pae_*.npz` | Predicted aligned error matrix |

Sanity checks:

- `iptm > 0.6` — confident protein–protein interface
- `ligand_iptm > 0.5` — confident ligand placement
- A low off-diagonal block between chain `A` and chain `C` in the PAE map = confident interaction

---

## BoltzYML v2.0 — hosted-API builder &amp; submitter

> **`v2.html`** — the second, broader tool. Live at **<https://ayushmania2002.github.io/boltzyml/v2.html>**.

Where v1 emits local-CLI YAML, **v2.0 targets the hosted [Boltz-2 API](https://boltz.bio)**. It builds the
API payload (`entities` / `templates` / `binding` / `model_options`), repairs your template CIFs in the
browser, and submits jobs with **your own API key**. It is **not** limited to ternary complexes — define
any binary, ternary, or N-body mix of proteins, ligands (CCD or SMILES), DNA, and RNA.

| Stage | Capability |
| --- | --- |
| **1 · Build** | Arbitrary entity sets (protein / ligand-CCD / ligand-SMILES / DNA / RNA), per-chain IDs, binder selection, and full sampling control (`num_samples`, `recycling_steps`, `sampling_steps`, `step_scale`, MSA mode). |
| **1 · Clean templates** | Drop a raw RCSB/ChimeraX `.cif`/`.pdb`. BoltzYML rewrites `_struct_asym` to remove phantom chains, strips waters/ligands, repairs modified residues (e.g. `OCY → CYS`), and deletes `_pdbx_poly_seq_scheme` / `_struct_conn` records — the exact fixes that otherwise make the Boltz template parser fail with `StopIteration` / `Invalid input schema`. Then map each template chain to a prediction chain. |
| **2 · Submit** | Paste **your own Boltz API key** and click submit — no setup, no install. Your key lives only in your browser tab and is forwarded to Boltz through BoltzYML's open-source proxy, which stores nothing. |
| **3 · Results** | Poll job status, read ipTM / pTM / pLDDT, and download a results `.zip` (every sample CIF + `metrics.json` + a branded `README.txt` with citations and a how-to-interpret guide) plus the best structure by ipTM. |

### Using BoltzYML v2.0 — just bring your Boltz API key

No installation, no proxy setup. The whole workflow is **drop files → paste key → submit → download**:

1. **Get a Boltz API key** ([instructions below](#getting-a-boltz-api-key--cost)).
2. Open the app: **<https://ayushmania2002.github.io/boltzyml/v2.html>**
3. **Define your complex** — add entities (protein sequence, ligand by CCD code or SMILES, DNA, RNA), give each a single-letter chain ID, and mark a ligand as **binder** if you want affinity/pose scoring.
4. **(Optional) Drop a template** — a `.cif`/`.pdb` from RCSB, AlphaFold, ChimeraX, etc. BoltzYML auto-cleans it **in your browser**; then map each template chain to a prediction chain.
5. **Set sampling options** (or keep the defaults) and click **Rebuild** to preview the exact payload.
6. **Paste your Boltz API key** and click **Submit prediction**.
7. Under **Jobs & results**: **Poll** until `succeeded`, then **Download results** — you get a `.zip` of every sample structure + `metrics.json` + `README.txt`, plus the best structure by ipTM.

### Getting a Boltz API key &amp; cost

The hosted Boltz-2 API is a paid service (currently in **beta**), run by Boltz — separate from BoltzYML.

1. Go to the **[Boltz API docs](https://api.boltz.bio/docs/api/)**, create an account, and generate an API key.
2. Boltz includes **$5 of free credit every month**; paid top-ups / subscriptions are available — check the **current rates on the Boltz site/docs** (pricing can change during beta).
3. Paste the key into BoltzYML v2.0. It stays in your browser tab only (optionally remembered for the session) and is never sent anywhere except through the proxy to Boltz.

**Rough cost per prediction** *(approximate — confirm current rates at the link above):* cost scales with
**`num_samples` × complex size**. A typical job runs on the order of **a few cents up to ~$0.50**, so the
**$5 monthly free credit comfortably covers dozens of small jobs**. Larger complexes and higher
`num_samples` cost more.

> ⚠️ The Boltz API is in **beta** — endpoints, pricing, and rate limits may change. Always check the [official docs](https://api.boltz.bio/docs/api/) for current details.

### How your inputs are processed — and what is (not) stored

**All parsing and cleaning happens in your browser.** Your raw files are never uploaded for processing.

1. **In your browser (client-side JavaScript):**
   - Sequences and ligand codes you type stay local.
   - When you drop a template CIF/PDB, BoltzYML parses it locally and: detects which chains actually
     have coordinates, rewrites `_struct_asym` to drop phantom chains, strips waters/ligands (HETATM),
     maps modified residues (e.g. `OCY → CYS`) to standard parents, and removes
     `_pdbx_poly_seq_scheme` / `_struct_conn` metadata that would otherwise crash the Boltz parser.
   - It assembles the Boltz API payload (`entities` / `templates` / `binding` / `model_options`).
2. **At submission**, your browser sends the **already-cleaned** payload plus your API key to the proxy
   — a small, stateless, open-source Cloudflare Worker ([`worker/worker.js`](worker/worker.js)). The proxy:
   - uploads each cleaned template to transient storage so Boltz can fetch it by URL,
   - forwards the payload to `api.boltz.bio` with your key in a request header,
   - relays status polls and proxies result downloads (Boltz's result files are otherwise CORS-blocked
     for browsers).

**Data handling / privacy:**

- **Your API key** is forwarded to Boltz once per request and is **never logged or stored** by the proxy.
- **Your sequences / payload** pass through the proxy to Boltz and are **not stored** by the proxy.
- **Cleaned template files** are the *only* thing held, and only **transiently** — in Workers KV with a
  **2-hour TTL**, after which they auto-delete (Boltz needs a fetchable URL for templates).
- The proxy is **stateless and open-source**, so you can read exactly what it does.

### Why a proxy at all?

`api.boltz.bio` sends no CORS headers, so a static page (GitHub Pages) can't call it directly, and result
files are likewise CORS-blocked. v2.0 therefore routes through a tiny stateless Cloudflare Worker. The
public app uses a **hosted proxy maintained by the author** — you don't deploy anything.

**Prefer to run your own proxy?** (e.g. for a lab, or to use your own free-tier quota.) Deploy the included
Worker in a few minutes and point the app at it with `?proxy=https://your-worker.workers.dev`:

```bash
cd worker
npx wrangler login
npx wrangler kv namespace create TEMPLATES   # prints an id → paste into wrangler.toml
npx wrangler deploy
```

See [`worker/README.md`](worker/README.md). Templates are stored in Workers KV with a 2-hour TTL, and no
payment method is required.

### Boltz API (beta) — SDKs for advanced / programmatic use

You don't need these to use BoltzYML (the web tool handles everything), but the Boltz API ships official
client libraries if you want to script submissions directly:

| Language | Install | Docs |
| --- | --- | --- |
| TypeScript `0.43.0` | `npm install boltz-api` | [docs](https://api.boltz.bio/docs/api/typescript) |
| Python `0.33.0` | `pip install boltz-api` | [docs](https://api.boltz.bio/docs/api/python) |
| Go `v0.23.0` | `go get -u 'github.com/boltz-bio/boltz-api-go@v0.0.1'` | [docs](https://api.boltz.bio/docs/api/go) |
| CLI `v0.28.0` | `irm https://install.boltz.bio/boltz-api/install.ps1 \| iex` | [docs](https://api.boltz.bio/docs/api/cli) |

---

## Project layout

```
boltzyml/
├── index.html              # v1 web app — ternary CLI-YAML generator (GitHub Pages)
├── v2.html                 # v2.0 web app — hosted-API builder, template cleaner, submitter
├── worker/                 # Stateless Cloudflare Worker proxy for v2.0 submission
│   ├── worker.js           #   key passthrough + template hosting + result fetch
│   ├── wrangler.toml       #   deploy config (R2 bucket binding)
│   └── README.md           #   one-time deploy instructions
├── logo.png                # Wordmark — favicon + header logo
├── banner.png              # Pipeline schematic — used in this README
│
├── pyproject.toml          # PyPI packaging metadata (hatchling)
├── LICENSE                 # MIT
│
├── src/boltzyml/
│   ├── __init__.py         # Public API re-exports
│   ├── cli.py              # CLI entry point (boltzyml command)
│   ├── parser.py           # CIF parser (1-line and 2-line layouts)
│   ├── contacts.py         # CA-to-ligand pocket contact computation
│   ├── utils.py            # Chain assignment via k-mer similarity
│   └── yaml_writer.py      # Boltz-2 v1 YAML emitter
│
└── tests/
    ├── test_parser.py      # Synthetic CIFs for both layouts
    ├── test_contacts.py    # Cutoff filtering, missing ligand, chain remap
    └── test_cli.py         # End-to-end CLI smoke test
```

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Or run each file directly without pytest:

```bash
python tests/test_parser.py
python tests/test_contacts.py
python tests/test_cli.py
```

Each script exits non-zero on failure and prints `all tests passed` otherwise.

---

## Gotchas

- **`LIG` / `UNL` / `UNK` ligands.** Docking tools often name the ligand generically. The real PDB CCD code (e.g. `A8S` for abscisic acid, `ATP`, `HEM`) belongs in the `ccd:` field — use the CCD override in the web app or `--ccd` on the CLI. Verify codes at <https://www.rcsb.org/ligand/>.
- **Residue numbering.** Boltz-2 uses `auth_seq_id` from your CIF. If your CIF starts at residue 14 (truncated structure), the pocket numbers will start at 14 too — that is correct.
- **Apo vs holo Protein 1.** For the ligand CIF, use the **holo** (ligand-bound) structure, not the apo AlphaFold prediction, so the pocket is in the right conformation.
- **Tamarind Bio users.** The same YAML works on <https://app.tamarind.bio/boltz>. Do **not** include a `templates:` block when submitting there — use Tamarind's UI fields for template CIFs instead.

---

## Citation

If you use BoltzYML in published or shared work, please cite **both** of the following.

**1. BoltzYML** (this tool):

> Mallick, A. *BoltzYML: a preprocessing-file generator for Boltz-2 ternary (Protein 1 + Ligand + Protein 2) binding prediction.* Zenodo (2026). <https://doi.org/10.5281/zenodo.20397272>

BibTeX:

```bibtex
@software{boltzyml_2026,
  author    = {Mallick, Ayushman},
  title     = {{BoltzYML}: a preprocessing-file generator for Boltz-2 ternary
               (Protein 1 + Ligand + Protein 2) binding prediction},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.20397272},
  url       = {https://doi.org/10.5281/zenodo.20397272}
}
```

**2. Boltz-2** (the upstream model BoltzYML produces input for):

> Wohlwend, J. et al. *Boltz-2: Towards Accurate and Efficient Binding Affinity Prediction.* 2024. <https://github.com/jwohlwend/boltz>

---

## License

[MIT](LICENSE). Copyright © 2026 Ayushman Mallick.
