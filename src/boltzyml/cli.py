"""BoltzYML CLI — generate a Boltz-2 v1 YAML from two CIF files.

Usage:
    boltzyml --ligand PYL2_ABA.cif --complex PYL2_PP2C30.cif \\
             --output PYL2_ABA_PP2C30.yaml

Run `boltzyml --help` for all flags.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .contacts import pocket_contacts, remap_contacts
from .parser import parse_cif, detect_ligand
from .utils import assign_chains, is_generic_ligand_code
from .yaml_writer import YamlJob, render


EPILOG = """\
BoltzYML - preprocessing-file generator for Boltz-2 ternary binding prediction.

Author:      Ayushman Mallick <ayushmania2002@gmail.com>
Repository:  https://github.com/Ayushmania2002/boltzyml
Web app:     https://ayushmania2002.github.io/boltzyml/
License:     MIT (see LICENSE in the repo)

Copyright (c) 2026 Ayushman Mallick.
"""


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="boltzyml",
        description="Generate a Boltz-2 v1 YAML from two CIF files "
                    "(Protein A + Ligand, Protein A + Protein B).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version",
                   version=f"boltzyml {__version__}")
    p.add_argument("--ligand", required=True, type=Path,
                   help="CIF with Protein A and the ligand.")
    p.add_argument("--complex", dest="complex_path", required=True, type=Path,
                   help="CIF with Protein A and Protein B.")
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="Output YAML path. Defaults to {job-name}.yaml.")
    p.add_argument("--job-name", default=None,
                   help="Job name (used for default output filename).")
    p.add_argument("--cutoff", type=float, default=6.0,
                   help="CA-to-ligand distance cutoff in Angstroms. Default 6.0.")
    p.add_argument("--ccd", default=None,
                   help="Override the ligand CCD code (e.g. A8S). "
                        "Used verbatim in the YAML's ccd: field.")
    p.add_argument("--no-affinity", action="store_true",
                   help="Skip the affinity prediction block.")
    p.add_argument("--no-pocket", action="store_true",
                   help="Skip pocket constraints entirely.")
    p.add_argument("--no-force", action="store_true",
                   help="Emit force: false on the pocket block.")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Print detected chains, ligand, and contacts.")
    return p


def auto_job_name(ligand: Path, complex_path: Path) -> str:
    return f"{ligand.stem}__{complex_path.stem}"


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)

    if not args.ligand.exists():
        print(f"error: ligand CIF not found: {args.ligand}", file=sys.stderr)
        return 2
    if not args.complex_path.exists():
        print(f"error: complex CIF not found: {args.complex_path}",
              file=sys.stderr)
        return 2

    ligand_cif = parse_cif(args.ligand)
    complex_cif = parse_cif(args.complex_path)

    lig = detect_ligand(ligand_cif)
    if lig is None:
        print("error: no ligand HETATM found in the ligand CIF.",
              file=sys.stderr)
        return 1
    lig_chain, lig_comp = lig

    assign = assign_chains(ligand_cif, complex_cif)
    if not assign.chain_b_in_complex or not assign.seq_b:
        print("error: could not identify Protein B in the complex CIF.",
              file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Ligand:    {lig_comp} (chain {lig_chain})", file=sys.stderr)
        print(f"Protein A: src chain {assign.chain_a_in_ligand} "
              f"({len(assign.seq_a)} aa) -> Boltz A", file=sys.stderr)
        print(f"Protein B: src chain {assign.chain_b_in_complex} "
              f"({len(assign.seq_b)} aa) -> Boltz C", file=sys.stderr)
        print(f"A<->complex similarity: {assign.match_similarity:.3f}",
              file=sys.stderr)

    if is_generic_ligand_code(lig_comp) and not args.ccd:
        print(f"warning: ligand named '{lig_comp}' is generic. Pass --ccd "
              f"with the real PDB CCD code (e.g. --ccd A8S).", file=sys.stderr)

    ccd = args.ccd or lig_comp

    contacts: list = []
    if not args.no_pocket:
        # Pocket residues live on Protein A in the ligand CIF.
        raw = pocket_contacts(
            ligand_cif,
            ligand_chain=lig_chain,
            ligand_comp=lig_comp,
            cutoff=args.cutoff,
            protein_chain=assign.chain_a_in_ligand,
        )
        # Source chain -> Boltz chain A.
        contacts = remap_contacts(raw, {assign.chain_a_in_ligand: "A"})
        if args.verbose:
            print(f"Pocket contacts ({len(contacts)} within "
                  f"{args.cutoff:.1f} A):", file=sys.stderr)
            for c in contacts:
                print(f"  {c.comp}{c.res_id}  d={c.distance:.2f}",
                      file=sys.stderr)

    job = YamlJob(
        seq_a=assign.seq_a,
        seq_c=assign.seq_b,
        ligand_ccd=ccd,
        contacts=contacts,
        cutoff=args.cutoff,
        affinity=not args.no_affinity,
        pocket=not args.no_pocket,
        force_pocket=not args.no_force,
    )

    yaml_text = render(job)

    job_name = args.job_name or auto_job_name(args.ligand, args.complex_path)
    out_path = args.output or Path(f"{job_name}.yaml")
    out_path.write_text(yaml_text, encoding="utf-8")
    print(f"wrote {out_path}", file=sys.stderr)
    return 0


def _entry() -> None:
    """Console-script entry point — wraps main() with sys.exit()."""
    sys.exit(main())


if __name__ == "__main__":
    _entry()
