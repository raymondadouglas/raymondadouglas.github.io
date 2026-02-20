#!/usr/bin/env python3
"""
Fetches Pride & Prejudice from Project Gutenberg, splits it into chapters,
downloads illustrations, and generates Jekyll HTML pages.

Run from the blog root:  python3 generate_pandp.py
"""

import re
import time
import urllib.request
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# ── config ──────────────────────────────────────────────────────────────────
HTML_URL   = "https://www.gutenberg.org/cache/epub/1342/pg1342-images.html"
IMG_BASE   = "https://www.gutenberg.org/cache/epub/1342/"
OUT_DIR    = Path("pride-and-prejudice")
IMG_DIR    = Path("assets/images/pandp")
TOTAL      = 61   # chapters in P&P
# ────────────────────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; educational/personal use)"}


def fetch_html(url: str) -> str:
    print(f"Fetching {url} …")
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def download_image(src: str, dest: Path) -> None:
    """Download one image if it doesn't exist yet."""
    if dest.exists():
        return
    abs_url = src if src.startswith("http") else IMG_BASE + src
    try:
        req = urllib.request.Request(abs_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            dest.write_bytes(resp.read())
        print(f"  downloaded {dest.name}")
        time.sleep(0.15)   # be polite
    except Exception as e:
        print(f"  WARN: could not download {abs_url}: {e}")


def local_img_path(src: str) -> str:
    """Return the site-relative path for an image."""
    filename = src.split("/")[-1].split("?")[0]
    return f"/assets/images/pandp/{filename}"


# ── junk filters ──────────────────────────────────────────────────────────────
_DROP_CLASSES = {"pagenum", "letra", "x-ebookmaker-drop"}
_CAPTION_RE   = re.compile(r"^\[.*copyright.*\]$", re.I)
_PAGENUM_RE   = re.compile(r"^\{[ivxlcdm\d]+\}$", re.I)
_INLINE_PN    = re.compile(r"\{[ivxlcdm\d]+\}", re.I)   # strip inline page-nums


def _is_junk_text(text: str) -> bool:
    t = text.strip()
    return bool(_CAPTION_RE.match(t) or _PAGENUM_RE.match(t))


def _has_drop_class(node) -> bool:
    return bool(_DROP_CLASSES & set(node.get("class", [])))


def _node_inner_text(node) -> str:
    """Recursively build inner HTML of a paragraph node."""
    result = ""
    for child in node.children:
        if isinstance(child, NavigableString):
            result += str(child)

        elif child.name in ("span", "a") and _has_drop_class(child):
            classes = child.get("class", [])
            if "pagenum" not in classes:
                # Could be text letra OR image letra (e.g. <img alt="M">)
                img_in_span = child.find("img") if hasattr(child, "find") else None
                if img_in_span:
                    result += img_in_span.get("alt", "")
                else:
                    result += child.get_text()
            # pagenum spans: silently drop

        elif child.name == "img":
            # images inside paragraphs — use placeholder, resolved below
            result += f'__IMG__{child.get("src","")}__ALT__{child.get("alt","").strip()}__'

        elif child.name in ("i", "em", "b", "strong", "br"):
            result += str(child)

        elif child.name in ("span", "a"):
            result += _node_inner_text(child)

        else:
            result += _node_inner_text(child)

    return result


def _emit_img(src: str, alt: str, parts: list) -> None:
    """Emit an <img> and optional caption into parts."""
    local = local_img_path(src)
    parts.append(f'<img src="{local}" alt="{alt}">')
    if alt:
        parts.append(f'<p class="caption">{alt}</p>')


def extract_h2_illustration(h2_tag) -> str:
    """
    Each chapter h2 contains the opening full-page illustration for that chapter.
    Pull it out and return clean HTML to prepend to the chapter body.
    """
    img = h2_tag.find("img")
    if not img:
        return ""
    src = img.get("src", "")
    if not src:
        return ""
    caption_span = h2_tag.find("span", class_="caption")
    caption = caption_span.get_text(strip=True) if caption_span else ""
    # strip inline page numbers from caption
    caption = _INLINE_PN.sub("", caption).strip()
    local = local_img_path(src)
    html = f'<img src="{local}" alt="{caption}" class="chapter-opener">'
    if caption:
        html += f'\n<p class="caption">{caption}</p>'
    return html


def clean_chapter_html(nodes) -> str:
    """
    Given a list of BS4 nodes (between two h2 headings),
    return cleaned HTML suitable for embedding in a Jekyll page.
    """
    parts: list[str] = []
    prev_was_img   = False
    first_para_emitted = False   # track first real text paragraph for drop cap

    for node in nodes:
        if isinstance(node, NavigableString):
            continue

        tag = node.name
        if tag is None:
            continue

        # ── skip junk elements ───────────────────────────────────────────────
        if _has_drop_class(node):
            continue
        if tag in ("style", "script", "link", "meta", "noscript"):
            continue

        # ── standalone images (not inside p) ────────────────────────────────
        if tag == "img":
            _emit_img(node.get("src",""), node.get("alt","").strip(), parts)
            prev_was_img = True
            continue

        # ── paragraphs ──────────────────────────────────────────────────────
        if tag == "p":
            inner = _node_inner_text(node)

            # resolve any __IMG__ placeholders (img tags that were inside <p>)
            img_m = re.search(r"__IMG__(.*?)__ALT__(.*?)__", inner)
            if img_m:
                before = _INLINE_PN.sub("", inner[:img_m.start()]).strip()
                if before and not _is_junk_text(before):
                    parts.append(f"<p>{before}</p>")
                _emit_img(img_m.group(1), img_m.group(2), parts)
                after = _INLINE_PN.sub("", inner[img_m.end():]).strip()
                if after and not _is_junk_text(after):
                    parts.append(f"<p>{after}</p>")
                prev_was_img = True
                continue

            # strip inline page numbers and any residual letra spans
            inner = _INLINE_PN.sub("", inner)
            inner = re.sub(r'<span[^>]*class="letra"[^>]*>(.*?)</span>', r"\1", inner)

            text = inner.strip()
            if not text or _is_junk_text(text):
                continue

            # copyright lines after images
            if prev_was_img and text.startswith("["):
                prev_was_img = False
                continue

            # caption paragraphs: follow a standalone <img>, marked with <br/>
            # (figcenter captions are already handled above; this is the fallback)
            if prev_was_img and text.endswith("<br/>"):
                caption = text.removesuffix("<br/>").strip()
                caption = _INLINE_PN.sub("", caption).strip()
                if not _is_junk_text(caption):
                    parts.append(f'<p class="caption">{caption}</p>')
                prev_was_img = False
                continue

            if not first_para_emitted:
                parts.append(f'<p class="first-para">{text}</p>')
                first_para_emitted = True
            else:
                parts.append(f"<p>{text}</p>")
            prev_was_img = False
            continue

        # ── figcenter divs — handle image + caption as a unit ────────────────
        if tag in ("div", "section", "figure"):
            classes = node.get("class", [])
            if "figcenter" in classes:
                img_tag = node.find("img")
                cap_div = node.find("div", class_="caption")
                if img_tag:
                    _emit_img(img_tag.get("src",""), img_tag.get("alt","").strip(), parts)
                if cap_div:
                    for p in cap_div.find_all("p"):
                        raw = _INLINE_PN.sub("", p.get_text(" ", strip=True)).strip()
                        if raw and not _is_junk_text(raw) and not _CAPTION_RE.match(raw):
                            # replace the empty-alt caption placeholder if present
                            if parts and parts[-1].startswith('<p class="caption">') \
                                    and img_tag and not img_tag.get("alt","").strip():
                                parts.pop()
                            parts.append(f'<p class="caption">{raw}</p>')
                            break
                # caption already handled — don't let next paragraph get swallowed
                prev_was_img = False
                continue

            # generic div/section — recurse
            inner_html = clean_chapter_html(list(node.children))
            if inner_html.strip():
                parts.append(inner_html)
            prev_was_img = False
            continue

        # ── inline / block markup — keep as-is ──────────────────────────────
        if tag in ("em", "i", "b", "strong", "br", "hr", "blockquote"):
            parts.append(str(node))
            prev_was_img = False
            continue

    return "\n".join(parts)


def int_to_roman(n: int) -> str:
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
            (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for v, s in vals:
        while n >= v:
            result += s
            n -= v
    return result


def roman_to_int(s: str) -> int:
    vals = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    s = s.upper().strip().rstrip(".")
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        total += v if v >= prev else -v
        prev = v
    return total


def chapter_label(heading_text: str) -> tuple[int, str]:
    """Return (chapter_number, display_label)."""
    m = re.search(r"chapter\s*([IVXLCDM]+\.?)", heading_text.strip(), re.I)
    if m:
        roman = m.group(1).rstrip(".")
        num   = roman_to_int(roman)
        return num, f"Chapter {roman}"
    return 0, heading_text.strip()


def generate_chapter_page(num: int, label: str, html_body: str) -> str:
    toc_link = '<a href="/pride-and-prejudice/">↑ Contents</a>'

    if num > 1:
        prev_link = (
            f'<a href="/pride-and-prejudice/chapter-{num-1:02d}.html">'
            f'<span class="nav-arrow">←</span> Chapter {int_to_roman(num-1)}</a>'
        )
    else:
        prev_link = toc_link

    if num < TOTAL:
        next_link = (
            f'<a href="/pride-and-prejudice/chapter-{num+1:02d}.html">'
            f'Chapter {int_to_roman(num+1)} <span class="nav-arrow">→</span></a>'
        )
    else:
        next_link = toc_link

    footer_prev = prev_link if num > 1 else '<span></span>'
    footer_next = next_link if num < TOTAL else '<span></span>'

    return f"""---
layout: reader
title: "{label} — Pride and Prejudice"
---
<nav class="reader-nav">
  {prev_link}
  <span class="reader-controls"></span>
  {next_link}
</nav>

<header class="chapter-header">
  <a class="book-title-link" href="/pride-and-prejudice/">Pride and Prejudice</a>
  <h1>{label}</h1>
  <span class="chapter-ornament">❧</span>
</header>

<div class="chapter-body">
{html_body}
</div>

<footer class="reader-footer">
  {footer_prev}
  <span class="footer-home"><a href="/pride-and-prejudice/">↑ Contents</a></span>
  {footer_next}
</footer>
"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    raw = fetch_html(HTML_URL)
    soup = BeautifulSoup(raw, "html.parser")

    # ── download all images ───────────────────────────────────────────────
    all_imgs = soup.find_all("img")
    print(f"Found {len(all_imgs)} images — downloading …")
    for img in all_imgs:
        src = img.get("src", "")
        if src:
            dest = IMG_DIR / src.split("/")[-1].split("?")[0]
            download_image(src, dest)

    # ── split by h2 chapter headings ─────────────────────────────────────
    body = soup.find("body") or soup

    chapters: list[tuple[int, str, str, list]] = []  # (num, label, h2_illus, nodes)
    current_num    = 0
    current_label  = ""
    current_illus  = ""
    current_nodes: list = []

    for node in body.children:
        if isinstance(node, Tag) and node.name == "h2":
            heading_text = node.get_text(" ", strip=True)
            num, label   = chapter_label(heading_text)
            if num > 0:
                # save previous chapter
                if current_num > 0 and current_nodes:
                    chapters.append((current_num, current_label, current_illus, current_nodes))
                current_num   = num
                current_label = label
                # extract the opening illustration embedded in the h2
                current_illus = extract_h2_illustration(node)
                current_nodes = []
        elif current_num > 0:
            current_nodes.append(node)

    # last chapter
    if current_num > 0 and current_nodes:
        chapters.append((current_num, current_label, current_illus, current_nodes))

    print(f"\nFound {len(chapters)} chapters — generating pages …")

    for num, label, h2_illus, nodes in chapters:
        body_parts = []
        if h2_illus:
            body_parts.append(h2_illus)
        body_parts.append(clean_chapter_html(nodes))
        html_body = "\n".join(body_parts)

        page     = generate_chapter_page(num, label, html_body)
        out_path = OUT_DIR / f"chapter-{num:02d}.html"
        out_path.write_text(page, encoding="utf-8")
        print(f"  wrote {out_path}")

    print("\nDone. Run `bundle exec jekyll serve` to preview.")


if __name__ == "__main__":
    main()
