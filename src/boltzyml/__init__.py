"""BoltzYML — Preprocessing file generator for Boltz-2 ternary
(Protein 1 + Ligand + Protein 2) binding prediction.

Public API:

    from boltzyml import parse_cif, detect_ligand, chain_sequence
    from boltzyml import assign_chains
    from boltzyml import pocket_contacts, remap_contacts, Contact
    from boltzyml import YamlJob, render

CLI entry point:

    boltzyml --ligand A.cif --complex B.cif -o out.yaml
"""

from __future__ import annotations

from .parser import (
    parse_cif,
    detect_ligand,
    chain_sequence,
    AtomRecord,
    ParsedCif,
    CifParseError,
    STANDARD_AA,
    AA3_TO_1,
)
from .contacts import pocket_contacts, remap_contacts, Contact
from .utils import assign_chains, ChainAssignment, is_generic_ligand_code
from .yaml_writer import YamlJob, render

__version__ = "0.1.1"

__all__ = [
    "__version__",
    # parser
    "parse_cif",
    "detect_ligand",
    "chain_sequence",
    "AtomRecord",
    "ParsedCif",
    "CifParseError",
    "STANDARD_AA",
    "AA3_TO_1",
    # contacts
    "pocket_contacts",
    "remap_contacts",
    "Contact",
    # utils
    "assign_chains",
    "ChainAssignment",
    "is_generic_ligand_code",
    # yaml writer
    "YamlJob",
    "render",
]
