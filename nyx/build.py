"""Rebuild the Nyx themes into ../themes/.

    python -I nyx/build.py

Each theme is the stock Nyx theme (base/nyx.json) with motion CSS appended.
Nyx · Aurora Ocean comes in three tiers that trade smoothness and detail for
GPU time (numbers are Task Manager GPU for T3 Code on a 3440x1440 window with
an Intel iGPU):
- nyx-aurora-ocean-full (Full): every effect (full.css adds the flares, the
  glow's hue drift and screen blend, and the over-bright sky breathe; the
  drift and the breathe are baked into images by gen_full.py, whose glow
  replaces glow.css), the sky unstepped, the ocean at full resolution and
  24 fps
- nyx-aurora-ocean (Balanced): no flares or hue drift, the sky stepped at
  10 fps, the ocean at half resolution and 20 fps
- nyx-aurora-ocean-speed (Speed): as Balanced, with the sky at 8 fps and the
  ocean at 16 fps
plus nyx-aurora-ocean-still-sky (Balanced with the sky frozen, still-sky.css).
All of them: the aurora glow (image baked into glow.css by tools/bake_glow.mjs),
stars, the teal stream (teal-stream.css, tools/bake_teal.mjs) and the
generated particle ocean (gen_ocean.py).

The file names are the theme ids T3 uses, so they match already-installed copies.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES = os.path.join(HERE, "..", "themes")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def run(*args, env=None):
    subprocess.run([sys.executable, "-I", *args], check=True, cwd=HERE, env={**os.environ, **(env or {})})


# Aurora Ocean tiers. ocean_fps: steps a second inside the ocean SVG (a
# multiple of 4, so its eight wave columns share one step grid). raster: the
# resolution the ocean is redrawn at on each step. sky_fps: steps a second for
# the sky layers (step_motion.py), or None to leave them smooth. Each sky step
# composites the whole window again, and the sky moves slowly, so it can step
# at a lower rate than the ocean without showing it.
TIERS = {
    "full": dict(ocean_fps=24, raster=1, sky_fps=None),
    "balanced": dict(ocean_fps=20, raster=0.5, sky_fps=10),
    "speed": dict(ocean_fps=16, raster=0.5, sky_fps=8),
}


def ocean(tier):
    t = TIERS[tier]
    path = os.path.join(OUT, f"variant-ocean-{tier}.css")
    run("gen_ocean.py", path, env={"NYX_FPS": str(t["ocean_fps"]), "NYX_RASTER": str(t["raster"])})
    return path


def sky(tier):
    fps = TIERS[tier]["sky_fps"]
    return [f"--step-fps={fps}"] if fps else []


AURORA = ["nyx-aurora-ocean.css", "glow.css", "teal-stream.css"]
oceans = {tier: ocean(tier) for tier in TIERS}
full_baked = os.path.join(OUT, "full-baked.css")
run("gen_full.py", full_baked)
for theme_id, name, flags, css in [
    ("nyx-aurora-ocean-full", "Nyx · Aurora Ocean (Full)", sky("full"),
     ["nyx-aurora-ocean.css", full_baked, "teal-stream.css", oceans["full"], "full.css"]),
    ("nyx-aurora-ocean", "Nyx · Aurora Ocean (Balanced)", sky("balanced"), [*AURORA, oceans["balanced"]]),
    ("nyx-aurora-ocean-speed", "Nyx · Aurora Ocean (Speed)", sky("speed"), [*AURORA, oceans["speed"]]),
    ("nyx-aurora-ocean-still-sky", "Nyx · Aurora Ocean (still sky)", sky("balanced"),
     [*AURORA, oceans["balanced"], "still-sky.css"]),
]:
    run("build_nyx_animated.py", *flags, os.path.join("base", "nyx.json"), os.path.join(THEMES, f"{theme_id}.json"), name, *css)
