"""Emit Boltz-2 v1 YAML for a ternary complex (Protein A + Ligand + Protein B).

No PyYAML dependency — the structure is fixed, so a direct emitter keeps
field ordering deterministic and avoids quoting surprises on long sequences.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contacts import Contact


@dataclass
class YamlJob:
    seq_a: str                 # Protein A sequence (Boltz chain A)
    seq_c: str                 # Protein B sequence (Boltz chain C)
    ligand_ccd: str            # PDB CCD code (or override) — Boltz chain B
    contacts: list[Contact]    # already remapped to Boltz chain A
    cutoff: float = 6.0
    affinity: bool = True
    pocket: bool = True
    force_pocket: bool = True


def render(job: YamlJob) -> str:
    out: list[str] = []
    out.append("version: 1")
    out.append("sequences:")
    out.append("  - protein:")
    out.append("      id: A")
    out.append("      sequence: " + job.seq_a)
    out.append("  - ligand:")
    out.append("      id: B")
    out.append("      ccd: " + job.ligand_ccd)
    out.append("  - protein:")
    out.append("      id: C")
    out.append("      sequence: " + job.seq_c)

    if job.pocket and job.contacts:
        out.append("constraints:")
        out.append("  - pocket:")
        out.append("      binder: B")
        out.append("      contacts:")
        for c in job.contacts:
            out.append(f"        - [A, {c.res_id}]   # {c.comp}{c.res_id}")
        out.append(f"      max_distance: {job.cutoff:.1f}")
        out.append("      force: " + ("true" if job.force_pocket else "false"))

    if job.affinity:
        out.append("properties:")
        out.append("  - affinity:")
        out.append("      binder: B")

    return "\n".join(out) + "\n"
