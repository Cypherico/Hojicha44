"""Hojicha44 — molab master-render notebook (marimo).

Renders the committed render programme at 4800x2700 / 4096 samples on a
molab notebook with an attached RTX PRO 6000 Blackwell GPU.

Sync/upload this file to molab, attach the GPU, run the cells top to
bottom, wait, download. See the first cell for the operating notes.

The notebook never edits the repo on GitHub; it clones (or hard-resets
to) the tip of `main`, then applies a small set of anchored runtime
patches to the checkout (OptiX device path + adaptive quality + frame
rescue in scene.py, silk-font env in pcb_tex.py, BSD-stat portability in
fetch_keycaps.sh). Anchors are asserted: upstream drift fails loudly
instead of half-patching.

This file is a marimo notebook: `python molab_hires_render.py` executes
it as a script, `marimo edit renders/molab_hires_render.py` opens it.
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md(
        r"""
        # Hojicha44 — molab master renders (RTX PRO 6000)

        **4800x2700 · 4096 samples · OptiX denoise · exact 16:9** — the
        full shot programme, the three priority shots first.

        ## Before you run anything

        1. **Attach the GPU** (notebook specs button — RTX PRO 6000). The
           notebook hard-stops without a GPU; a CPU attempt at these
           settings is a multi-day trap.
        2. **Push the state you want rendered.** The notebook pulls the
           tip of the repo from GitHub fresh on every run — nothing is
           pinned. The commit SHA it will render is printed and lands in
           the delivery manifest. Un-pushed local work is not seen.
        3. Know the session limits: molab shuts notebooks down after
           **12 hours**, and after **90 minutes idle**.

        ## How to run

        - Run the cells top to bottom, **or** click ▶ on *RENDER — the
          three* and marimo first runs the whole chain above it
          (bootstrap → smoke test → framecheck → renders). The same
          one-click trick works on any cell.
        - Provision trusted Blender, KiCad and CAD Python before running.
          See renders/README.md for the environment settings. The three priority shots follow in ~2–4 h.
        - *DOWNLOAD — the three* appears right after; grab the PNGs.
        - For the rest of the programme: set `GO_REST = True` in the
          gate cell and run it — the remaining shots render (bright/dark
          top + orbit, play top, artisan, env desk/mat/dev/gaming), and
          the final cell downloads everything with a hashed manifest.

        ## Notes

        - The sandbox disk is **ephemeral** — files do not survive a
          session. That is why the three priorities render first and are
          downloadable before the long tail runs; whatever the session
          does not finish waits for the next run.
        - Every stage caches on **git SHA + render settings**: accidental
          re-runs are cheap no-ops, and renders only restart when the
          tree or the settings actually change.
        - Failures name their log: each stage prints the exact file under
          `_molab_render/logs/` to inspect.
        - The runtime patches touch the sandbox checkout only.
        """
    )
    return (mo,)


@app.cell
def _():
    import hashlib
    import json
    import os
    import platform
    import re
    import shutil
    import subprocess
    import sys
    import time
    import zipfile
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    return (
        ThreadPoolExecutor,
        Path,
        hashlib,
        json,
        os,
        platform,
        re,
        shutil,
        subprocess,
        sys,
        time,
        zipfile,
    )


@app.cell
def _():
    # ------------------------------------------------------------------
    # config — edit freely; every stage caches on git SHA + this config
    # ------------------------------------------------------------------
    CFG = {
        "notebook": "molab-hires v1.1",
        "repo_url": "https://github.com/BitPeppr/Hojicha44.git",
        # 4800x2700 = 12.96 MP, exact 16:9. All cameras (composed at
        # 16:10) were pre-flight verified to fit this frame; jobs that
        # ever clip get an automatic composition-preserving zoom-out.
        "res": "4800x2700",
        # 4096 max samples/pixel; adaptive trims flat regions, the
        # threshold below keeps the hard pixels working to ~1-3k.
        "samples": 4096,
        "adaptive_threshold": "0.002",
        "device": "optix",            # optix | cuda | cpu
        "frame_rescue": True,         # auto zoom-out for clipped shots
        "run_smoke": True,            # 800x500 E2E proof before the queue
        "run_framecheck": True,       # NDC pre-flight for every job
        "force": False,               # True = re-render even if recorded
        "rebuild_assets": False,      # True = rebuild even if fingerprint ok
    }

    # The rendered programme. No `out` = generated/renders/v0.5.0.
    # PRIORITY_IDS render first; everything else follows in the "rest"
    # batch after the gate. Edit/delete lines freely — nothing else in
    # the notebook knows shot names.
    QUEUE = [
        dict(id="play_hero", script="scene",
             args=["--colourway", "play", "--setups", "bright",
                   "--shots", "hero"],
             out="generated/renders/play", expect=["bright/hero.png"],
             note="play colourway, airborne toss pose"),
        dict(id="bright_hero", script="scene",
             args=["--colourway", "bright", "--setups", "bright",
                   "--shots", "hero"],
             expect=["bright/hero.png"], note="standard colourway hero"),
        dict(id="bright_exploded", script="scene",
             args=["--colourway", "bright", "--setups", "bright",
                   "--shots", "exploded", "--stack-colors"],
             expect=["bright/exploded.png"],
             note="exploded diagram, stack palette"),
        dict(id="bright_top", script="scene",
             args=["--setups", "bright", "--shots", "top"],
             expect=["bright/top.png"], note="orthographic layout proof"),
        dict(id="bright_orbit", script="scene",
             args=["--setups", "bright", "--shots", "orbit"],
             expect=["bright/orbit_02.png", "bright/orbit_08.png"],
             note="turntable keepers 02/08"),
        dict(id="dark_hero", script="scene",
             args=["--colourway", "dark", "--setups", "dark",
                   "--shots", "hero"],
             expect=["dark/hero.png"], note="stealth colourway hero"),
        dict(id="dark_top", script="scene",
             args=["--colourway", "dark", "--setups", "dark",
                   "--shots", "top"],
             expect=["dark/top.png"], note="stealth top"),
        dict(id="dark_orbit", script="scene",
             args=["--colourway", "dark", "--setups", "dark",
                   "--shots", "orbit"],
             expect=["dark/orbit_02.png", "dark/orbit_08.png"],
             note="stealth turntable keepers"),
        dict(id="play_top", script="scene",
             args=["--colourway", "play", "--setups", "bright",
                   "--shots", "top"],
             out="generated/renders/play", expect=["bright/top.png"],
             note="play top"),
        dict(id="artisan", script="scene",
             args=["--colourway", "artisan", "--setups", "bright",
                   "--shots", "artisan"],
             out="generated/renders/artisan",
             expect=["bright/artisan.png"],
             note="sculpted accent-cap shot"),
        dict(id="env_desk_mat", script="env",
             args=["--shots", "desk,mat"],
             expect=["env/desk.png", "env/mat.png"],
             note="desk environment (wireless) + mat closeup"),
        dict(id="env_dev", script="env",
             args=["--shots", "dev"],
             expect=["env/dev.png"], note="dev-desk scene"),
        dict(id="env_gaming", script="env",
             args=["--shots", "gaming"],
             expect=["env/gaming.png"],
             note="gaming scene (clipped 16:9 on the Mac check -> the "
                  "frame rescue will zoom out a measured step)"),
    ]

    PRIORITY_IDS = ["play_hero", "bright_hero", "bright_exploded"]
    _ids = [j["id"] for j in QUEUE]
    assert len(_ids) == len(set(_ids)), "duplicate job id in QUEUE"
    assert set(PRIORITY_IDS) <= set(_ids), "PRIORITY_IDS not all in QUEUE"
    assert CFG["device"] in ("optix", "cuda", "cpu")
    return CFG, PRIORITY_IDS, QUEUE


@app.cell
def _(CFG, Path, mo, os, platform, shutil, subprocess, sys):
    # ------------------------------------------------------------------
    # environment check — hard gate on the GPU
    # ------------------------------------------------------------------
    WORK = Path.cwd() / "_molab_render"
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "logs").mkdir(exist_ok=True)

    if not shutil.which("git"):
        raise RuntimeError("git is not on PATH in this sandbox — cannot "
                           "clone the repo. Report this on the molab "
                           "discord; every current image ships git.")

    gpu_line = None
    try:
        proc = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=60)
        if proc.returncode == 0 and proc.stdout.strip():
            gpu_line = proc.stdout.strip().splitlines()[0]
    except FileNotFoundError:
        pass

    free_gb = shutil.disk_usage(str(WORK)).free / 1e9
    # container overlay filesystems can report absurd "free" values
    # (2^63-ish bytes); show them honestly instead of a fake number
    if free_gb >= 1e6:
        free_txt = "unbounded (container overlay reports no real limit)"
        free_gb = -1.0
    else:
        free_txt = f"{free_gb:.1f} GB"

    ENV = {
        "cwd": str(Path.cwd()),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "gpu": gpu_line or "",
        "free_gb": free_gb,
    }

    if gpu_line is None:
        raise RuntimeError(
            "No GPU visible (nvidia-smi failed).\n"
            "Attach the RTX PRO 6000 via the notebook specs button in "
            "the molab header, then re-run this cell. A CPU render at "
            "these settings would take days — this notebook refuses to "
            "try.")

    mo.md(
        f"""
        | | |
        |---|---|
        | GPU | `{gpu_line}` |
        | Free disk | **{free_txt}** |
        | Python | {ENV['python']} · {ENV['platform']} |
        | Work dir | `{WORK}` |

        Config: **{CFG['res']} @ {CFG['samples']} samples**, device
        `{CFG['device']}`, adaptive `{CFG['adaptive_threshold']}`.
        """
    )
    return (ENV, WORK)


@app.cell
def _(Path, hashlib, os, re, subprocess, time):
    # ------------------------------------------------------------------
    # toolkit — shared process/network helpers (the only cell importing
    # these stdlib modules; every other cell calls in here)
    # ------------------------------------------------------------------

    def run_capture(cmd, env=None, cwd=None, timeout=None):
        """Run to completion; returns (rc, combined stdout+stderr)."""
        r = subprocess.run([str(c) for c in cmd], env=env,
                           cwd=None if cwd is None else str(cwd),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout,
                           text=True, errors="replace")
        return r.returncode, r.stdout

    def run_stream(cmd, env, cwd, log_path, on_tick=None):
        """Run with byte streaming to a log + progress callbacks.

        on_tick(progress_pair_or_None, elapsed_seconds) fires whenever
        the Cycles 'Sample: n/m' counter changes, and at least every 30 s
        as a heartbeat. Returns (rc, seconds).
        """
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        proc = subprocess.Popen(
            [str(c) for c in cmd], cwd=str(cwd), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        buf = b""
        last = None
        last_cb = t0
        try:
            with open(log_path, "wb") as fh:
                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    fh.write(chunk)
                    buf = (buf + chunk)[-12000:]
                    m = re.findall(rb"Sample:\s*(\d+)/(\d+)", buf)
                    prog = (m[-1][0].decode(), m[-1][1].decode()) \
                        if m else None
                    now = time.time()
                    if on_tick is not None and (
                            prog != last or now - last_cb > 30.0):
                        last = prog
                        last_cb = now
                        on_tick(prog, now - t0)
        except KeyboardInterrupt:
            proc.kill()
            proc.wait()
            raise
        return proc.wait(), time.time() - t0

    def sha256_file(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    return run_capture, run_stream, sha256_file


@app.cell
def _(Path, mo, os, shutil, subprocess):
    executable = os.environ.get("H44_BLENDER") or shutil.which("blender")
    if not executable:
        raise RuntimeError("Provision Blender and set H44_BLENDER.")
    BLENDER = Path(executable).resolve(strict=True)
    BLENDER_VER = subprocess.check_output(
        [str(BLENDER), "--version"], text=True).splitlines()[0]
    mo.md(f"**Blender ready:** `{BLENDER_VER}`")
    return BLENDER, BLENDER_VER


@app.cell
def _(Path, WORK, mo, os, shutil, subprocess):
    executable = os.environ.get("H44_KICAD_CLI") or shutil.which("kicad-cli")
    models = os.environ.get("KICAD10_3DMODEL_DIR")
    if not executable or not models or not Path(models).is_dir():
        raise RuntimeError("Provision KiCad CLI and set KICAD10_3DMODEL_DIR.")
    KICAD_CLI = Path(executable).resolve(strict=True)
    KICAD_ENV = {
        "KICAD_CONFIG_HOME": str(WORK / "kicad-config"),
        "KICAD10_3DMODEL_DIR": str(Path(models).resolve()),
    }
    KICAD_VER = subprocess.check_output(
        [str(KICAD_CLI), "version"], env={**os.environ, **KICAD_ENV},
        text=True).strip()
    mo.md(f"**KiCad ready:** `{KICAD_VER}`")
    return KICAD_CLI, KICAD_ENV, KICAD_VER


@app.cell
def _(Path, mo, os, subprocess):
    executable = os.environ.get("H44_RENDER_PYTHON")
    if not executable:
        raise RuntimeError("Set H44_RENDER_PYTHON to a provisioned CAD environment.")
    VENV_PY = Path(executable).absolute()
    VENV_BIN = VENV_PY.parent
    subprocess.run([str(VENV_PY), "-c",
                    "import cadquery, trimesh, ezdxf; from PIL import Image"],
                   check=True)
    SILK_FONT = os.environ.get("H44_SILK_FONT")
    mo.md(f"**CAD Python ready:** `{VENV_PY}`")
    return SILK_FONT, VENV_BIN, VENV_PY


@app.cell
def _(CFG, Path, WORK, mo, run_capture):
    # ------------------------------------------------------------------
    # repo — clone on first run, then hard-reset to the GitHub tip on
    # every run. Nothing is pinned: what you push is what renders.
    # ------------------------------------------------------------------
    REPO_TMP = str(WORK / "repo")
    if (WORK / "repo/.git").exists():
        rc, out = run_capture(["git", "-C", REPO_TMP, "fetch", "--depth",
                               "1", "origin", "HEAD"])
        if rc == 0:
            rc, out = run_capture(["git", "-C", REPO_TMP, "reset",
                                   "--hard", "FETCH_HEAD"])
        else:
            rc, out = run_capture(["git", "-C", REPO_TMP, "fetch",
                                   "--depth", "1", "origin"])
            if rc == 0:
                rc, out = run_capture(["git", "-C", REPO_TMP, "reset",
                                       "--hard", "FETCH_HEAD"])
        if rc != 0:
            raise RuntimeError("git fetch/reset failed:\n" + out[-1500:])
    else:
        print("  cloning (first run) ...", flush=True)
        rc, out = run_capture(["git", "clone", "--depth", "1",
                               CFG["repo_url"], REPO_TMP], timeout=600)
        if rc != 0:
            raise RuntimeError("git clone failed — is the repo reachable "
                               "and public?\n" + out[-1500:])
    _, sha_txt = run_capture(["git", "-C", REPO_TMP, "rev-parse", "HEAD"])
    SHA = sha_txt.strip()
    _, subj_txt = run_capture(
        ["git", "-C", REPO_TMP, "log", "-1", "--format=%s | %ad",
         "--date=iso"])
    SHA_SUBJECT = subj_txt.strip()
    SHA_SHORT = SHA[:7]
    _, dirty = run_capture(["git", "-C", REPO_TMP, "status", "--porcelain"])
    REPO = Path(REPO_TMP)
    print(f"  rendering {SHA_SHORT}: {SHA_SUBJECT}", flush=True)
    if dirty.strip():
        print(f"  ({len(dirty.splitlines())} untracked build paths on "
              f"disk — fine)", flush=True)
    mo.md(f"**Repo @ `{SHA_SHORT}`** — {SHA_SUBJECT}\n\n"
          f"Everything below renders this exact commit; re-push and "
          f"re-run this cell to move the whole chain forward.")
    return REPO, SHA, SHA_SHORT, SHA_SUBJECT


@app.cell
def _(REPO, mo):
    # ------------------------------------------------------------------
    # runtime patches — re-applied to the fresh checkout on every run.
    # The GitHub repo is untouched; anchors are asserted so upstream
    # drift fails loudly instead of half-patching.
    # ------------------------------------------------------------------
    def _apply(rel, old, new, label, sentinel):
        p = REPO / rel
        src = p.read_text()
        if sentinel in src:
            return label, "already applied"
        if src.count(old) != 1:
            raise RuntimeError(
                f"[patch] anchor not found exactly once in {rel} "
                f"({label}) — upstream changed this code; update the "
                f"notebook's patch list.")
        p.write_text(src.replace(old, new, 1))
        return label, "applied"

    PATCHES = []

    PATCHES.append(_apply(
        "renders/scene.py",
        'choices=["metal", "cpu"])',
        'choices=["metal", "cpu", "optix", "cuda"])',
        "scene.py: --device accepts optix/cuda",
        'choices=["metal", "cpu", "optix", "cuda"])'))

    PATCHES.append(_apply(
        "renders/scene.py",
        '''    if device == "metal":
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
        except Exception as e:
            print("  (GPU setup unavailable, CPU render):", e)
    else:
        sc.cycles.device = "CPU"''',
        '''    if device in ("optix", "cuda"):
        # [molab patch] RTX path: OptiX (or CUDA) compute + OptiX denoise
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX" if device == "optix" else "CUDA"
        prefs.get_devices()
        enabled = 0
        for d in prefs.devices:
            if getattr(d, "type", "") in ("OPTIX", "CUDA"):
                d.use = True
                enabled += 1
        if not enabled:
            raise RuntimeError(
                "[molab] no CUDA/OptiX device visible to Cycles - attach "
                "the GPU in the molab specs and re-run")
        sc.cycles.device = "GPU"
        if device == "optix":
            try:
                sc.cycles.denoiser = "OPTIX"
            except Exception:
                pass
        print("  [molab] cycles GPU:", prefs.compute_device_type,
              "| enabled:", enabled, flush=True)
    elif device == "metal":
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
        except Exception as e:
            print("  (GPU setup unavailable, CPU render):", e)
    else:
        sc.cycles.device = "CPU"''',
        "scene.py: optix/cuda device branch",
        "[molab patch] RTX path"))

    PATCHES.append(_apply(
        "renders/scene.py",
        """    sc.cycles.samples = samples
    sc.cycles.use_denoising = True""",
        """    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    # [molab patch] master-quality adaptive sampling (env-driven)
    _molab_thr = os.environ.get("H44_ADAPTIVE_THRESHOLD", "")
    if _molab_thr:
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = float(_molab_thr)""",
        "scene.py: adaptive threshold via env", "_molab_thr"))

    PATCHES.append(_apply(
        "renders/scene.py",
        """def add_cam(name, loc, look_at, lens=50):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    co = bpy.data.objects.new(name, cam)
    co.location = loc""",
        """def _molab_frame_rescue():
    # [molab patch] 16:9 frame rescue: >1 zooms every camera out without
    # moving it (lens / ortho scale), so a clip at a new aspect is fixed
    # at composition-preserving cost.
    try:
        return max(1.0, float(os.environ.get("H44_FRAME_RESCUE", "1")))
    except ValueError:
        return 1.0


def add_cam(name, loc, look_at, lens=50):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens / _molab_frame_rescue()
    co = bpy.data.objects.new(name, cam)
    co.location = loc""",
        "scene.py: frame-rescue zoom hook", "def _molab_frame_rescue"))

    PATCHES.append(_apply(
        "renders/scene.py",
        "            cam.data.ortho_scale = 0.44",
        "            cam.data.ortho_scale = 0.44 * _molab_frame_rescue()",
        "scene.py: frame rescue on the ortho top cam",
        "0.44 * _molab_frame_rescue()"))

    PATCHES.append(_apply(
        "renders/pcb_tex.py",
        "FONT_CANDIDATES = (",
        'FONT_CANDIDATES = (\n    os.environ.get("H44_SILK_FONT", ""),',
        "pcb_tex.py: silk font via env", "H44_SILK_FONT"))

    PATCHES.append(_apply(
        "renders/fetch_keycaps.sh",
        '$(stat -f%z "$f")',
        "$(wc -c < \"$f\" | tr -d ' ')",
        "fetch_keycaps.sh: BSD stat -> portable wc", "wc -c <"))

    mo.md("**Runtime patches** (checkout-only, re-applied every run):\n\n"
          + "\n".join(f"- {lbl} — **{state}**" for lbl, state in PATCHES))
    return (PATCHES,)


@app.cell
def _(CFG, KICAD_CLI, KICAD_ENV, PATCHES, REPO, VENV_BIN, VENV_PY, WORK,
      json, mo, os, sha256_file, subprocess):
    # ------------------------------------------------------------------
    # assets — full self-build (the documented recipe, verbatim):
    # keycaps -> case generators -> build_assets (kicad-cli STEP export,
    # plate/knob/switch solids, placements + cutouts)
    # ------------------------------------------------------------------
    assert PATCHES, "patch cell must run first"
    assets = REPO / "generated/renders/assets"
    state_p = WORK / "state.json"
    st = json.loads(state_p.read_text()) if state_p.exists() else {}

    # fingerprint of the board-affecting artifacts: rebuild only when
    # they change, files are missing, or CFG.rebuild_assets forces it
    fp = ""
    for rel in ("pcb/kicad/Hojicha44-Left.kicad_pcb",
                "pcb/kicad/Hojicha44-Right.kicad_pcb",
                "plate/Hojicha44-Left-plate.dxf",
                "plate/Hojicha44-Right-plate.dxf",
                "case/out/Hojicha44-Left-tub.step",
                "case/out/Hojicha44-Left-cover.step",
                "case/out/Hojicha44-Right-tub.step",
                "case/out/Hojicha44-Right-cover.step"):
        p = REPO / rel
        fp += sha256_file(p)[:12] if p.exists() else "missing"

    expected = [
        "board/Hojicha44-Left.glb", "board/Hojicha44-Right.glb",
        "plate/Hojicha44-Left.glb", "plate/Hojicha44-Right.glb",
        "case/Hojicha44-Left-tub.glb", "case/Hojicha44-Left-cover.glb",
        "case/Hojicha44-Right-tub.glb", "case/Hojicha44-Right-cover.glb",
        "parts/choc.glb", "parts/nano.glb", "parts/knob.glb", "parts/artisan.glb",
        "parts/klp_normal_tilted.glb", "parts/klp_saddle.glb",
        "placements.json", "cutouts.json",
    ]
    have_all = all((assets / e).exists() for e in expected)
    fresh = st.get("assets_fp") == fp

    if have_all and fresh and not CFG["rebuild_assets"]:
        print("  assets present, fingerprint matches — skipping",
              flush=True)
        ASSETS_OK = "reused"
        mo.md("**Assets reused** — fingerprint matches the committed "
              "boards/plate/case.")
        return (ASSETS_OK,)

    print("  building assets (10-25 min total) ...", flush=True)

    # 1. keycaps: require the verified repository fetch.
    capdir = WORK / "keycaps"
    capdir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["KEYCAP_DIR"] = str(capdir)
    print("  keycaps: repo fetch script ...", flush=True)
    r = subprocess.run(["bash", "renders/fetch_keycaps.sh"],
                       cwd=str(REPO), env=env, capture_output=True,
                       text=True)
    tail = (r.stdout or "") + (r.stderr or "")
    print("   " + tail[-400:].replace("\n", "\n   "), flush=True)
    if r.returncode:
        raise RuntimeError(f"Pinned keycap fetch failed:\n{tail[-1200:]}")

    env.update({
        "CASE_OUT": str(REPO / "case/out-dev"),
        "KEYCAP_DIR": str(capdir),
        "KICAD_CLI": str(KICAD_CLI),
    })
    env.update(KICAD_ENV)
    env["PATH"] = str(VENV_BIN) + os.pathsep + env.get("PATH", "")

    # 2. case generators (the thin-top recipe from renders/README.md)
    for script in ("case/gen_case.py", "case/gen_cover.py"):
        print(f"  {script} ...", flush=True)
        r = subprocess.run([str(VENV_PY), script], cwd=str(REPO),
                           env=env, capture_output=True, text=True,
                           timeout=3600)
        if r.returncode != 0:
            raise RuntimeError(f"{script} failed:\n"
                               + ((r.stdout or "")
                                  + (r.stderr or ""))[-2500:])
        print("   " + (r.stdout or "")[-500:].replace("\n", "\n   "),
              flush=True)

    # 3. build_assets (board STEP -> glb, plate, knob, choc, artisan...)
    print("  renders/build_assets.py (the long one) ...", flush=True)
    r = subprocess.run([str(VENV_PY), "renders/build_assets.py"],
                       cwd=str(REPO), env=env, capture_output=True,
                       text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("build_assets failed:\n"
                           + ((r.stdout or "")
                              + (r.stderr or ""))[-2500:])
    print("   " + (r.stdout or "")[-1200:].replace("\n", "\n   "),
          flush=True)

    miss = [e for e in expected if not (assets / e).exists()]
    if miss:
        raise RuntimeError(f"asset build incomplete, missing: {miss}")

    st["assets_fp"] = fp
    state_p.write_text(json.dumps(st, indent=1))
    ASSETS_OK = "built"
    mo.md(f"**Assets built** — {len(expected)} artifacts, fingerprint "
          f"`{fp[:8]}`.")
    return (ASSETS_OK,)


@app.cell
def _(ASSETS_OK, BLENDER, BLENDER_VER, CFG, ENV, KICAD_CLI, KICAD_ENV,
      KICAD_VER, PRIORITY_IDS, QUEUE, REPO, SHA, SHA_SHORT, SHA_SUBJECT,
      SILK_FONT, VENV_PY, WORK, hashlib, json, mo, os, run_capture,
      run_stream, sha256_file, time, zipfile):
    # ------------------------------------------------------------------
    # engine — job model, state cache, render runner, delivery UI.
    # Everything after this cell is thin.
    # ------------------------------------------------------------------
    assert ASSETS_OK, "assets cell must run first"
    STATE_P = WORK / "state.json"

    def load_state():
        return json.loads(STATE_P.read_text()) if STATE_P.exists() else {}

    def save_state(st):
        STATE_P.write_text(json.dumps(st, indent=1))

    def cfg_fp():
        c = {k: CFG[k] for k in ("res", "samples", "adaptive_threshold",
                                 "device")}
        return hashlib.sha256(
            json.dumps(c, sort_keys=True).encode()).hexdigest()[:16]

    def job_dir(job):
        return REPO / job.get("out", "generated/renders/v0.5.0")

    def job_outputs(job):
        return [job_dir(job) / rel for rel in job["expect"]]

    def base_env(rescue=None):
        e = os.environ.copy()
        e["PATH"] = str(VENV_PY.parent) + os.pathsep + e.get("PATH", "")
        e["H44_ADAPTIVE_THRESHOLD"] = str(CFG["adaptive_threshold"])
        e["BLENDER_USER_CONFIG"] = str(WORK / "blender-config")
        if SILK_FONT:
            e["H44_SILK_FONT"] = str(SILK_FONT)
        e["KICAD_CLI"] = str(KICAD_CLI)
        # 3D-model dirs are harmless; LD_LIBRARY_PATH is deliberately
        # NOT forwarded — renders never invoke KiCad, and KiCad's bundled
        # libs must not shadow Blender's/cadquery's dynamic libraries
        e.update({k: v for k, v in KICAD_ENV.items()
                  if k != "LD_LIBRARY_PATH"})
        if rescue and float(rescue) > 1.0:
            e["H44_FRAME_RESCUE"] = str(rescue)
        else:
            e.pop("H44_FRAME_RESCUE", None)
        return e

    def cmd_for(job, framecheck=False):
        script = "renders/scene_env.py" if job["script"] == "env" \
            else "renders/scene.py"
        cmd = [str(BLENDER), "--background", "--python", script, "--"]
        cmd += list(job["args"])
        if framecheck:
            cmd += ["--framecheck"]
        cmd += ["--samples", str(CFG["samples"]),
                "--res", CFG["res"], "--device", CFG["device"]]
        if job.get("out"):
            cmd += ["--out", str(job_dir(job))]
        return cmd

    def _cost_unit():
        w, h = (int(v) for v in CFG["res"].split("x"))
        return (w * h / 1e6) * int(CFG["samples"])

    def _job_skip(job, st):
        if CFG["force"]:
            return False
        e = st.get("jobs", {}).get(job["id"])
        if not e or e.get("sha") != SHA or e.get("cfg") != cfg_fp():
            return False
        return all(p.exists() and p.stat().st_size > 10_000
                   for p in job_outputs(job))

    def _table(rows):
        out = ["| job | status | detail |", "|---|---|---|"]
        for r in rows:
            out.append(f"| `{r[0]}` | {r[1]} | {r[2]} |")
        return "\n".join(out)

    def run_batch(jobs, label):
        """Render a job list sequentially; display live; never raises."""
        st = load_state()
        rows, ok, skipped, failed = [], [], [], []
        for job in jobs:
            if _job_skip(job, st):
                e = st["jobs"][job["id"]]
                rows.append((job["id"], "skipped",
                             f"done {e.get('seconds', 0) / 60:.0f} min "
                             f"@ {e['sha'][:7]}"))
                skipped.append(job["id"])
                continue
            rescue = st.get("framecheck", {}).get(job["id"], {}) \
                .get("factor", 1.0)

            def _tick(prog, elapsed, job=job):
                cur = list(rows)
                if prog:
                    total = max(1, int(prog[1]))
                    pct = int(int(prog[0]) * 100 / total)
                    det = (f"sample {prog[0]}/{prog[1]} ({pct}%), "
                           f"{elapsed / 60:.1f} min")
                else:
                    det = f"{elapsed / 60:.1f} min (scene build/denoise)"
                cur.append((job["id"], "**rendering**", det))
                mo.output.replace(mo.md(f"### {label}\n\n" + _table(cur)))

            rows.append((job["id"], "rendering", "starting ..."))
            mo.output.replace(mo.md(f"### {label}\n\n" + _table(rows)))
            log = WORK / "logs" / f"{job['id']}.log"
            rc, secs = run_stream(cmd_for(job), base_env(rescue), REPO,
                                  log, on_tick=_tick)
            missing = [p for p in job_outputs(job)
                       if not p.exists() or p.stat().st_size < 10_000]
            if rc != 0 or missing:
                tail = log.read_text(errors="replace")[-700:] \
                    if log.exists() else ""
                failed.append(job["id"])
                rows[-1] = (job["id"], "**FAILED**",
                            f"rc {rc}, {len(missing)} missing; log "
                            f"`{log.name}`")
                mo.output.replace(mo.md(f"### {label}\n\n" + _table(rows)
                                        + f"\n\n```\n{tail}\n```"))
                break
            st.setdefault("jobs", {})[job["id"]] = {
                "sha": SHA, "cfg": cfg_fp(), "seconds": round(secs, 1),
                "rescue": rescue, "done": time.strftime("%Y-%m-%d %H:%M"),
                "files": {str(p.relative_to(REPO)): sha256_file(p)
                          for p in job_outputs(job)},
            }
            save_state(st)
            rows[-1] = (job["id"], "done",
                        f"{secs / 60:.1f} min"
                        + (f" · rescue x{rescue}" if rescue > 1 else "")
                        + f" · {sha256_file(job_outputs(job)[0])[:10]}")
            ok.append(job["id"])
            mo.output.replace(mo.md(f"### {label}\n\n" + _table(rows)))

        # naive ETA from this config's finished jobs
        done_secs = [e["seconds"] for e in st.get("jobs", {}).values()
                     if e.get("cfg") == cfg_fp() and e.get("seconds")]
        eta = ""
        if done_secs and jobs:
            rate = sum(done_secs) / (len(done_secs) * _cost_unit())
            rem_n = len([j for j in jobs
                         if j["id"] not in ok + skipped])
            if rem_n:
                eta = (f"\n\nApprox. remaining at the measured rate: "
                       f"**{rate * _cost_unit() * rem_n / 3600:.1f} h**.")
        summary = (f"### {label} — finished\n\n" + _table(rows) + "\n\n"
                   f"ok {len(ok)} · skipped {len(skipped)} · failed "
                   f"{len(failed)}{eta}")
        if failed:
            summary += ("\n\n⚠️ failures stop their batch — fix and "
                        "re-run this cell; completed shots are skipped.")
        mo.output.replace(mo.md(summary))
        return {"ok": ok, "skipped": skipped, "failed": failed,
                "stamp": time.strftime("%H:%M:%S")}

    def framecheck_run(job, factors):
        """Try rescue factors until the NDC pre-flight passes."""
        last = ""
        for f in factors:
            log = WORK / "logs" / f"fc_{job['id']}_{f}.log"
            t0 = time.time()
            rc, txt = run_capture(cmd_for(job, framecheck=True),
                                  env=base_env(f), cwd=REPO,
                                  timeout=3600)
            log.write_text(txt)
            good = (rc == 0 and "[frame]" in txt and "CLIPPED" not in txt
                    and "FAIL" not in txt)
            if good:
                n = len([ln for ln in txt.splitlines()
                         if "[frame]" in ln])
                return f, f"{n} cam(s), {time.time() - t0:.0f}s"
            last = txt[-600:]
        raise RuntimeError(f"framecheck never passed for {job['id']} "
                           f"(factors {factors}). Last output:\n{last}")

    def delivery_ui(jobs, zip_name):
        st = load_state()
        files = []
        for job in jobs:
            for p in job_outputs(job):
                if p.exists() and p.stat().st_size > 10_000:
                    files.append((job, p))
        if not files:
            return mo.md("Nothing on disk yet for this set.")
        thumbs = WORK / "thumbs"
        thumbs.mkdir(exist_ok=True)
        gen = WORK / "thumbs_gen.py"
        if not gen.exists():
            gen.write_text(
                "import sys\n"
                "from PIL import Image\n"
                "im = Image.open(sys.argv[1])\n"
                "im.thumbnail((1600, 1600))\n"
                "im.convert('RGB').save(sys.argv[2], 'JPEG', quality=88)\n")
        rows = ["| file | size | sha256 | render |", "|---|---|---|---|"]
        images, buttons, entries = [], [], []
        for job, p in files:
            e = st.get("jobs", {}).get(job["id"], {})
            digest = sha256_file(p)
            size_mb = p.stat().st_size / 1e6
            rescue = e.get("rescue", 1.0)
            rows.append(
                f"| `{p.name}` ({job['id']}) | {size_mb:.1f} MB | "
                f"`{digest[:12]}` | {e.get('seconds', 0) / 60:.0f} min"
                + (f" · rescue x{rescue}" if rescue > 1 else "")
                + " |")
            entries.append((job, p, digest, size_mb))
            t = thumbs / f"{job['id']}_{p.stem}.jpg"
            if not t.exists():
                run_capture([str(VENV_PY), str(gen), str(p), str(t)],
                            timeout=120)
            if t.exists():
                images.append(mo.image(str(t)))

        man = WORK / "MANIFEST_molab.txt"
        lines = [
            "Hojicha44 — molab master renders",
            f"repo:     {CFG['repo_url']}",
            f"git:      {SHA} ({SHA_SUBJECT})",
            f"notebook: {CFG['notebook']}",
            f"renderer: {BLENDER_VER} (linux-x64)",
            f"kicad:    {KICAD_VER}",
            f"gpu:      {ENV['gpu']}",
            f"res:      {CFG['res']}  samples: {CFG['samples']} "
            f"(adaptive {CFG['adaptive_threshold']})  "
            f"device: {CFG['device']}",
            f"rendered: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 72,
        ]
        for job, p, digest, size_mb in entries:
            e = st.get("jobs", {}).get(job["id"], {})
            lines.append(f"{p.relative_to(REPO)}  {size_mb:.1f} MB  "
                         f"{digest}  {e.get('seconds', 0) / 60:.0f} min  "
                         f"rescue x{e.get('rescue', 1)}")
        man.write_text("\n".join(lines) + "\n")

        zp = WORK / zip_name
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED,
                             compresslevel=1) as z:
            z.write(man, "MANIFEST_molab.txt")
            for job, p, _, _ in entries:
                z.write(p, str(p.relative_to(REPO / "generated/renders")))
            for lg in sorted((WORK / "logs").glob("*.log")):
                z.write(lg, f"logs/{lg.name}")

        buttons.append(mo.download(
            data=lambda zp=zp: zp.read_bytes(),
            filename=zip_name, mimetype="application/zip",
            label=f"⬇  ZIP — everything here "
                  f"({zp.stat().st_size / 1e6:.0f} MB)"))
        for job, p, _, _ in entries:
            buttons.append(mo.download(
                data=lambda p=p: p.read_bytes(),
                filename=p.name, mimetype="image/png",
                label=f"⬇  {p.name} ({job['id']})"))

        return mo.vstack([
            mo.md(f"## Delivery — {len(files)} master file(s)\n\n"
                  + "\n".join(rows)
                  + f"\n\n`git {SHA_SHORT}` · full PNGs below, ZIP last "
                    f"(manifest + logs inside)."),
            *images,
            mo.md("---\n### Downloads"),
            *buttons,
        ])

    PRIORITY_JOBS = [j for j in QUEUE if j["id"] in PRIORITY_IDS]
    REST_JOBS = [j for j in QUEUE if j["id"] not in PRIORITY_IDS]
    return (
        PRIORITY_JOBS,
        REST_JOBS,
        base_env,
        cfg_fp,
        cmd_for,
        delivery_ui,
        framecheck_run,
        job_outputs,
        load_state,
        run_batch,
        save_state,
    )


@app.cell
def _(BLENDER, CFG, REPO, SHA, WORK, base_env, load_state, mo, run_stream,
      save_state):
    # ------------------------------------------------------------------
    # smoke test — a tiny E2E render that proves device, materials,
    # textures and the patched scripts before hours are committed
    # ------------------------------------------------------------------
    st = load_state()
    if not CFG["run_smoke"]:
        print("smoke disabled in CFG", flush=True)
        SMOKE = "disabled"
    elif st.get("smoke_sha") == SHA and not CFG["force"]:
        print(f"smoke already passed for {SHA[:7]}", flush=True)
        SMOKE = f"passed @ {SHA[:7]}"
    else:
        import shutil as _sh  # underscored alias, marimo-local
        _sh.rmtree(WORK / "smoke", ignore_errors=True)
        # hero AND exploded: the exploded run covers the stack palette
        # and the PCB gerber artwork generation (pcb_tex.py via the
        # venv python3 — the artwork only regenerates on the
        # stack-colours path, so the hero alone cannot prove it)
        cmd = [str(BLENDER), "--background", "--python",
               "renders/scene.py", "--",
               "--samples", "24", "--res", "800x500",
               "--setups", "bright", "--shots", "hero,exploded",
               "--colourway", "bright", "--stack-colors",
               "--out", str(WORK / "smoke")]
        log = WORK / "logs/smoke.log"
        rc, secs = run_stream(cmd, base_env(1.0), REPO, log)
        outs = [WORK / "smoke/bright/hero.png",
                WORK / "smoke/bright/exploded.png"]
        text = log.read_text(errors="replace") if log.exists() else ""
        if rc != 0 or not all(p.exists() for p in outs) \
                or "artwork generation failed" in text:
            raise RuntimeError(
                "SMOKE RENDER FAILED — nothing below this point will "
                "work until it passes.\n"
                f"log: {log}\n```\n{text[-1500:]}\n```")
        st["smoke_sha"] = SHA
        save_state(st)
        print(f"smoke OK in {secs:.0f}s -> {outs[0].parent}", flush=True)
        SMOKE = f"ok {secs:.0f}s @ {SHA[:7]}"
    mo.md(f"**Smoke:** {SMOKE}")
    return (SMOKE,)


@app.cell
def _(CFG, QUEUE, SHA, ThreadPoolExecutor, cfg_fp, framecheck_run,
      load_state, mo, save_state):
    # ------------------------------------------------------------------
    # framecheck gate — NDC pre-flight for EVERY queued job at the real
    # target resolution, with automatic zoom-out rescue (3 parallel
    # workers). Every failed factor is named in _molab_render/logs/.
    # ------------------------------------------------------------------
    st = load_state()
    fc = st.setdefault("framecheck", {})
    todo = [j for j in QUEUE
            if fc.get(j["id"], {}).get("sha") != SHA
            or fc.get(j["id"], {}).get("fp") != cfg_fp()]
    factors = [1.0] + ([1.05, 1.10, 1.15] if CFG["frame_rescue"] else [])

    if not CFG["run_framecheck"]:
        for j in QUEUE:
            fc.setdefault(j["id"], {"sha": SHA, "fp": cfg_fp(),
                                    "factor": 1.0})
        save_state(st)
        print("framecheck disabled — factors default to x1.0", flush=True)
    elif not todo:
        print("all jobs already framechecked for this SHA", flush=True)
    else:
        print(f"framechecking {len(todo)} job(s), up to "
              f"{len(factors)} factor(s) each, 3 at a time "
              f"(~5-15 min) ...", flush=True)

        def _one(job):
            f, note = framecheck_run(job, factors)
            return job["id"], f, note

        with ThreadPoolExecutor(max_workers=3) as ex:
            for jid, f, note in ex.map(_one, todo):
                fc[jid] = {"sha": SHA, "fp": cfg_fp(), "factor": f}
                save_state(st)
                print(f"  {jid}: PASS at x{f} ({note})", flush=True)

    rows = ["| job | rescue factor | status |", "|---|---|---|"]
    for j in QUEUE:
        e = fc.get(j["id"], {})
        if e.get("sha") == SHA and e.get("fp") == cfg_fp():
            f = e.get("factor", 1.0)
            tag = f"x{f:.2f} (zoomed out)" if f > 1 else "x1.00"
            rows.append(f"| `{j['id']}` | {tag} | PASS |")
        else:
            rows.append(f"| `{j['id']}` | — | not checked |")
    FC_TABLE = "\n".join(rows)
    mo.md("## Framecheck @ " + CFG["res"] + "\n\n" + FC_TABLE)
    return (FC_TABLE,)


@app.cell
def _(CFG, FC_TABLE, PRIORITY_JOBS, SHA, SMOKE, mo, run_batch):
    # ------------------------------------------------------------------
    # RENDER — the three (the ~2-4 h cell)
    # ------------------------------------------------------------------
    assert SMOKE and FC_TABLE, "smoke + framecheck must pass first"
    mo.md(f"### Rendering the three priority shots @ {CFG['res']} / "
          f"{CFG['samples']} samples\n\nplay hero → bright hero → bright "
          f"exploded. Live table below; logs in `_molab_render/logs/`.")
    _summary = run_batch(PRIORITY_JOBS, "Priority renders")
    PRIORITY_STAMP = (f"{SHA[:7]} {_summary['stamp']} "
                      f"ok={len(_summary['ok'])} "
                      f"fail={len(_summary['failed'])}")
    return (PRIORITY_STAMP,)


@app.cell
def _(PRIORITY_JOBS, PRIORITY_STAMP, delivery_ui):
    # ------------------------------------------------------------------
    # DOWNLOAD — the three (auto-runs after the renders; re-run any
    # time — it lists whatever is on disk right now)
    # ------------------------------------------------------------------
    assert PRIORITY_STAMP
    delivery_ui(PRIORITY_JOBS,
                f"hojicha44_priority_{PRIORITY_STAMP.split()[0]}.zip")


@app.cell
def _(mo):
    # ------------------------------------------------------------------
    # GATE — set GO_REST = True and re-run this cell when you are ready
    # for the rest of the programme (download the three first!)
    # ------------------------------------------------------------------
    GO_REST = False
    mo.md(
        f"""
        ## Gate to the rest of the programme

        The three priority shots are on disk when the cell above shows
        their download buttons. Set `GO_REST = True` in **this cell** and
        re-run it: the remaining shots render next, and the final cell
        downloads everything.

        Current gate: **{'OPEN' if GO_REST else 'CLOSED'}**
        """)
    return (GO_REST,)


@app.cell
def _(CFG, FC_TABLE, GO_REST, REST_JOBS, SHA, mo, run_batch):
    # ------------------------------------------------------------------
    # RENDER — the rest (bright/dark top + orbit, play top, artisan,
    # env desk/mat/dev/gaming)
    # ------------------------------------------------------------------
    assert FC_TABLE, "framecheck must pass first"
    if not GO_REST:
        mo.md("Rest gated — set `GO_REST = True` in the gate cell above, "
              "then re-run this cell (or the gate cell).")
        REST_STAMP = "gated"
    else:
        mo.md(f"### Remaining programme @ {CFG['res']} / "
              f"{CFG['samples']} samples\n\nLive table below; logs in "
              f"`_molab_render/logs/`.")
        _summary = run_batch(REST_JOBS, "Remaining programme")
        REST_STAMP = (f"{SHA[:7]} {_summary['stamp']} "
                      f"ok={len(_summary['ok'])} "
                      f"fail={len(_summary['failed'])}")
    return (REST_STAMP,)


@app.cell
def _(QUEUE, REST_STAMP, delivery_ui):
    # ------------------------------------------------------------------
    # DOWNLOAD — everything (auto-refreshes when the rest finishes)
    # ------------------------------------------------------------------
    assert REST_STAMP
    _tag = "partial" if REST_STAMP == "gated" else REST_STAMP.split()[0]
    delivery_ui(QUEUE, f"hojicha44_full_programme_{_tag}.zip")


if __name__ == "__main__":
    app.run()
