#!/usr/bin/env python3
"""Compare fresh CAD against the fabrication STEPs in case/out."""
import argparse
from pathlib import Path

import cadquery as cq


def changed_volume(fresh, recorded):
    # STEP headers contain export dates. Identical DATA sections need no CAD comparison.
    files = [path.read_bytes().replace(b"\r\n", b"\n") for path in (fresh, recorded)]
    bodies = [data.split(b"\nDATA;\n", 1)[1] for data in files]
    if bodies[0] == bodies[1]:
        return 0.0

    a, b = (cq.importers.importStep(str(path)).val() for path in (fresh, recorded))
    if abs(a.Volume() - b.Volume()) > 0.01:
        return abs(a.Volume() - b.Volume())  # Lower bound is enough to reject.
    return a.cut(b).Volume() + b.cut(a).Volume()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fresh", type=Path)
    parser.add_argument("--recorded", type=Path, default=Path(__file__).parent / "out")
    args = parser.parse_args()
    failed = False
    for half in ("Left", "Right"):
        for part in ("tub", "cover"):
            name = f"Hojicha44-{half}-{part}.step"
            delta = changed_volume(args.fresh / name, args.recorded / name)
            if delta > 0.01:
                print(f"FAIL {name}: at least {delta:.4f} mm³ of changed solid; refresh fabrication export")
                failed = True
            else:
                print(f"PASS {name}: matches current generator within 0.01 mm³")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
