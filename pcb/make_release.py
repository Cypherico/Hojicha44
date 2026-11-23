#!/usr/bin/env python3
"""Hojicha44 versioned release builder — roadmap Phase 7/12 evidence gate.

Exports Gerbers/drill/pos/bom per half with explicit layers (default export
dumps 21 junk layers), copies the gitignored ERC/DRC reports into the
versioned tree, and writes MANIFEST.txt (spec version, git commit, tool
versions, router rev, sha256 per file, gate status).

  python3 pcb/make_release.py            # writes generated/release/vX.Y.Z/
  python3 pcb/make_release.py --check    # verify only, no kicad-cli runs

Outputs stay tracked under generated/release/ (NOT gitignored — only
layout/generated/, *-erc.rpt, *-drc.rpt, pcb/kicad/export/, out/ are).
out/release/ remains scratch.
"""
import csv
import glob
import json
import hashlib
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pcb", "generators"))
import frame
SPEC = os.path.join(REPO, "spec", "electronics.yaml")
PCB_DIR = os.path.join(REPO, "pcb", "kicad")
LAYERS = "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts"
BOM_FIELDS = "Reference,Value,Footprint,MPN,Datasheet,QUANTITY"

KICAD_CLI = (
    shutil.which("kicad-cli")
    or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


def spec_version():
    s = open(SPEC).read()
    m = re.search(r"^version:\s*(\d+\.\d+\.\d+)", s, re.M)
    assert m, "spec missing version MAJOR.MINOR.PATCH"
    return m.group(1)


def board_commit():
    """Last commit that touched board-affecting sources. A release cut at
    an older commit is stale by definition (gerbers predate the boards)."""
    def run(*a):
        r = subprocess.run(a, capture_output=True, text=True, cwd=REPO)
        return r.stdout.strip().splitlines()[0] if r.returncode == 0 and \
            r.stdout.strip() else "unknown"
    return run("git", "log", "-1", "--format=%H", "--",
               "pcb/kicad", "pcb/generators",
               # These tools verify or package the board. The stamp
               # identifies the source revision of the fabricated design.
               ":(exclude)pcb/generators/audit_silk.py",
               ":(exclude)pcb/generators/check_board.py",
               "spec/electronics.yaml",
               # three more board-affecting input trees (3-review audit
               # 2026-10-21): the placement anchors, the board outline and
               # the vendored footprint library all feed the .kicad_pcb —
               # editing any of them must move the release stamp
               "layout/generated/v2/points/points.yaml",
               "layout/generated/v2/outlines/board.dxf",
               "pcb/stock")


def git_info():
    def run(*a):
        r = subprocess.run(a, capture_output=True, text=True, cwd=REPO)
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    return run("git", "rev-parse", "HEAD"), run("git", "describe", "--tags", "--always", "--dirty")


def tool_versions():
    r = subprocess.run([KICAD_CLI, "version"], capture_output=True, text=True)
    cli = (r.stdout + r.stderr).strip().splitlines()
    cli = cli[0] if cli else "unknown"
    sys.path.insert(0, os.path.join(REPO, "pcb", "generators"))
    import gen_route
    return cli, f"r{gen_route.ROUTER_VERSION}"


def choc_drill_findings(half, drill):
    from check_board import dxf_polylines, frame_residuals, parse_drill

    hits = parse_drill(drill)
    plate = os.path.join(REPO, "plate", f"Hojicha44-{half}-plate.dxf")
    findings, _, _ = frame_residuals(hits.get(3.45, []),
                                     hits.get(3.05, []), dxf_polylines(plate))
    return findings


def component_drill_findings(half, drills):
    """Check plating, PJ-320A seating and the controller socket slots."""
    from check_board import case_ports, committed_pads

    x, y = case_ports()[half]["trrs"]
    facing = 1 if half == "Left" else -1
    slots, pegs, bad = [], [], []
    for drill in drills:
        diameter = plating = None
        tools = {}
        expected = (drill.endswith("-PTH.drl") if len(drills) == 2 else None)
        with open(drill) as file:
            for line in map(str.strip, file):
                if "AperFunction,NonPlated" in line:
                    plating = False
                elif "AperFunction,Plated" in line:
                    plating = True
                if match := re.fullmatch(r"(T\d+)C([\d.]+)", line):
                    if expected is not None and plating != expected:
                        bad.append(f"{os.path.basename(drill)}: wrong plating for {match[1]}")
                    tools[match[1]] = float(match[2]), plating
                elif line in tools:
                    diameter, plating = tools[line]
                elif diameter == 0.90 and plating and "G85" in line:
                    coords = re.findall(r"X([-\d.]+)Y([-\d.]+)", line)
                    if len(coords) == 2:
                        slots.append(tuple(tuple(map(float, xy)) for xy in coords))
                elif diameter == 1.20 and plating is False:
                    if match := re.fullmatch(r"X([-\d.]+)Y([-\d.]+)", line):
                        pegs.append(tuple(map(float, match.groups())))

    for setback in (3.6, 10.6):
        point = (x - facing * setback, y)
        if not any(math.dist(point, p) <= 0.01 for p in pegs):
            bad.append(f"PJ-320A 1.20 NPTH peg missing at {point}")
    for setback, side in ((5.2, -1), (8.2, -1), (12.2, -1), (13.2, 1)):
        point = (x - facing * setback, y + facing * side * 2.4)
        if not any(
            abs(a[1] - b[1]) <= 0.01 and abs(math.dist(a, b) - 0.90) <= 0.01
            and math.dist(point, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)) <= 0.01
            for a, b in slots
        ):
            bad.append(f"PJ-320A 0.90 × 1.80 plated axial slot missing at {point}")
    board = os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_pcb")
    controller = [p for p in committed_pads(board) if p[0] == f"U_{half[0]}1"]
    if len(controller) != 24:
        bad.append(f"expected 24 controller pads, found {len(controller)}")
    for _, pin, x, y, *_ in controller:
        # KiCad's Excellon exporter reverses the board file's Y coordinate.
        if not any(abs(a[0] - b[0]) <= 0.01 and abs(math.dist(a, b) - 0.40) <= 0.01
                   and math.dist((x, -y), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)) <= 0.01
                   for a, b in slots):
            bad.append(f"controller pin {pin}: 0.90 × 1.30 plated slot missing")
    return bad


def export_half(half, outdir):
    pcb = os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_pcb")
    sch = os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_sch")
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(
        [KICAD_CLI, "pcb", "export", "gerbers", "-l", LAYERS,
         "-o", outdir, pcb], check=True, capture_output=True)
    subprocess.run(
        [KICAD_CLI, "pcb", "export", "drill", "--excellon-separate-th", "-o", outdir, pcb],
        check=True, capture_output=True)
    # KiCad 10 writes Finish: "None"; stamp the decided board finish so
    # CAM readers don't get a hole (first-article decision: ENIG). The
    # reader-visible field is GeneralSpecs.Finish — a top-level Finish is
    # off-spec noise that fab parsers ignore (the point of the stamp).
    for jb in glob.glob(os.path.join(outdir, "*.gbrjob")):
        with open(jb) as f:
            job = json.load(f)
        gs = job.get("GeneralSpecs") or {}
        if gs.get("Finish") in (None, "", "None"):
            gs["Finish"] = "ENIG"
            job["GeneralSpecs"] = gs
            with open(jb, "w") as f:
                json.dump(job, f, indent=2)
                f.write("\n")
    subprocess.run(
        [KICAD_CLI, "pcb", "export", "pos", "--format", "csv",
         "--units", "mm", "-o", os.path.join(outdir, "pos.csv"), pcb],
        check=True, capture_output=True)
    subprocess.run(
        [KICAD_CLI, "sch", "export", "bom", "--fields", BOM_FIELDS,
         "-o", os.path.join(outdir, "bom.csv"), sch],
        check=True, capture_output=True)
    # pos-smt.csv: SMD-fab subset (SOD-123 diodes only; everything else hand
    # assembly per spec/bom.md). Derived from pos.csv so both stay in sync.
    with open(os.path.join(outdir, "pos.csv"), newline="") as f:
        rows = list(csv.DictReader(f))
    smt = [r for r in rows if r.get("Package", "") == "D_SOD-123"]
    assert len(smt) == 22, f"{half}: want 22 SMT diodes, got {len(smt)}"
    with open(os.path.join(outdir, "pos-smt.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(smt)
    from check_board import release_drills

    drills = release_drills(outdir, half)
    findings = choc_drill_findings(half, drills[-1]) + component_drill_findings(half, drills)
    if findings:
        sys.exit(f"release cut refused: {half} component drill geometry: "
                 + "; ".join(findings[:3]))
    # ERC/DRC reports are produced FRESH here, on the exact board and
    # schematic that are exported below (audit round 2026-10-21: the cut
    # used to COPY the generator's committed reports, so a hand-edited
    # board shipped with fresh gerbers beside a STALE clean report —
    # the cut's own comment demanded "a failing or stale report must
    # not ride beside fresh gerbers" but only the FAILING case was
    # detected). kicad-cli is already required for the gerber export.
    # DRC uses the same design-frame copy and exact footprint exception
    # set as gen_pcb. The exported drill check above verifies that the
    # manufactured Choc pattern has the correct handedness.
    drc_stem = os.path.join(PCB_DIR, f".release-{half}-drc-design")
    drc_src = drc_stem + ".kicad_pcb"
    copied = [drc_src]
    try:
        with open(drc_src, "w") as f:
            f.write(frame.read_design(
                os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_pcb")))
        # matching project/custom-rule copies: otherwise KiCad falls back
        # to default edge clearance and false-flags the router's edge tracks
        for ext in (".kicad_pro", ".kicad_dru"):
            s = os.path.join(PCB_DIR, f"Hojicha44-{half}{ext}")
            if os.path.exists(s):
                shutil.copyfile(s, drc_stem + ext)
                copied.append(drc_stem + ext)
        for ext, args, src in (
                ("-drc.rpt",
                 ["pcb", "drc", "--severity-all", "--format", "report"],
                 drc_src),
                ("-erc.rpt",
                 ["sch", "erc", "--severity-all", "--format", "report"],
                 os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_sch"))):
            out = os.path.join(outdir, f"Hojicha44-{half}{ext}")
            r = subprocess.run([KICAD_CLI] + args + ["-o", out, src],
                               capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"release cut refused: {half} {ext} run failed "
                         f"(exit {r.returncode}):\n"
                         + (r.stdout + r.stderr)[-400:])
            if not os.path.exists(out) or os.path.getsize(out) == 0:
                sys.exit(f"release cut refused: {half} {ext} is empty — a "
                         f"missing report must never read as clean")
    finally:
        for p in copied:
            if os.path.exists(p):
                os.unlink(p)
    # gate on the reports we just produced (same bytes the fab sees)
    sys.path.insert(0, os.path.join(REPO, "pcb", "generators"))
    import gen_pcb as _gp
    import gen_schematic as _gs
    drc_rc = _gp.check_drc_report(
        os.path.join(outdir, f"Hojicha44-{half}-drc.rpt"), half[0],
        native_choc=True, native_jst=True)
    erc_rc = _gs.check_erc_report(
        os.path.join(outdir, f"Hojicha44-{half}-erc.rpt"), half[0])
    if drc_rc or erc_rc:
        sys.exit(f"release cut refused: {half} report gate failed "
                 f"(drc rc={drc_rc}, erc rc={erc_rc})")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha12(path):
    """Legacy v0.3.1 manifest prefix; new manifests use full sha256."""
    return sha256(path)[:12]


def manifest_lines(reldir):
    man = os.path.join(reldir, "MANIFEST.txt")
    if not os.path.exists(man):
        return []
    return open(man).read().splitlines()


def manifest_value(lines, key):
    """Value of 'key: value' manifest header line, or None."""
    for l in lines:
        if l.startswith(f"{key}: "):
            return l.split(f"{key}: ", 1)[1].strip()
    return None


def verify_release(reldir, with_manifest=True):
    """with_manifest=True (--check/CI): hashes + commit currency + scope.
    with_manifest=False (mid-build): structure only, manifest not written yet."""
    bad = []
    lines = manifest_lines(reldir)
    if with_manifest and not lines:
        return ["MANIFEST.txt missing or empty"]
    if with_manifest:
        tops = sorted(os.listdir(reldir))
        if tops != ["Left", "MANIFEST.txt", "Right"]:
            bad.append(f"unexpected release top-level: {tops} (clean-cut only)")
    # every listed file must still hash to its manifest digest (the manifest
    # is the tamper evidence; eb6678f was caught shipping stale gerbers
    # beside a re-pointed manifest exactly because nothing re-verified).
    # v0.4.0+ writes full sha256; accept 12-hex v0.3.1 manifests for history.
    for half in ("Left", "Right"):
        d = os.path.join(reldir, half)
        if not os.path.isdir(d):
            bad.append(f"{half}/ missing")
            continue
        files = sorted(os.listdir(d))
        gerbers = [f for f in files if f.endswith(
            (".gbl", ".gbs", ".gbp", ".gbo", ".gm1", ".gtl",
             ".gts", ".gtp", ".gto"))]
        for want in ("pos.csv", "pos-smt.csv", "bom.csv",
                     f"Hojicha44-{half}-erc.rpt", f"Hojicha44-{half}-drc.rpt"):
            p = os.path.join(d, want)
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                bad.append(f"{half}/{want} missing or empty")
        if len(gerbers) != 9:
            bad.append(f"{half}: want 9 gerbers, got {len(gerbers)}")
        if not any(f.endswith(".gbrjob") for f in files):
            bad.append(f"{half}: job file missing")
        from check_board import release_drills

        try:
            drills = release_drills(d, half)
        except ValueError as err:
            bad.append(str(err))
        else:
            if len(drills) != 2:
                bad.append(f"{half}: current release requires separate PTH and NPTH drill files")
            if with_manifest:
                findings = choc_drill_findings(half, drills[-1]) + component_drill_findings(half, drills)
                if findings:
                    bad.append(f"{half}: {len(findings)} component drill findings "
                               f"(first: {findings[0]})")
        for f in files:
            p = os.path.join(d, f)
            if os.path.getsize(p) == 0:
                bad.append(f"{half}/{f} empty")
        if with_manifest:
            listed = {}
            started = False
            for l in lines:
                if l.startswith(f"[{half}]"):
                    started = True
                    continue
                if started and l.startswith("["):
                    break
                if started:
                    m = re.match(
                        r"^  ([0-9a-f]{12}|[0-9a-f]{64})  (\S+)$", l)
                    if not m:
                        bad.append(f"{half}: unparseable manifest line {l!r}")
                        continue
                    listed[m.group(2)] = m.group(1)
            if len(listed) != len(files):
                bad.append(f"{half}: manifest lists {len(listed)} files, "
                           f"dir has {len(files)}")
            for f, want_hash in listed.items():
                if not os.path.exists(os.path.join(d, f)):
                    bad.append(f"{half}/{f} in manifest but missing on disk")
                    continue
                p = os.path.join(d, f)
                got_hash = (sha256(p) if len(want_hash) == 64
                            else sha12(p))
                if got_hash != want_hash:
                    bad.append(f"{half}/{f} hash {got_hash} != manifest "
                               f"{want_hash} (stale content or edited artifact)")
            for f in files:
                if f not in listed:
                    bad.append(f"{half}/{f} on disk but not in manifest")
    # the manifest must claim the CURRENT board-affecting commit, else the
    # gerbers were exported from older boards
    if with_manifest:
        head = board_commit()
        cmt = manifest_value(lines, "git commit")
        if cmt != head:
            bad.append(f"manifest commit {cmt} != board-affecting HEAD {head} "
                       f"(- boards changed since the cut; re-run make_release)")
        # and it must certify the board BYTES it was cut from, so a local
        # edit cannot ride under an unchanged commit stamp.
        bh = manifest_value(lines, "board sha256") or ""
        m = re.match(
            r"Left ([0-9a-f]{12}|[0-9a-f]{64})  "
            r"Right ([0-9a-f]{12}|[0-9a-f]{64})$", bh)
        if not m:
            bad.append("manifest board sha256 line missing/unparseable")
        else:
            for half, want in (("Left", m.group(1)), ("Right", m.group(2))):
                p = os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_pcb")
                got = sha256(p) if len(want) == 64 else sha12(p)
                if got != want:
                    bad.append(
                        f"{half} board hash {got} != manifest {want} "
                        f"(board changed since the cut)")
    return bad


def main():
    check_only = "--check" in sys.argv
    ver = spec_version()
    reldir = os.path.join(REPO, "generated", "release", f"v{ver}")
    bhead = board_commit()
    if check_only:
        bad = verify_release(reldir)
        print(f"release {reldir}: "
              f"{'CLEAN' if not bad else 'FAIL'} (boards @{bhead[:12]})")
        for b in bad:
            print(f"  !! {b}")
        sys.exit(1 if bad else 0)
    # refuse a dirty tree: the manifest certifies committed sources only.
    # Untracked junk cannot be referenced by any generator input, so it
    # only warrants a note; a modified tracked file would silently ship.
    st = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                        text=True, cwd=REPO).stdout.splitlines()
    mod = [l for l in st if not l.startswith("??")]
    if mod:
        sys.exit("release cut refused: committed tree is dirty "
                 "(commit first — the manifest certifies committed "
                 "sources):\n" + "\n".join(mod[:12]))
    if st:
        print(f"  note: {len(st)} untracked file(s) present (not certified)")
    _, tree_stamp = git_info()
    parent = os.path.dirname(reldir)
    os.makedirs(parent, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cut-", dir=parent) as temp:
        staged = os.path.join(temp, "staged")
        cli, router = cut_release(staged, ver, bhead, tree_stamp)
        backup = os.path.join(temp, "previous")
        if os.path.exists(reldir):
            os.rename(reldir, backup)
        try:
            os.rename(staged, reldir)
        except BaseException:
            if os.path.exists(backup):
                os.rename(backup, reldir)
            raise
    print(f"release v{ver}: {reldir}")
    print(f"  spec {ver} boards @{bhead[:12]} router {router} cli {cli[:24]}")
    print("  CLEAN: 9 gerbers + job + split drills + pos + pos-smt + bom + erc + drc per half")


def cut_release(reldir, ver, bhead, tree_stamp):
    cli, router = tool_versions()
    for half in ("Left", "Right"):
        export_half(half, os.path.join(reldir, half))
    bad = verify_release(reldir, with_manifest=False)
    if bad:  # surface BEFORE hashing so a broken cut never self-certifies
        print(f"release v{ver}: export FAILED:")
        for b in bad:
            print(f"  !! {b}")
        sys.exit(1)
    board_hash = {
        half: sha256(os.path.join(PCB_DIR, f"Hojicha44-{half}.kicad_pcb"))
        for half in ("Left", "Right")}
    lines = [
        "Hojicha44 release manifest",
        f"spec version: {ver}",
        # commit the boards were exported from (NOT repo HEAD — case, docs
        # and firmware commits must not flag the release stale)
        f"git commit: {bhead}",
        f"git tag: {tree_stamp}",
        f"router: gen_route.py {router}",
        f"kicad-cli: {cli}",
        # the board bytes this release certifies (audit round 2026-10-21:
        # the manifest named a COMMIT but not the board's hash, so a
        # hand-edited board could ride along under a clean commit stamp)
        f"board sha256: Left {board_hash['Left']}  Right {board_hash['Right']}",
        "ERC: 0 errors + 5 documented spare warnings/half (check_erc_report gate)",
        "DRC: 0 non-waived (exact W1 set of 47/half asserted); "
        "unconnected NOT waived; PTH/NPTH-in-courtyard = error",
        "reports: ERC on the exported schematic; DRC on the design-frame "
        "reflection of the exported y-negated board (same physical "
        "geometry, same project rules) at cut time",
        "",
    ]
    for half in ("Left", "Right"):
        d = os.path.join(reldir, half)
        files = sorted(os.listdir(d))
        lines.append(f"[{half}] {len(files)} files")
        for f in files:
            lines.append(f"  {sha256(os.path.join(d, f))}  {f}")
    open(os.path.join(reldir, "MANIFEST.txt"), "w").write("\n".join(lines) + "\n")
    return cli, router


if __name__ == "__main__":
    main()
