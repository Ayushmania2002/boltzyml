"""CIF parser for Boltz-2 input preparation.

Handles two ATOM/HETATM record layouts seen in CIF files from
AlphaFold3 / AlphaFill / docking tools:

  - 1-line records: all N fields on one line.
  - 2-line records: N fields split across two consecutive lines.

Exposes parse_cif(path) -> ParsedCif with atom records and the
field schema (so downstream code can read by name, not index).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


STANDARD_AA = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLU", "GLN", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}

NON_LIGAND_HET = {"HOH", "WAT", "DOD"}

AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLU": "E", "GLN": "Q", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


@dataclass
class AtomRecord:
    group_PDB: str          # ATOM or HETATM
    label_atom_id: str      # e.g. CA, C1, O1
    label_comp_id: str      # residue/ligand 3-letter code
    label_asym_id: str
    label_seq_id: str       # may be "."
    auth_asym_id: str       # chain id used by Boltz
    auth_seq_id: int        # residue number used by Boltz
    x: float
    y: float
    z: float
    model: int = 1


@dataclass
class ParsedCif:
    path: Path
    fields: list[str]
    atoms: list[AtomRecord] = field(default_factory=list)

    def by_chain(self) -> dict[str, list[AtomRecord]]:
        out: dict[str, list[AtomRecord]] = {}
        for a in self.atoms:
            out.setdefault(a.auth_asym_id, []).append(a)
        return out

    def hetatm(self) -> Iterator[AtomRecord]:
        return (a for a in self.atoms if a.group_PDB == "HETATM")

    def protein_atoms(self) -> Iterator[AtomRecord]:
        return (a for a in self.atoms
                if a.group_PDB == "ATOM" and a.label_comp_id in STANDARD_AA)


class CifParseError(ValueError):
    pass


def parse_cif(path: str | Path) -> ParsedCif:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    fields, data_lines = _collect_atom_site(lines)
    if not fields:
        raise CifParseError(f"No _atom_site loop fields found in {p}")
    if not data_lines:
        raise CifParseError(f"No ATOM/HETATM records in {p}")

    n_fields = len(fields)
    tokens_first = data_lines[0].split()
    n_tokens = len(tokens_first)
    if n_tokens == 0:
        raise CifParseError(f"Empty atom line in {p}")

    if n_tokens >= n_fields:
        lines_per_record = 1
    else:
        lines_per_record = max(1, round(n_fields / n_tokens))
        if (n_fields % lines_per_record) != 0:
            raise CifParseError(
                f"Cannot reconcile {n_fields} fields with {n_tokens} tokens "
                f"per line in {p}"
            )

    records = _group_records(data_lines, lines_per_record, n_fields)

    idx = {name: i for i, name in enumerate(fields)}
    required = ("group_PDB", "label_atom_id", "label_comp_id",
                "auth_asym_id", "auth_seq_id", "Cartn_x", "Cartn_y", "Cartn_z")
    for r in required:
        if r not in idx:
            raise CifParseError(f"Missing required field {r} in {p}")

    atoms: list[AtomRecord] = []
    for tokens in records:
        if len(tokens) < n_fields:
            # Padding short lines is safer than dropping them silently;
            # but if a record is badly truncated, skip with no data loss.
            continue
        try:
            atoms.append(AtomRecord(
                group_PDB=tokens[idx["group_PDB"]],
                label_atom_id=_unquote(tokens[idx["label_atom_id"]]),
                label_comp_id=tokens[idx["label_comp_id"]],
                label_asym_id=tokens[idx["label_asym_id"]] if "label_asym_id" in idx else ".",
                label_seq_id=tokens[idx["label_seq_id"]] if "label_seq_id" in idx else ".",
                auth_asym_id=tokens[idx["auth_asym_id"]],
                auth_seq_id=int(tokens[idx["auth_seq_id"]]),
                x=float(tokens[idx["Cartn_x"]]),
                y=float(tokens[idx["Cartn_y"]]),
                z=float(tokens[idx["Cartn_z"]]),
                model=int(tokens[idx["pdbx_PDB_model_num"]])
                    if "pdbx_PDB_model_num" in idx else 1,
            ))
        except (ValueError, IndexError) as e:
            raise CifParseError(
                f"Bad atom record in {p}: {tokens!r} ({e})"
            ) from e

    return ParsedCif(path=p, fields=fields, atoms=atoms)


def _collect_atom_site(lines: list[str]) -> tuple[list[str], list[str]]:
    """Return (field_names, data_lines) for the _atom_site loop.

    data_lines are kept verbatim (no splitting) so the caller can handle
    1-line and multi-line record layouts. The data block ends at the first
    line beginning with '#', 'loop_', 'data_', or another '_'-prefixed item.
    """
    fields: list[str] = []
    data: list[str] = []
    state = "before"  # before | fields | data
    for ln in lines:
        s = ln.strip()
        if state == "before":
            if s.startswith("_atom_site."):
                fields.append(s.split(".", 1)[1])
                state = "fields"
        elif state == "fields":
            if s.startswith("_atom_site."):
                fields.append(s.split(".", 1)[1])
            elif s == "" or s.startswith("#"):
                continue
            else:
                state = "data"
                data.append(s)
        elif state == "data":
            if s == "" or s.startswith("#") or s.startswith("loop_") \
                    or s.startswith("data_") or s.startswith("_"):
                break
            data.append(s)
    return fields, data


def _group_records(data_lines: list[str], lines_per_record: int,
                   n_fields: int) -> list[list[str]]:
    if lines_per_record == 1:
        return [ln.split() for ln in data_lines]
    out: list[list[str]] = []
    buf: list[str] = []
    for ln in data_lines:
        buf.extend(ln.split())
    for i in range(0, len(buf), n_fields):
        chunk = buf[i:i + n_fields]
        if len(chunk) == n_fields:
            out.append(chunk)
    return out


def _unquote(tok: str) -> str:
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
        return tok[1:-1]
    return tok


def detect_ligand(cif: ParsedCif) -> tuple[str, str] | None:
    """Return (auth_asym_id, comp_id) of the first non-water HETATM ligand,
    or None if no ligand is present."""
    seen: set[tuple[str, str]] = set()
    for a in cif.hetatm():
        if a.label_comp_id in STANDARD_AA or a.label_comp_id in NON_LIGAND_HET:
            continue
        key = (a.auth_asym_id, a.label_comp_id)
        if key not in seen:
            return key
    return None


def chain_sequence(cif: ParsedCif, chain: str) -> str:
    """Return the 1-letter amino acid sequence for a chain, using CA atoms
    sorted by auth_seq_id. Unknown residues become 'X'."""
    cas: dict[int, str] = {}
    for a in cif.protein_atoms():
        if a.auth_asym_id != chain:
            continue
        if a.label_atom_id != "CA":
            continue
        cas[a.auth_seq_id] = AA3_TO_1.get(a.label_comp_id, "X")
    return "".join(cas[i] for i in sorted(cas))
