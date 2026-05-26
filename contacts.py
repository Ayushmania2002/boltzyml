"""Pocket contact computation for Boltz-2 constraints.

Uses CA (alpha carbon) atoms only — CA-based 6.0 A roughly matches
all-atom 4.0 A real sidechain contacts, which is what Boltz-2 expects
as a soft pocket constraint.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from parser import AtomRecord, ParsedCif, STANDARD_AA


@dataclass(frozen=True)
class Contact:
    chain: str          # auth_asym_id of the protein residue
    res_id: int         # auth_seq_id
    comp: str           # 3-letter residue code (e.g. PHE)
    distance: float     # angstroms, CA-to-nearest-ligand-atom


def pocket_contacts(cif: ParsedCif,
                    ligand_chain: str,
                    ligand_comp: str,
                    *,
                    cutoff: float = 6.0,
                    protein_chain: str | None = None,
                    ligand_seq_id: int | None = None) -> list[Contact]:
    """Return CA atoms whose nearest distance to any ligand atom is <= cutoff.

    If protein_chain is None, scan all protein chains in the file (useful
    when a CIF contains both partners and you want a global pocket).
    If ligand_seq_id is given, only that ligand residue's atoms are used —
    helpful when multiple copies of the same ligand exist.

    Results are sorted by residue number for stable YAML output.
    """
    lig_atoms: list[tuple[float, float, float]] = []
    for a in cif.hetatm():
        if a.auth_asym_id != ligand_chain:
            continue
        if a.label_comp_id != ligand_comp:
            continue
        if ligand_seq_id is not None and a.auth_seq_id != ligand_seq_id:
            continue
        lig_atoms.append((a.x, a.y, a.z))

    if not lig_atoms:
        raise ValueError(
            f"No ligand atoms found for chain={ligand_chain} comp={ligand_comp}"
        )

    cutoff_sq = cutoff * cutoff
    out: list[Contact] = []
    seen: set[tuple[str, int]] = set()

    for a in cif.protein_atoms():
        if a.label_atom_id != "CA":
            continue
        if protein_chain is not None and a.auth_asym_id != protein_chain:
            continue
        if a.label_comp_id not in STANDARD_AA:
            continue

        key = (a.auth_asym_id, a.auth_seq_id)
        if key in seen:
            continue

        min_d2 = min(
            (a.x - lx) ** 2 + (a.y - ly) ** 2 + (a.z - lz) ** 2
            for lx, ly, lz in lig_atoms
        )
        if min_d2 <= cutoff_sq:
            seen.add(key)
            out.append(Contact(
                chain=a.auth_asym_id,
                res_id=a.auth_seq_id,
                comp=a.label_comp_id,
                distance=sqrt(min_d2),
            ))

    out.sort(key=lambda c: (c.chain, c.res_id))
    return out


def remap_contacts(contacts: list[Contact],
                   chain_map: dict[str, str]) -> list[Contact]:
    """Rewrite contact.chain via chain_map (e.g. source CIF chain 'A' -> Boltz
    chain 'A'). Contacts with no mapping are dropped."""
    out: list[Contact] = []
    for c in contacts:
        if c.chain not in chain_map:
            continue
        out.append(Contact(chain=chain_map[c.chain], res_id=c.res_id,
                           comp=c.comp, distance=c.distance))
    return out
