#!/usr/bin/env python3
"""
Builds the illustrated Call of the Wild reader.

Text comes from Project Gutenberg #215 (clean, public domain).
Illustrations are cropped by crop_cotw_images.py from the high-resolution
Internet Archive scan `callwild04londgoog` (Goodwin / Bull / Hooper) into
assets/images/cotw/.

Run from the blog root:  python3 generate_cotw.py
"""

import re
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from PIL import Image

HTML_URL = "https://www.gutenberg.org/cache/epub/215/pg215-images.html"
OUT_DIR  = Path("call-of-the-wild")
IMG_BASE = "/assets/images/cotw"
ASSET_DIR = Path("assets/images/cotw")
HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; educational/personal use)"}


def img_attrs(name: str) -> str:
    """Emit width/height from the actual JPEG so the browser locks the aspect
    ratio and reserves layout space (no reflow as images load, no distortion
    when the 100vh height cap kicks in)."""
    path = ASSET_DIR / f"{name}.jpg"
    if not path.exists():
        return ""
    with Image.open(path) as im:
        w, h = im.size
    return f' width="{w}" height="{h}"'

TITLES = [
    "Into the Primitive",
    "The Law of Club and Fang",
    "The Dominant Primordial Beast",
    "Who Has Won to Mastership",
    "The Toil of Trace and Trail",
    "For the Love of a Man",
    "The Sounding of the Call",
]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]

# Decorative Bull/Hooper headpieces exist for chapters I–III only (as in the
# book). Chapters I & II carry their title inside the art (so we suppress the
# visible HTML title); III's title is set beneath the vignette. Chapter I's
# headpiece also contains the verse epigraph, so it replaces the HTML poem too.
HEADPIECE = {1: "head-01", 2: "head-02", 3: "head-03"}
TITLE_IN_ART = {1, 2}
EPIGRAPH_IN_ART = {1}

# ── full-page plates & in-text cuts ──────────────────────────────────────────
# (image, chapter, anchor phrase [lowercased], caption, alt)
# Each image is placed at the first paragraph in its chapter that contains the
# anchor — i.e. right where the text names the scene it depicts. The caption
# (None for the uncaptioned cuts) is reproduced beneath the image.
PLATES = [
    ("plate-demesne",    1, "over this great demesne", "“Over this great demesne.”",
        "A sunlit valley of orchards and vine-clad hills"),
    ("plate-perrault",   1, "perrault", "Perrault.",
        "Perrault, the French-Canadian courier, in furs"),
    ("plate-glaciers",   2, "glaciers and snowdrifts", "“Glaciers and snowdrifts.”",
        "A pass between glaciers and snowdrifts"),
    ("plate-francois",   2, "françois", "François.",
        "François on snowshoes, holding the traces"),
    ("plate-wildwaters", 3, "defied the frost", "“Wild waters defied the frost.”",
        "Wild waters breaking against ice and cliff"),
    ("plate-aurora",     3, "aurora borealis",
        "“With the aurora borealis flaming coldly overhead.”",
        "Sled dogs on the snow beneath the aurora borealis"),
    ("plate-death",      3, "it was to the death", "“It was to the death.”",
        "Buck and Spitz fighting, ringed by the waiting pack"),
    ("plate-snowed",     4, "it snowed every day", "“It snowed every day.”",
        "A grey snowfall over the trail"),
    ("plate-running",    5, "trickle of running water", "“Running water.”",
        "A thread of running water down a snowbound gorge"),
    ("plate-hal",        5, "charles and hal", "Hal.",
        "Hal, muffled in furs, a revolver at his belt"),
    ("cut-sled",         5, "unending family quarrel", None,
        "Hal's overloaded sled and dog-team on the trail"),
    ("plate-thornton",   5, "looked at each other",
        "“John Thornton and Buck looked at each other.”",
        "John Thornton crouched over Buck by the tent"),
    ("plate-riverbank",  6, "river bank", "“By the river bank.”",
        "A snow-capped mountain above the river bank"),
    ("plate-shades",     6, "shades of all manner of dogs",
        "“Behind him were the shades of all manner of dogs.”",
        "A ghostly pack of dogs and wolves gathered in the gloom"),
    ("plate-fullmoon",   7, "moon rose", "“A full moon rose.”",
        "A full moon rising over the dark northern hills"),
    ("cut-wolves",       7, "whirl around at bay", None,
        "A timber wolf and Buck loping side by side"),
    ("plate-moose",      7, "moose stood still", "“Lying down when the moose stood still.”",
        "A great bull moose at bay in the forest, Buck below"),
    ("plate-wolf",       7, "gloriously coated wolf",
        "“In the summers there is one visitor … to that valley, "
        "… a great, gloriously coated wolf.”",
        "A great wolf in a shadowed forest glade"),
]


# ── text extraction ──────────────────────────────────────────────────────────
def fetch_html() -> str:
    cache = Path(".cotw-scan-cache") / "pg215.html"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    req = urllib.request.Request(HTML_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8")
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(html, encoding="utf-8")
    return html


def clean_inner(p: Tag) -> str:
    """Serialize a <p>'s inner HTML, keeping only <i> and <br>."""
    html = p.decode_contents()
    html = re.sub(r"</?(em)>", lambda m: m.group(0).replace("em", "i"), html)
    html = re.sub(r"<(?!/?(i|br)\b)[^>]*>", "", html)
    return " ".join(html.split())


def parse_chapters(html: str):
    soup = BeautifulSoup(html, "html.parser")
    heads = [h for h in soup.find_all("h2")
             if h.get_text(strip=True).startswith("Chapter")]
    chapters = []
    for h in heads:
        epigraph, paras = None, []
        for sib in h.next_siblings:
            if isinstance(sib, Tag):
                if sib.name == "h2":
                    break
                if sib.name == "p":
                    if "poem" in (sib.get("class") or []):
                        epigraph = clean_inner(sib)
                    else:
                        paras.append(clean_inner(sib))
        chapters.append({"epigraph": epigraph, "paras": paras})
    return chapters


# ── plate placement ──────────────────────────────────────────────────────────
def plate_html(img: str, caption, alt: str) -> str:
    cls = "cut" if img.startswith("cut-") else "plate"
    out = f'<figure class="{cls}">\n  <img src="{IMG_BASE}/{img}.jpg" alt="{alt}"{img_attrs(img)}>\n'
    if caption:
        out += f'  <figcaption>{caption}</figcaption>\n'
    out += '</figure>'
    return out


def place_plates(chapters):
    """Place each image at the first paragraph (in its chapter) that names its
    scene — i.e. where the text calls for it. Images sharing a paragraph stack in
    list order (which is the book's plate order)."""
    inserts = {ci: {} for ci in range(len(chapters))}
    for img, chapter, anchor, caption, alt in PLATES:
        ci = chapter - 1
        paras = chapters[ci]["paras"]
        target = None
        for pi, para in enumerate(paras):
            if anchor in re.sub(r"<[^>]+>", "", para).lower():
                target = pi
                break
        if target is None:
            print(f"  WARN: no anchor match for {img} ('{anchor}') in chapter {chapter}")
            continue
        inserts[ci].setdefault(target, []).append(plate_html(img, caption, alt))
    return inserts


# ── page rendering ───────────────────────────────────────────────────────────
def chapter_header(num: int) -> str:
    idx = num - 1
    title = TITLES[idx]
    parts = ['<header class="chapter-header">',
             '  <a class="book-title-link" href="/call-of-the-wild/">The Call of the Wild</a>']
    if num in HEADPIECE:
        alt = f"Chapter {ROMAN[idx]} — {title}"
        cls = "chapter-headpiece chapter-headpiece-full" if num in EPIGRAPH_IN_ART \
            else "chapter-headpiece"
        # only the headpiece rides a full-bleed white band; the title sits below
        # it on the page background
        parts.append('  <div class="chapter-plate">')
        parts.append(f'    <img class="{cls}" src="{IMG_BASE}/{HEADPIECE[num]}.jpg" alt="{alt}"{img_attrs(HEADPIECE[num])}>')
        parts.append('  </div>')
    if num in TITLE_IN_ART:
        # title is engraved into the headpiece art; keep an sr-only heading only
        parts.append(f'  <h1 class="sr-only">{ROMAN[idx]}. {title}</h1>')
    else:
        parts.append(f'  <span class="chapter-num">{ROMAN[idx]}</span>')
        parts.append(f'  <h1>{title}</h1>')
    if num not in HEADPIECE:
        parts.append('  <span class="chapter-ornament">❧</span>')
    parts.append('</header>')
    return "\n".join(parts)


def chapter_body(num: int, ch) -> str:
    parts = []
    if ch["epigraph"] and num not in EPIGRAPH_IN_ART:
        parts.append(f'<p class="chapter-epigraph">{ch["epigraph"]}</p>')
    first_done = False
    for pi, para in enumerate(ch["paras"]):
        cls = "" if first_done else ' class="first-para"'
        parts.append(f"<p{cls}>{para}</p>")
        first_done = True
        for plate in ch["inserts"].get(pi, []):
            parts.append(plate)
    return "\n".join(parts)


TOTAL = 7


def chapter_nav(num: int, direction: str) -> str:
    """Stacked prev/next label: a small dir kicker over the chapter title."""
    idx = num - 1
    roman, title = ROMAN[idx], TITLES[idx]
    if direction == "prev":
        dir_label = f'<span class="nav-arrow">‹</span> {roman}'
    else:
        dir_label = f'{roman} <span class="nav-arrow">›</span>'
    return (f'<a href="/call-of-the-wild/chapter-{num:02d}.html">'
            f'<span class="nav-dir">{dir_label}</span>'
            f'<span class="nav-title">{title}</span></a>')


CONTENTS = '<a class="nav-contents" href="/call-of-the-wild/">↑ Contents</a>'


def render_chapter(num: int, ch) -> str:
    idx = num - 1
    # header nav shows Contents at the ends; the footer keeps its own centre
    # Contents, so its edge slots go empty to avoid doubling it up at the bottom
    edge = '<span class="nav-edge"></span>'
    nav_prev = chapter_nav(num - 1, "prev") if num > 1 else CONTENTS
    nav_next = chapter_nav(num + 1, "next") if num < TOTAL else CONTENTS
    foot_prev = chapter_nav(num - 1, "prev") if num > 1 else edge
    foot_next = chapter_nav(num + 1, "next") if num < TOTAL else edge

    body = chapter_body(num, ch)
    if num == TOTAL:  # closing tailpiece — rides the same full-bleed white band
        body += (f'\n<figure class="cut finis">\n'
                 f'  <img src="{IMG_BASE}/finis.jpg" alt="Finis"{img_attrs("finis")}>\n'
                 f'</figure>')

    header = chapter_header(num)

    return f"""---
layout: reader
book: cotw
title: "{ROMAN[idx]}. {TITLES[idx]} — The Call of the Wild"
---
<nav class="reader-nav">
  {nav_prev}
  <span class="reader-controls"></span>
  {nav_next}
</nav>

{header}

<div class="chapter-body">
{body}
</div>

<footer class="reader-footer">
  {foot_prev}
  <span class="footer-home">{CONTENTS}</span>
  {foot_next}
</footer>
"""


def render_toc() -> str:
    items = "\n".join(
        f'      <li><a href="/call-of-the-wild/chapter-{i+1:02d}.html">'
        f'{ROMAN[i]}. {TITLES[i]}</a></li>'
        for i in range(TOTAL)
    )
    return f"""---
layout: reader
book: cotw
title: "The Call of the Wild — Jack London"
---
<div class="toc-topbar">
  <a class="site-back" href="/">← raymonddouglas.com</a>
  <div class="toc-controls"></div>
</div>

<header class="toc-header">
  <h1>The Call of the Wild</h1>
  <p class="author">Jack London</p>
  <span class="toc-ornament">❧</span>
</header>

<a class="toc-cover-link" href="/call-of-the-wild/chapter-01.html">
  <img class="toc-cover" src="{IMG_BASE}/cover.jpg" alt="The Call of the Wild — title page, illustrated by Philip R. Goodwin and Charles Livingston Bull"{img_attrs("cover")}>
</a>
<a class="begin-reading" href="/call-of-the-wild/chapter-01.html">Begin reading →</a>

<figure class="toc-frontispiece">
  <img src="{IMG_BASE}/frontispiece.jpg" alt="A man crouched by a campfire in the dark, wild eyes gleaming beyond"{img_attrs("frontispiece")}>
  <figcaption>“And beyond that fire … Buck could see many gleaming coals,<br>two by two, always two by two.”</figcaption>
</figure>

<div class="toc-volumes">
  <section class="toc-volume">
    <ul class="toc-list toc-list-titled">
{items}
    </ul>
  </section>
</div>

<p class="toc-note">Text from <a href="https://www.gutenberg.org/ebooks/215">Project Gutenberg #215</a>.
Illustrations by Philip R. Goodwin &amp; Charles Livingston Bull, decorated by Chas. Edw. Hooper,<br>
from the <a href="https://archive.org/details/callwild04londgoog">1903 edition scanned by the Internet Archive</a> — public domain.</p>
"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    chapters = parse_chapters(fetch_html())
    assert len(chapters) == TOTAL, f"expected 7 chapters, got {len(chapters)}"

    inserts = place_plates(chapters)
    for ci, ch in enumerate(chapters):
        ch["inserts"] = inserts[ci]

    (OUT_DIR / "index.html").write_text(render_toc(), encoding="utf-8")
    print("  wrote index.html")
    for num in range(1, TOTAL + 1):
        page = render_chapter(num, chapters[num - 1])
        (OUT_DIR / f"chapter-{num:02d}.html").write_text(page, encoding="utf-8")
        print(f"  wrote chapter-{num:02d}.html")
    print("Done.")


if __name__ == "__main__":
    main()
