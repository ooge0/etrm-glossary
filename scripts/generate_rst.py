"""
Generate Sphinx/RST pages from the ETRM glossary markdown.

Reads : etrm_wiki_glossary.md     (order | Term | Category | Definition)
Writes: docs/glossary/*.rst       (index, alphabetical, per-category pages)

Usage:
    python scripts/generate_rst.py
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ─────────────────────────────────────────────────────────────────────────
# Category metadata
# ─────────────────────────────────────────────────────────────────────────

CATEGORY_TITLES: dict[str, str] = {
    "s_1": "Energy Markets Training Program",
    "s_2": "Energy Hedging & Risk Management Glossary",
    "gl_trm_1": "Homefield Energy Glossary",
    "basics": "Basics",
    "product": "Products & Platforms",
    "vendor": "Vendors & Exchanges",
    "team": "Team & Roles",
    "etrm_basics": "ETRM Basics",
    "other": "Other",
}

RST_UNDERLINES = "=-~^\"'`#*+"

# ─────────────────────────────────────────────────────────────────────────
# Normalization
# ─────────────────────────────────────────────────────────────────────────


def normalize_category(raw: str) -> str:
    """Lowercase, trim, collapse whitespace, fix known typos.

    Guarantees a non-empty result. Unknown categories fall back to 'other'.
    """
    cat = (raw or "").strip().lower()
    cat = re.sub(r"\s+", "_", cat)      # 'ETRM basics' -> 'etrm_basics'
    cat = re.sub(r"[^a-z0-9_]+", "", cat)
    cat = cat.replace("ohter", "other").replace("oter", "other")
    return cat or "other"


def slug(category: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (category or "").lower()).strip("_")
    return s or "other"


# ─────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Row:
    order: int
    term: str
    category: str
    definition: str


@dataclass
class Glossary:
    rows: list[Row] = field(default_factory=list)
    intro_md: str = ""

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def unique_terms(self) -> int:
        return len({r.term.lower() for r in self.rows})

    @property
    def duplicate_terms(self) -> int:
        return self.total - self.unique_terms

    def by_category(self) -> dict[str, list[Row]]:
        out: dict[str, list[Row]] = defaultdict(list)
        for r in self.rows:
            out[r.category].append(r)
        for items in out.values():
            items.sort(key=lambda r: r.term.lower())
        return dict(out)

    def unique_by_term(self) -> dict[str, list[Row]]:
        grouped: dict[str, list[Row]] = defaultdict(list)
        for r in self.rows:
            grouped[r.term].append(r)
        return {k: grouped[k] for k in sorted(grouped, key=str.lower)}


# ─────────────────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────────────────

_HEADER_MARKER = "Term"


def parse_markdown(path: Path) -> Glossary:
    lines = path.read_text(encoding="utf-8").splitlines()

    header_idx: int | None = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("|") and _HEADER_MARKER in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"No glossary table header found in {path}")

    intro_lines: list[str] = []
    for line in lines[:header_idx]:
        if line.strip().lower().startswith("## glossary"):
            break
        intro_lines.append(line)

    rows: list[Row] = []
    for raw in lines[header_idx + 2:]:
        stripped = raw.strip()
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 4:
            continue
        try:
            order = int(cells[0])
        except ValueError:
            continue
        term = cells[1].lstrip("*").strip()
        if not term:
            continue
        rows.append(
            Row(
                order=order,
                term=term,
                category=normalize_category(cells[2]),
                definition=cells[3],
            )
        )

    return Glossary(rows=rows, intro_md="\n".join(intro_lines).strip())


# ─────────────────────────────────────────────────────────────────────────
# RST rendering helpers
# ─────────────────────────────────────────────────────────────────────────


def escape_rst(text: str) -> str:
    t = (
        (text or "")
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", " ")
        .strip()
    )
    if t.count("`") % 2:
        t = t.replace("`", "\\`")
    return t


def safe_code(s: str, fallback: str = "unknown") -> str:
    """Produce a string safe to wrap in RST ``double backticks``."""
    cleaned = re.sub(r"[`\s]+", "_", (s or "")).strip("_")
    return cleaned or fallback


def rst_heading(title: str, level: int = 1) -> str:
    underline = RST_UNDERLINES[level - 1] * max(len(title), 3)
    return f"{title}\n{underline}\n\n"


def render_list_table(rows: Iterable[Row]) -> str:
    out = [
        ".. list-table::",
        "   :header-rows: 1",
        "   :widths: auto",
        "   :class: glossary-table",
        "",
        "   * - #",
        "     - Term",
        "     - Definition",
    ]
    for r in rows:
        out.append(f"   * - {r.order}")
        out.append(f"     - **{escape_rst(r.term)}**")
        out.append(f"     - {escape_rst(r.definition)}")
    return "\n".join(out) + "\n"


def render_glossary_directive(glossary: Glossary) -> str:
    out = [".. glossary::\n   :sorted:\n\n"]
    for term, entries in glossary.unique_by_term().items():
        out.append(f"   {term}\n")
        if len(entries) == 1:
            out.append(f"      {escape_rst(entries[0].definition)}\n\n")
        else:
            for e in entries:
                src = CATEGORY_TITLES.get(e.category, e.category)
                out.append(f"      *{src}* — {escape_rst(e.definition)}\n")
            out.append("\n")
    return "".join(out)


# ─────────────────────────────────────────────────────────────────────────
# Page writers
# ─────────────────────────────────────────────────────────────────────────


def render_index(glossary: Glossary, by_cat: dict[str, list[Row]]) -> str:
    parts = [rst_heading("Glossary")]
    parts.append(
        f"**{glossary.total}** terms · "
        f"**{glossary.unique_terms}** unique · "
        f"**{glossary.duplicate_terms}** duplicated across sources.\n\n"
    )

    parts.append(".. toctree::\n   :maxdepth: 1\n   :caption: Views\n\n")
    parts.append("   alphabetical\n\n")

    parts.append(".. toctree::\n   :maxdepth: 1\n   :caption: By source\n\n")
    seen_slugs: set[str] = set()
    for cat in sorted(by_cat, key=lambda c: CATEGORY_TITLES.get(c, c)):
        s = slug(cat)
        if s in seen_slugs:
            continue
        seen_slugs.add(s)
        parts.append(f"   {s}\n")
    parts.append("\n")

    parts.append(rst_heading("Sources", level=2))
    parts.append(".. list-table::\n   :header-rows: 1\n   :widths: 20 80\n\n")
    parts.append("   * - Code\n     - Description\n")
    seen_slugs = set()
    for cat in sorted(by_cat, key=lambda c: CATEGORY_TITLES.get(c, c)):
        s = slug(cat)
        if s in seen_slugs:
            continue
        seen_slugs.add(s)
        parts.append(
            f"   * - ``{safe_code(cat)}``\n"
            f"     - {CATEGORY_TITLES.get(cat, cat)}\n"
        )

    return "".join(parts)


def write_pages(glossary: Glossary, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_cat = glossary.by_category()

    expected = {"index.rst", "alphabetical.rst"} | {
        f"{slug(cat)}.rst" for cat in by_cat
    }
    for existing in out_dir.glob("*.rst"):
        if existing.name not in expected:
            print(f"Removing stale: {existing}")
            existing.unlink()

    (out_dir / "index.rst").write_text(
        render_index(glossary, by_cat),
        encoding="utf-8",
        newline="\n",
    )

    (out_dir / "alphabetical.rst").write_text(
        rst_heading("Alphabetical index")
        + "Terms are deduplicated across sources. Where a term appears "
          "in several glossaries, every definition is shown next to its source.\n\n"
        + render_glossary_directive(glossary),
        encoding="utf-8",
        newline="\n",
    )

    for cat, items in by_cat.items():
        title = CATEGORY_TITLES.get(cat) or cat.replace("_", " ").title() or "Other"
        cat_label = safe_code(cat)
        body = (
            rst_heading(title)
            + f"*{len(items)} terms* · source code: ``{cat_label}``\n\n"
            + render_list_table(items)
        )
        (out_dir / f"{slug(cat)}.rst").write_text(
            body, encoding="utf-8", newline="\n"
        )


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("etrm_wiki_glossary.md"),
        help="Path to the markdown glossary (default: etrm_wiki_glossary.md)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/glossary"),
        help="Output directory for generated RST (default: docs/glossary)",
    )
    args = parser.parse_args()

    glossary = parse_markdown(args.source)
    write_pages(glossary, args.out)

    print(
        f"Generated {glossary.total} terms "
        f"({glossary.unique_terms} unique, "
        f"{glossary.duplicate_terms} duplicated) → {args.out}"
    )


if __name__ == "__main__":
    main()