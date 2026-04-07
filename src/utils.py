from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


TARGET_COUNTRIES = ["DE", "IT", "ES", "FR", "BE", "NL", "AT", "FI"]


def ensure_dirs(paths: Iterable[str | Path]) -> None:
    """Create directories if they do not exist."""
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, path: str | Path, index: bool = False) -> None:
    """Persist a dataframe as CSV with parent-dir creation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def normalize_country_code(value: str) -> str:
    """Normalize country labels to upper-case 2-letter codes."""
    if value is None:
        return value
    text = str(value).strip().upper()
    # Minimal alias handling to stay robust with manual input files.
    aliases = {
        "GERMANY": "DE",
        "ITALY": "IT",
        "SPAIN": "ES",
        "FRANCE": "FR",
        "BELGIUM": "BE",
        "NETHERLANDS": "NL",
        "AUSTRIA": "AT",
        "FINLAND": "FI",
    }
    return aliases.get(text, text)
