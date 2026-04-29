"""Small cross-cutting helpers."""
from __future__ import annotations

import csv
import io
from pathlib import Path


def parse_quotes(text: str) -> list[str]:
    """Turn a multi-line / multi-paragraph blob into a clean list of quotes.

    - Empty lines separate quotes
    - Lines beginning with ``#`` are treated as comments
    - Each quote is trimmed; blanks are dropped.
    """
    quotes: list[str] = []
    buf: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("#"):
            continue
        if not line.strip():
            if buf:
                quotes.append(" ".join(buf).strip())
                buf = []
            continue
        buf.append(line)
    if buf:
        quotes.append(" ".join(buf).strip())
    return [q for q in quotes if q]


def import_quotes_from_path(path: str | Path) -> list[str]:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix.lower() == ".csv":
        out: list[str] = []
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            for cell in row:
                cell = cell.strip()
                if cell:
                    out.append(cell)
        return out
    return parse_quotes(text)


def humanize_seconds(s: float) -> str:
    s = max(0.0, float(s))
    m, sec = divmod(int(round(s)), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"
