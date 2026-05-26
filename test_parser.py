"""Smoke tests for parser.py — synthetic CIFs covering 1-line and 2-line
atom record layouts. Run: python test_parser.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from parser import (
    parse_cif, detect_ligand, chain_sequence, STANDARD_AA,
)


# 18-field, 1-line-per-record (AlphaFold3 style). Two ALA + one ABA ligand atom.
CIF_ONE_LINE = """\
data_test
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_asym_id
_atom_site.auth_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_PDB_model_num
ATOM   1  N  N   . ALA A 1 1  10.000 10.000 10.000 A 1 ? 1.00 20.00 1
ATOM   2  C  CA  . ALA A 1 1  11.000 10.000 10.000 A 1 ? 1.00 20.00 1
ATOM   3  C  C   . ALA A 1 1  12.000 10.000 10.000 A 1 ? 1.00 20.00 1
ATOM   4  N  N   . VAL A 1 2  13.000 10.000 10.000 A 2 ? 1.00 20.00 1
ATOM   5  C  CA  . VAL A 1 2  14.000 11.000 10.000 A 2 ? 1.00 20.00 1
HETATM 6  C  C1  . A8S B 2 .  15.000 11.500 10.000 B 1 ? 1.00 20.00 1
HETATM 7  O  O1  . HOH C 3 .  50.000 50.000 50.000 C 1 ? 1.00 20.00 1
#
"""


# Same 18 fields but each ATOM record split across 2 lines (9 tokens each).
def _make_two_line() -> str:
    header = """\
data_test2
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_asym_id
_atom_site.auth_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_PDB_model_num
"""
    # Each record = 18 tokens, written as 9 + 9 across two lines.
    records = [
        # (group, id, type, atom_id, alt, comp, lasym, lent, lseq,
        #  x, y, z, aasym, aseq, ins, occ, b, model)
        ("ATOM",   "1", "N", "N",  ".", "ALA", "A", "1", "1",
         "10.000", "10.000", "10.000", "A", "1", "?", "1.00", "20.00", "1"),
        ("ATOM",   "2", "C", "CA", ".", "ALA", "A", "1", "1",
         "11.000", "10.000", "10.000", "A", "1", "?", "1.00", "20.00", "1"),
        ("ATOM",   "3", "C", "CA", ".", "VAL", "A", "1", "2",
         "14.000", "11.000", "10.000", "A", "2", "?", "1.00", "20.00", "1"),
        ("HETATM", "4", "C", "C1", ".", "A8S", "B", "2", ".",
         "15.000", "11.500", "10.000", "B", "1", "?", "1.00", "20.00", "1"),
    ]
    body = []
    for r in records:
        body.append(" ".join(r[:9]))
        body.append(" ".join(r[9:]))
    return header + "\n".join(body) + "\n#\n"


def _write(text: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".cif", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


def test_one_line():
    p = _write(CIF_ONE_LINE)
    cif = parse_cif(p)
    assert len(cif.atoms) == 7, f"expected 7 atoms, got {len(cif.atoms)}"
    chains = cif.by_chain()
    assert set(chains) == {"A", "B", "C"}, chains.keys()
    ca = [a for a in cif.protein_atoms() if a.label_atom_id == "CA"]
    assert len(ca) == 2
    lig = detect_ligand(cif)
    assert lig == ("B", "A8S"), lig
    seq = chain_sequence(cif, "A")
    assert seq == "AV", seq
    print("one-line: OK")


def test_two_line():
    p = _write(_make_two_line())
    cif = parse_cif(p)
    assert len(cif.atoms) == 4, f"expected 4 atoms, got {len(cif.atoms)}"
    assert detect_ligand(cif) == ("B", "A8S")
    seq = chain_sequence(cif, "A")
    assert seq == "AV", seq
    # Coordinates must be parsed from the correct positions, not shifted.
    first = cif.atoms[0]
    assert first.auth_asym_id == "A" and first.auth_seq_id == 1
    assert (first.x, first.y, first.z) == (10.0, 10.0, 10.0)
    print("two-line: OK")


def test_standard_aa_constant():
    assert "ALA" in STANDARD_AA and "HOH" not in STANDARD_AA


if __name__ == "__main__":
    test_standard_aa_constant()
    test_one_line()
    test_two_line()
    print("all tests passed")
