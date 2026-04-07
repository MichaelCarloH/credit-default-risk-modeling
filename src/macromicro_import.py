from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from .utils import TARGET_COUNTRIES, save_csv


COUNTRY_HINTS = {
    "germany": "DE",
    "italy": "IT",
    "spain": "ES",
    "france": "FR",
    "belgium": "BE",
    "netherlands": "NL",
    "austria": "AT",
    "finland": "FI",
}


def _infer_country_from_name(name: str) -> str | None:
    low = name.lower()
    for hint, code in COUNTRY_HINTS.items():
        if hint in low:
            return code
    return None


def _extract_date_value_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    cols = list(df.columns)
    date_col = None
    value_col = None
    for c in cols:
        lc = str(c).lower()
        if date_col is None and ("date" in lc or "time" in lc or "week" in lc):
            date_col = c
        if value_col is None and any(k in lc for k in ["value", "price", "cds", "bp"]):
            value_col = c
    if date_col is None and cols:
        date_col = cols[0]
    if value_col is None and len(cols) >= 2:
        value_col = cols[1]
    return date_col, value_col


def import_macromicro_cds(
    source_dir: str | Path = "data/raw/macromicro",
    output_path: str | Path = "data/raw/cds_from_macromicro.csv",
) -> pd.DataFrame:
    """
    Ingest MacroMicro exported CSVs and normalize to: date,country,cds.

    Expected workflow:
    - User downloads CSV per country from MacroMicro series page.
    - Save all files in data/raw/macromicro/.
    - File name should include country name (e.g., italy_5y_cds.csv).
    """
    source_dir = Path(source_dir)
    files = sorted(source_dir.glob("*.csv"))
    if not files:
        return pd.DataFrame(columns=["date", "country", "cds"])

    rows = []
    for fp in files:
        country = _infer_country_from_name(fp.name)
        if country is None:
            continue
        raw = pd.read_csv(fp)
        if raw.empty:
            continue
        date_col, value_col = _extract_date_value_columns(raw)
        if date_col is None or value_col is None:
            continue
        tmp = raw[[date_col, value_col]].copy()
        tmp.columns = ["date", "cds"]
        tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
        tmp["cds"] = pd.to_numeric(tmp["cds"], errors="coerce")
        tmp["country"] = country
        tmp = tmp.dropna(subset=["date", "cds"])
        rows.append(tmp)

    if not rows:
        return pd.DataFrame(columns=["date", "country", "cds"])

    out = pd.concat(rows, ignore_index=True)
    out = out[out["country"].isin(TARGET_COUNTRIES)].drop_duplicates(subset=["date", "country"], keep="last")
    out = out.sort_values(["date", "country"]).reset_index(drop=True)
    save_csv(out, Path(output_path), index=False)
    return out
