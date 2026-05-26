"""Smoke tests for boltzyml.contacts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from boltzyml.parser import parse_cif
from boltzyml.contacts import pocket_contacts, remap_contacts, Contact


# Three protein residues at known x positions, one ligand atom at x=20.
# CA-to-ligand distances: 11, 6, 3 -> only RES 2 (d=6) and RES 3 (d=3)
# are within cutoff=6.0. RES 1 is too far.
CIF = """\
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
ATOM   1 N N  . PHE A 1 1   9.000 0.000 0.000 A 1 ? 1.00 20.00 1
ATOM   2 C CA . PHE A 1 1   9.000 0.000 0.000 A 1 ? 1.00 20.00 1
ATOM   3 C CA . VAL A 1 2  14.000 0.000 0.000 A 2 ? 1.00 20.00 1
ATOM   4 C CA . SER A 1 3  17.000 0.000 0.000 A 3 ? 1.00 20.00 1
ATOM   5 C CA . LEU A 1 4  50.000 0.000 0.000 A 4 ? 1.00 20.00 1
HETATM 6 C C1 . A8S B 2 .  20.000 0.000 0.000 B 1 ? 1.00 20.00 1
HETATM 7 O O1 . HOH C 3 .  60.000 0.000 0.000 C 1 ? 1.00 20.00 1
#
"""


def _write(text: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".cif", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


def test_basic_pocket():
    cif = parse_cif(_write(CIF))
    contacts = pocket_contacts(cif, ligand_chain="B", ligand_comp="A8S",
                               cutoff=6.0)
    assert len(contacts) == 2, contacts
    assert contacts[0].res_id == 2 and contacts[0].comp == "VAL"
    assert contacts[1].res_id == 3 and contacts[1].comp == "SER"
    assert abs(contacts[0].distance - 6.0) < 1e-6
    assert abs(contacts[1].distance - 3.0) < 1e-6
    print("basic pocket: OK")


def test_cutoff_filters():
    cif = parse_cif(_write(CIF))
    tight = pocket_contacts(cif, ligand_chain="B", ligand_comp="A8S",
                            cutoff=4.0)
    assert [c.res_id for c in tight] == [3], tight
    loose = pocket_contacts(cif, ligand_chain="B", ligand_comp="A8S",
                            cutoff=12.0)
    assert [c.res_id for c in loose] == [1, 2, 3], loose
    print("cutoff filter: OK")


def test_missing_ligand_raises():
    cif = parse_cif(_write(CIF))
    try:
        pocket_contacts(cif, ligand_chain="Z", ligand_comp="A8S")
    except ValueError:
        print("missing ligand raises: OK")
        return
    raise AssertionError("expected ValueError for missing ligand")


def test_remap():
    cs = [Contact("X", 10, "PHE", 5.0), Contact("Y", 20, "VAL", 4.0)]
    mapped = remap_contacts(cs, {"X": "A"})
    assert len(mapped) == 1
    assert mapped[0].chain == "A" and mapped[0].res_id == 10
    print("remap: OK")


if __name__ == "__main__":
    test_basic_pocket()
    test_cutoff_filters()
    test_missing_ligand_raises()
    test_remap()
    print("all tests passed")
