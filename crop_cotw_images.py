#!/usr/bin/env python3
"""
Extracts the Call of the Wild illustrations (Goodwin / Bull / Hooper, public
domain) from the high-resolution Internet Archive scan `callwild04londgoog`
and crops them for the web reader.

  Source: archive.org/details/callwild04londgoog  (3037 x 4469 colour pages)

Every picture is a full page in the scan (frame, printed caption, margins), so
each crop box below is a fraction (left, top, right, bottom) of its page. An
optional 5th value rotates a plate the book printed sideways. Captions are kept
IN the crop (they are part of the plate); the reader also reproduces them as
text beneath each image.

Pages are read from a local cache under .cotw-scan-cache/ (git-ignored). If a
page is missing the script converts it from the JP2 zip with `sips` (macOS),
downloading the zip first if necessary.

    python3 crop_cotw_images.py            # write all crops
    python3 crop_cotw_images.py --review   # + build a labelled review grid

Run from the blog root.
"""

import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ZIP_URL = "https://archive.org/download/callwild04londgoog/callwild04londgoog_jp2.zip"
CACHE = Path(".cotw-scan-cache")
ZIP_PATH = CACHE / "callwild_jp2.zip"
JP2_DIR = CACHE / "callwild04londgoog_jp2"
PAGES = CACHE / "pages"
OUT = Path("assets/images/cotw")
MAX_W = 1400  # cap output width for the web (retina-friendly)

# name: (scan_page, (left, top, right, bottom)[, rotate_degrees])
# scan_page is the JP2 index (zero-padded 4 digits). Tweak the fractions to
# re-crop; re-run with --review to eyeball the result.
BOXES = {
    # ── front matter ────────────────────────────────────────────────────────
    "frontispiece": (8,  (0.19, 0.12, 0.86, 0.9)),   # "…two by two"
    "cover":        (9,  (0.11, 0.10, 0.79, 0.85)),   # illustrated title page

    # ── decorative chapter headpieces (Bull/Hooper) — chapters I–III only ─────
    # I carries the title AND verse epigraph in the art (it replaces the HTML
    # head + poem); II carries the title inside the art; III's title is set below.
    "head-01": (17, (0.150, 0.200, 0.805, 0.620)),
    "head-02": (43, (0.150, 0.170, 0.800, 0.392)),
    "head-03": (67, (0.160, 0.09, 0.840, 0.370)),

    # ── in-text vignettes (part-page cuts, no printed caption) ───────────────
    "cut-sled":   (142, (0.20, 0.380, 0.89, 0.55)),  # Hal's overloaded sled
    "cut-wolves": (203, (0.100, 0.340, 0.780, 0.59)),  # Buck and the timber wolf

    # ── bordered duotone landscapes (engraved caption banner inside frame) ───
    "plate-demesne":    (16,  (0.20, 0.100, 0.870, 0.89)),
    "plate-glaciers":   (42,  (0.210, 0.08, 0.880, 0.88)),
    "plate-wildwaters": (66,  (0.200, 0.09, 0.870, 0.89)),
    "plate-snowed":     (102, (0.220, 0.100, 0.90, 0.89)),
    "plate-running":    (122, (0.200, 0.100, 0.860, 0.89)),
    "plate-riverbank":  (160, (0.200, 0.090, 0.870, 0.87)),
    "plate-fullmoon":   (192, (0.220, 0.080, 0.90, 0.88)),

    # ── borderless halftones (printed caption below) ─────────────────────────
    "plate-aurora":   (85,  (0.150, 0.140, 0.83, 0.85)),
    "plate-death":    (95,  (0.120, 0.130, 0.8, 0.86)),
    "plate-thornton": (155, (0.150, 0.120, 0.82, 0.84)),
    "plate-moose":    (215, (0.10, 0.1, 0.79, 0.90)),
    "plate-wolf":     (229, (0.190, 0.100, 0.790, 0.910)),

    # ── portrait figures ─────────────────────────────────────────────────────
    "plate-perrault": (35,  (0.280, 0.150, 0.620, 0.810)),
    "plate-francois": (53,  (0.20, 0.150, 0.850, 0.850)),
    "plate-hal":      (127, (0.18, 0.24, 0.8, 0.760)),

    # ── printed sideways (rotate to upright) ─────────────────────────────────
    "plate-shades":   (169, (0.10, 0.210, 0.8, 0.79), -90),  # image only; caption in HTML

    # ── tailpiece ────────────────────────────────────────────────────────────
    "finis": (231, (0.250, 0.330, 0.67, 0.86)),
}


def ensure_zip() -> None:
    if ZIP_PATH.exists():
        return
    CACHE.mkdir(exist_ok=True)
    print("  downloading JP2 zip (~160 MB) …")
    urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)


def ensure_jp2(n: int) -> Path:
    jp2 = JP2_DIR / f"callwild04londgoog_{n:04d}.jp2"
    if jp2.exists():
        return jp2
    ensure_zip()
    print(f"  extracting {jp2.name} …")
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extract(f"callwild04londgoog_jp2/{jp2.name}", CACHE)
    return jp2


def page(n: int) -> Path:
    """Return a JPEG of scan page n, converting from JP2 with sips if needed."""
    PAGES.mkdir(parents=True, exist_ok=True)
    p = PAGES / f"p{n:04d}.jpg"
    if not p.exists():
        jp2 = ensure_jp2(n)
        print(f"  converting {p.name} …")
        subprocess.run(["sips", "-s", "format", "jpeg", str(jp2), "--out", str(p)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p


def crop_one(name: str, spec) -> Path:
    n, (l, t, r, b) = spec[0], spec[1]
    rot = spec[2] if len(spec) > 2 else 0
    im = Image.open(page(n)).convert("RGB")
    W, H = im.size
    crop = im.crop((int(l * W), int(t * H), int(r * W), int(b * H)))
    if rot:
        crop = crop.rotate(rot, expand=True)
    if crop.width > MAX_W:
        crop.thumbnail((MAX_W, MAX_W * 4))
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.jpg"
    crop.save(out, quality=88)
    return out


def build_review():
    """Tile every crop with its name + box numbers for eyeballing."""
    cols = 5
    tw = 360
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
    except Exception:
        font = ImageFont.load_default()
    items = list(BOXES.items())
    th = 460
    lb = 46
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + lb)), "white")
    d = ImageDraw.Draw(sheet)
    for i, (name, spec) in enumerate(items):
        r, c = divmod(i, cols)
        im = Image.open(OUT / f"{name}.jpg").convert("RGB")
        im.thumbnail((tw - 8, th - 8))
        x, y = c * tw, r * (th + lb)
        box = ", ".join(f"{v:.3f}" for v in spec[1])
        rot = f"  rot={spec[2]}" if len(spec) > 2 else ""
        d.text((x + 4, y + 2), f"{name}  (pg {spec[0]}){rot}", fill="red", font=font)
        d.text((x + 4, y + 22), box, fill="blue", font=font)
        # center the thumbnail in its cell
        sheet.paste(im, (x + (tw - im.width) // 2, y + lb))
    out = CACHE / "crop_review.jpg"
    sheet.save(out, quality=84)
    print(f"  wrote {out}")


def build_grid(only=None):
    """For each image, draw the FULL source page with a fractional grid and the
    current crop box on top — so boxes can be read straight off the page. One
    file per image under .cotw-scan-cache/grid/. Pass `only` to limit the set."""
    gdir = CACHE / "grid"
    gdir.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    GW = 900  # rendered page width
    for name, spec in BOXES.items():
        if only and name not in only:
            continue
        n, box = spec[0], spec[1]
        im = Image.open(page(n)).convert("RGB")
        im = im.resize((GW, int(GW * im.height / im.width)))
        w, h = im.size
        d = ImageDraw.Draw(im, "RGBA")
        # finest 0.01 grid; medium 0.05; bold labelled 0.1 drawn last on top
        for i in range(1, 100):
            if i % 10 == 0:
                continue  # 0.1 lines drawn below
            f = i / 100
            x, y = int(f * w), int(f * h)
            if i % 5 == 0:  # 0.05 medium
                fill, wd = (70, 70, 90, 90), 1
            else:           # 0.01 faint
                fill, wd = (90, 90, 110, 32), 1
            d.line([(x, 0), (x, h)], fill=fill, width=wd)
            d.line([(0, y), (w, y)], fill=fill, width=wd)
        # bold, labelled 0.1 lines
        for i in range(11):
            f = i / 10
            x, y = int(f * w), int(f * h)
            d.line([(x, 0), (x, h)], fill=(215, 45, 45, 165), width=2)
            d.line([(0, y), (w, y)], fill=(215, 45, 45, 165), width=2)
            d.text((x + 3, 2), f"{f:.1f}", fill=(200, 0, 0), font=font)
            d.text((3, y + 2), f"{f:.1f}", fill=(200, 0, 0), font=font)
        l, t, r, b = box
        d.rectangle([l * w, t * h, r * w, b * h], outline=(0, 110, 255), width=4)
        rot = f"  rot={spec[2]}" if len(spec) > 2 else ""
        cap = ", ".join(f"{v:.3f}" for v in box)
        d.rectangle([0, h - 30, w, h], fill=(255, 255, 255, 220))
        d.text((6, h - 28), f"{name} (pg {n}){rot}   box=({cap})", fill=(0, 0, 160), font=font)
        im.save(gdir / f"{name}.jpg", quality=86)
    print(f"  wrote grid overlays to {gdir}/")


def main():
    for name, spec in BOXES.items():
        crop_one(name, spec)
        print(f"  wrote {name}.jpg")
    if "--review" in sys.argv:
        build_review()
    if "--grid" in sys.argv:
        names = [a for a in sys.argv[1:] if not a.startswith("--")]
        build_grid(set(names) or None)
    print("Done.")


if __name__ == "__main__":
    main()
