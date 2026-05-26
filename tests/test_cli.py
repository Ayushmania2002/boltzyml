"""End-to-end smoke test: build two synthetic CIFs, run the CLI, check YAML."""

from __future__ import annotations

import tempfile
from pathlib import Path

from boltzyml import cli


HEADER = """\
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
"""

# Protein A residues: ALA(1) PHE(2) VAL(3) SER(4) LEU(5)
# Ligand A8S at residue 1 (chain B), placed at x=11 so PHE(2) at x=11 is in
# the pocket (d=0) and VAL(3) at x=14 is borderline.
LIG_BODY = """\
ATOM   1 N N  . ALA A 1 1   8.000 0.000 0.000 A 1 ? 1.00 20.00 1
ATOM   2 C CA . ALA A 1 1   8.000 0.000 0.000 A 1 ? 1.00 20.00 1
ATOM   3 C CA . PHE A 1 2  11.000 0.000 0.000 A 2 ? 1.00 20.00 1
ATOM   4 C CA . VAL A 1 3  14.000 0.000 0.000 A 3 ? 1.00 20.00 1
ATOM   5 C CA . SER A 1 4  17.000 0.000 0.000 A 4 ? 1.00 20.00 1
ATOM   6 C CA . LEU A 1 5  40.000 0.000 0.000 A 5 ? 1.00 20.00 1
HETATM 7 C C1 . A8S B 2 .  11.000 0.000 0.000 B 1 ? 1.00 20.00 1
HETATM 8 O O1 . HOH C 3 .  60.000 0.000 0.000 C 1 ? 1.00 20.00 1
#
"""

# Complex CIF: same Protein A on chain A, Protein B (different sequence)
# on chain B. Protein B = GLY MET TRP.
COMPLEX_BODY = """\
ATOM   1 C CA . ALA A 1 1   0.0 0.0 0.0 A 1 ? 1.00 20.00 1
ATOM   2 C CA . PHE A 1 2   3.8 0.0 0.0 A 2 ? 1.00 20.00 1
ATOM   3 C CA . VAL A 1 3   7.6 0.0 0.0 A 3 ? 1.00 20.00 1
ATOM   4 C CA . SER A 1 4  11.4 0.0 0.0 A 4 ? 1.00 20.00 1
ATOM   5 C CA . LEU A 1 5  15.2 0.0 0.0 A 5 ? 1.00 20.00 1
ATOM   6 C CA . GLY B 2 1   0.0 5.0 0.0 B 1 ? 1.00 20.00 1
ATOM   7 C CA . MET B 2 2   3.8 5.0 0.0 B 2 ? 1.00 20.00 1
ATOM   8 C CA . TRP B 2 3   7.6 5.0 0.0 B 3 ? 1.00 20.00 1
#
"""


def write_temp(suffix: str, body: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(HEADER + body)
    f.close()
    return Path(f.name)


def test_end_to_end():
    lig = write_temp("_lig.cif", LIG_BODY)
    cx = write_temp("_cx.cif", COMPLEX_BODY)
    out = Path(tempfile.mkdtemp()) / "job.yaml"

    rc = cli.main([
        "--ligand", str(lig),
        "--complex", str(cx),
        "--output", str(out),
        "--cutoff", "5.0",
    ])
    assert rc == 0, f"CLI exit {rc}"
    text = out.read_text(encoding="utf-8")

    # Structural assertions on the emitted YAML.
    assert "version: 1" in text
    assert "id: A" in text and "id: B" in text and "id: C" in text
    assert "ccd: A8S" in text
    # Protein A sequence is AFVSL.
    assert "sequence: AFVSL" in text
    # Protein B sequence is GMW.
    assert "sequence: GMW" in text
    # Pocket: ligand at x=11. With cutoff 5.0 only PHE(2, d=0) and
    # VAL(3, d=3) qualify; SER(4, d=6) is outside.
    assert "- [A, 2]" in text
    assert "- [A, 3]" in text
    assert "- [A, 4]" not in text
    assert "max_distance: 5.0" in text
    assert "force: true" in text
    assert "- affinity:" in text
    print("end-to-end CLI: OK")


def test_no_affinity_no_pocket():
    lig = write_temp("_lig.cif", LIG_BODY)
    cx = write_temp("_cx.cif", COMPLEX_BODY)
    out = Path(tempfile.mkdtemp()) / "job2.yaml"
    rc = cli.main([
        "--ligand", str(lig),
        "--complex", str(cx),
        "--output", str(out),
        "--no-affinity", "--no-pocket",
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "constraints:" not in text
    assert "properties:" not in text
    print("no-affinity / no-pocket flags: OK")


def test_ccd_override():
    lig = write_temp("_lig.cif", LIG_BODY)
    cx = write_temp("_cx.cif", COMPLEX_BODY)
    out = Path(tempfile.mkdtemp()) / "job3.yaml"
    rc = cli.main([
        "--ligand", str(lig), "--complex", str(cx),
        "--output", str(out), "--ccd", "ATP",
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "ccd: ATP" in text
    assert "ccd: A8S" not in text
    print("--ccd override: OK")


if __name__ == "__main__":
    test_end_to_end()
    test_no_affinity_no_pocket()
    test_ccd_override()
    print("all tests passed")
