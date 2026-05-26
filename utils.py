"""Chain identification helpers — match Protein A across two CIFs by
sequence similarity, then pick whatever is left as Protein B."""

from __future__ import annotations

from dataclasses import dataclass

from parser import ParsedCif, STANDARD_AA, chain_sequence


@dataclass
class ChainAssignment:
    chain_a_in_ligand: str
    chain_a_in_complex: str
    chain_b_in_complex: str | None
    seq_a: str
    seq_b: str
    match_similarity: float  # similarity between seq_a and the matched A in complex CIF


def protein_chains(cif: ParsedCif) -> list[tuple[str, int]]:
    """Return (chain_id, CA_count) for every chain with >=1 standard-AA CA."""
    counts: dict[str, int] = {}
    for a in cif.protein_atoms():
        if a.label_atom_id != "CA":
            continue
        counts[a.auth_asym_id] = counts.get(a.auth_asym_id, 0) + 1
    return sorted(counts.items(), key=lambda kv: -kv[1])


def kmer_similarity(a: str, b: str, k: int = 5) -> float:
    """Jaccard-ish overlap: fraction of b's k-mers also in a's k-mer set.
    Cheap, no dependencies, robust enough to tell same-protein from
    different-protein for typical 100-500 aa chains."""
    if len(a) < k or len(b) < k:
        return 0.0
    seen = {a[i:i + k] for i in range(len(a) - k + 1)}
    total = len(b) - k + 1
    hits = sum(1 for i in range(total) if b[i:i + k] in seen)
    return hits / total if total else 0.0


def assign_chains(ligand_cif: ParsedCif,
                  complex_cif: ParsedCif) -> ChainAssignment:
    lig_chains = protein_chains(ligand_cif)
    if not lig_chains:
        raise ValueError("No protein chain in the ligand CIF.")
    chain_a_lig = lig_chains[0][0]  # longest protein chain = Protein A
    seq_a = chain_sequence(ligand_cif, chain_a_lig)

    cx_chains = protein_chains(complex_cif)
    if not cx_chains:
        raise ValueError("No protein chain in the complex CIF.")

    scored: list[tuple[str, str, float]] = []
    for name, _ in cx_chains:
        seq = chain_sequence(complex_cif, name)
        scored.append((name, seq, kmer_similarity(seq_a, seq)))

    scored.sort(key=lambda t: -t[2])
    match_a_name, _match_a_seq, sim = scored[0]

    chain_b_name: str | None = None
    seq_b = ""
    for name, seq, _ in scored:
        if name != match_a_name:
            chain_b_name = name
            seq_b = seq
            break
    if chain_b_name is None and len(scored) == 1:
        # Single-chain complex CIF — treat it as Protein B itself, even
        # though it also matched as A. The user almost certainly meant this.
        chain_b_name = scored[0][0]
        seq_b = scored[0][1]

    return ChainAssignment(
        chain_a_in_ligand=chain_a_lig,
        chain_a_in_complex=match_a_name,
        chain_b_in_complex=chain_b_name,
        seq_a=seq_a,
        seq_b=seq_b,
        match_similarity=sim,
    )


GENERIC_LIGAND_CODES = {"LIG", "UNL", "UNK"}


def is_generic_ligand_code(comp: str) -> bool:
    return comp.upper() in GENERIC_LIGAND_CODES
