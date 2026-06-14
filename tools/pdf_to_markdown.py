#!/usr/bin/env python
"""Convert the EmblemPrintShop source PDFs to chapter-split Markdown.

Output goes to ./Markdown/<book-slug>/ with one .md file per detected chapter,
plus a per-book README.md index. A top-level Markdown/README.md summarises all
books and the conversion quality.

These are scanned historical books with embedded OCR text layers of varying
quality. Chapter boundaries are detected from text headings (no PDF has an
embedded table of contents). Where heading detection looks unreliable the book
falls back to a single whole-text file so nothing is lost.
"""
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Markdown"

# ---------------------------------------------------------------------------
# Per-book configuration
#
# splitter is one of:
#   ("label_change", regex)        new chapter each time the matched, normalised
#                                  heading label differs from the current one
#   ("marker_gap", regex, gap)     new chapter on each heading line that is at
#                                  least <gap> pages after the previous split;
#                                  chapters numbered sequentially
#   ("whole",)                     single whole-text file (OCR/structure too
#                                  noisy to chapter reliably)
#   ("none", reason)               cannot convert (no text layer)
# ---------------------------------------------------------------------------
BOOKS = [
    {
        "slug": "rosarium",
        "title": "Rosarium Philosophorum (English transcription, MS Ferguson 210)",
        "pdf": "sources/rosarium/rosarium.pdf",
        "splitter": ("label_change", re.compile(r"^Rosarium Philosophorum \(part \d+\)", re.I)),
    },
    {
        "slug": "splendor_solis",
        "title": "Splendor Solis (English translation)",
        "pdf": "sources/splendor_solis/SplendorSolis.pdf",
        "splitter": ("label_change",
                     re.compile(r"^THE (FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH) TREATISE")),
    },
    {
        "slug": "cramer_emblemata_sacra",
        "title": "Daniel Cramer — Emblemata Sacra (Decades Quinque Emblematum)",
        "pdf": "sources/cramer/emblematasacraho00cram.pdf",
        # EMBLEMA but not the title-page word EMBLEMATUM
        "splitter": ("marker_gap", re.compile(r"^/?EMBLEMA(?!TUM)"), 2),
    },
    {
        "slug": "fludd_mosaicall_philosophy",
        "title": "Robert Fludd — Mosaicall Philosophy (1659)",
        "pdf": "sources/fludd/bim_early-english-books-1641-1700_mosaicall-philosophy-_fludd-robert_1659.pdf",
        "splitter": ("marker_gap", re.compile(r"^CHAP[\.,]"), 1),
    },
    {
        "slug": "maier_viatorium",
        "title": "Michael Maier — Viatorium (De Montibus Planetarum Septem)",
        "pdf": "sources/maier_viatorium/majeriviatoriumh00maie.pdf",
        # only standalone heading lines "De Monte <planet>.", not prose mentions
        "splitter": ("marker_gap", re.compile(r"^[\^T>i\s]*[Dd]e\s+Monte\s+\w+\.?\s*$"), 3),
    },
    {
        "slug": "maier_arcana_arcanissima",
        "title": "Michael Maier — Arcana Arcanissima (Hieroglyphica Aegyptio-Graeca)",
        "pdf": "sources/maier_arcana/arcanaarcanissim00maie.pdf",
        # 6 books, but the Latin running-header OCR is too garbled to split on.
        "splitter": ("whole",),
    },
    {
        "slug": "khunrath_amphitheatrum",
        "title": "Heinrich Khunrath — Amphitheatrum Sapientiae Aeternae",
        "pdf": "sources/khunrath/BIUSante_pharma_res005272.pdf",
        "splitter": ("whole",),
    },
    {
        "slug": "hall_manuscripts",
        "title": "Manly Palmer Hall — Alchemical Manuscripts (Box 18 v6)",
        "pdf": "sources/hall_manuscripts/manlypalmerhabox18v6hall.pdf",
        "splitter": ("whole",),
    },
    {
        "slug": "maier_atalanta_fugiens",
        "title": "Michael Maier — Atalanta Fugiens (Mellon 48)",
        "pdf": "sources/maier_af_mellon/mellon48atalanta.pdf",
        "splitter": ("none", "PDF has no embedded text layer (image-only scan); "
                             "OCR required and no OCR engine is installed."),
    },
]

MIN_CHAPTERS, MAX_CHAPTERS = 3, 120  # plausibility band for auto-chaptering


def clean_page(text: str) -> str:
    """Light, lossless-ish cleanup of one page of OCR text."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out, blanks = [], 0
    for ln in lines:
        if not ln.strip():
            blanks += 1
            if blanks <= 1:
                out.append("")
            continue
        blanks = 0
        out.append(ln)
    text = "\n".join(out).strip()
    # de-hyphenate words broken across line ends: "exam-\nple" -> "example"
    text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)
    return text


def slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "section"


def write_chapter(book_dir: Path, idx: int, title: str, pages, parts):
    """Write one chapter file; pages is (first,last) 0-based; parts list of (pno,text)."""
    fname = f"{idx:02d}-{slugify(title)[:50]}.md"
    body = [f"# {title}", ""]
    for pno, txt in parts:
        body.append(f"<!-- page {pno + 1} -->")
        body.append("")
        body.append(txt)
        body.append("")
    (book_dir / fname).write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
    return fname, pages


def convert(book) -> dict:
    pdf = ROOT / book["pdf"]
    book_dir = OUT / book["slug"]
    book_dir.mkdir(parents=True, exist_ok=True)
    for old in book_dir.glob("*.md"):  # clear stale output from prior runs
        old.unlink()
    doc = fitz.open(pdf)
    npages = doc.page_count
    pages = [(i, clean_page(doc[i].get_text())) for i in range(npages)]
    kind = book["splitter"][0]
    result = {"slug": book["slug"], "title": book["title"], "pages": npages,
              "pdf": book["pdf"], "kind": kind, "chapters": [], "note": ""}

    if kind == "none":
        reason = book["splitter"][1]
        (book_dir / "README.md").write_text(
            f"# {book['title']}\n\n**Not converted.** {reason}\n\n"
            f"Source: `{book['pdf']}` ({npages} pages).\n", encoding="utf-8")
        result["note"] = reason
        return result

    chapters = []  # list of dict(title, parts=[(pno,text)], first,last)

    def detect_chapters():
        if kind == "whole":
            return None
        regex = book["splitter"][1]
        cur = None
        if kind == "label_change":
            for pno, txt in pages:
                label = None
                for ln in txt.splitlines():
                    m = regex.search(ln.strip())
                    if m:
                        label = re.sub(r"\s+", " ", m.group(0)).strip()
                        break
                if label and (cur is None or label.lower() != cur["title"].lower()):
                    cur = {"title": label, "parts": [], "first": pno}
                    chapters.append(cur)
                if cur is not None:
                    cur["parts"].append((pno, txt))
        elif kind == "marker_gap":
            gap = book["splitter"][2]
            last_split = -10
            for pno, txt in pages:
                head = None
                for ln in txt.splitlines():
                    s = ln.strip()
                    # real headings are short standalone lines, not prose mentions
                    if len(s) <= 40 and regex.search(s):
                        head = re.sub(r"\s+", " ", s).strip("/^ ")
                        break
                if head is not None and pno - last_split >= gap:
                    cur = {"title": head or None, "parts": [], "first": pno}
                    chapters.append(cur)
                    last_split = pno
                if cur is not None:
                    cur["parts"].append((pno, txt))
        # capture any leading pages before the first detected heading so no
        # content is lost (front matter, or sections whose OCR heading was missed)
        if chapters and chapters[0]["first"] > 0:
            lead = [(pno, txt) for pno, txt in pages if pno < chapters[0]["first"]]
            chapters.insert(0, {"title": "Front matter", "parts": lead, "first": 0})
        return chapters

    detected = detect_chapters()
    use_whole = (kind == "whole") or (detected is None) or not (
        MIN_CHAPTERS <= len(detected) <= MAX_CHAPTERS)

    if use_whole:
        if kind != "whole":
            result["note"] = (f"heading detection found {len(detected) if detected else 0} "
                              f"sections (outside {MIN_CHAPTERS}-{MAX_CHAPTERS}); "
                              f"wrote single whole-text file instead")
            result["kind"] = "whole(fallback)"
        body = [f"# {book['title']}", ""]
        for pno, txt in pages:
            body.append(f"<!-- page {pno + 1} -->")
            body.append("")
            if txt:
                body.append(txt)
                body.append("")
        fname = "00-full-text.md"
        (book_dir / fname).write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
        result["chapters"].append({"file": fname, "title": book["title"],
                                   "pages": f"1-{npages}"})
    else:
        # number sequentially; assign titles
        for n, ch in enumerate(chapters, 1):
            first = ch["first"]
            last = ch["parts"][-1][0]
            if ch["title"]:
                title = f"{n:02d} — {ch['title']}"
            else:
                title = f"Chapter {n:02d}"
            fname, _ = write_chapter(book_dir, n, title, (first, last), ch["parts"])
            result["chapters"].append({"file": fname, "title": title,
                                       "pages": f"{first + 1}-{last + 1}"})

    # per-book index
    idx = [f"# {book['title']}", "",
           f"Source PDF: `{book['pdf']}` — {npages} pages.", ""]
    if result["note"]:
        idx.append(f"> Note: {result['note']}")
        idx.append("")
    idx.append("## Chapters")
    idx.append("")
    for c in result["chapters"]:
        idx.append(f"- [{c['title']}]({c['file']}) — pp. {c['pages']}")
    (book_dir / "README.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    return result


def main():
    OUT.mkdir(exist_ok=True)
    results = []
    for book in BOOKS:
        print(f"converting {book['slug']} ...", flush=True)
        try:
            results.append(convert(book))
        except Exception as e:  # noqa
            print(f"  ERROR: {e}", file=sys.stderr)
            results.append({"slug": book["slug"], "title": book["title"],
                            "kind": "error", "note": str(e), "chapters": [],
                            "pages": "?", "pdf": book["pdf"]})

    # top-level index
    top = ["# EmblemPrintShop — Source Books as Markdown", "",
           "Converted from the scanned PDFs under `sources/`. Each book is a "
           "subfolder of chapter Markdown files plus a `README.md` index.", "",
           "These are historical books with embedded OCR text layers of varying "
           "quality; the Markdown reflects the OCR as-is (page numbers marked with "
           "`<!-- page N -->`). No PDF had an embedded table of contents, so "
           "chapters were detected from text headings.", "",
           "| Book | Pages | Result | Notes |", "|---|---|---|---|"]
    for r in results:
        nch = len(r["chapters"])
        if r["kind"] == "none":
            res = "not converted"
        elif r["kind"].startswith("whole"):
            res = "whole-text (1 file)"
        elif r["kind"] == "error":
            res = "error"
        else:
            res = f"{nch} chapters"
        note = r.get("note", "")
        top.append(f"| [{r['title']}]({r['slug']}/README.md) | {r['pages']} | {res} | {note} |")
    (OUT / "README.md").write_text("\n".join(top) + "\n", encoding="utf-8")

    print("\nSummary:")
    for r in results:
        print(f"  {r['slug']:30s} {r['kind']:18s} {len(r['chapters'])} files")


if __name__ == "__main__":
    main()
