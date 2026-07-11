import csv
import io
from datetime import date, datetime
from typing import Optional

import pandas as pd

# Ambiguous numeric dates are day-first (DD/MM/YYYY); month-first is a last resort
# for values that cannot be day-first (e.g. 07/25/2026).
_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
    "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y",
    "%B %d, %Y", "%b %d, %Y",
]


def parse_csv(file_bytes: bytes) -> pd.DataFrame:
    # utf-8-sig first so a BOM is stripped rather than leaking into the first header
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not decode file with any supported encoding")

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        sep = dialect.delimiter
    except csv.Error:
        sep = ","

    return pd.read_csv(io.StringIO(text), sep=sep, dtype=str).fillna("")


def normalize_date(val: str) -> Optional[date]:
    val = val.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except Exception:
        return None


def normalize_status(val: str, known: list[str]) -> Optional[str]:
    normalized = val.strip().lower()
    for name in known:
        if name.lower() == normalized:
            return name
    # Fuzzy: prefix match
    for name in known:
        if name.lower().startswith(normalized) or normalized.startswith(name.lower()):
            return name
    return None
