from __future__ import annotations

from pathlib import Path

import pandas as pd

from .utils import TARGET_COUNTRIES, normalize_country_code, save_csv


def load_raw_inputs(
    raw_dir: str | Path = "data/raw",
    yields_file: str = "sovereign_yields_fred.csv",
    cds_file: str = "cds_template.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load raw yield and CDS files."""
    raw_dir = Path(raw_dir)
    y = pd.read_csv(raw_dir / yields_file)
    # Priority order: MacroMicro import > paper-graph reconstruction > manual template
    mm_path = raw_dir / "cds_from_macromicro.csv"
    reconstructed = raw_dir / "cds_from_paper_graphs_monthly.csv"
    if mm_path.exists():
        c = pd.read_csv(mm_path)
        if "cds" not in c.columns or pd.to_numeric(c["cds"], errors="coerce").notna().sum() == 0:
            c = pd.read_csv(raw_dir / cds_file)
    elif reconstructed.exists():
        c = pd.read_csv(reconstructed)
        if "cds" not in c.columns or pd.to_numeric(c["cds"], errors="coerce").notna().sum() == 0:
            c = pd.read_csv(raw_dir / cds_file)
    else:
        c = pd.read_csv(raw_dir / cds_file)
    return y, c


def clean_panel(yields_df: pd.DataFrame, cds_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Harmonize dates/countries and align yields with CDS.

    Output:
    - long panel: date, country, yield, cds
    - yield wide matrix
    - cds wide matrix
    """
    y = yields_df.copy()
    c = cds_df.copy()

    y["date"] = pd.to_datetime(y["date"], errors="coerce")
    c["date"] = pd.to_datetime(c["date"], errors="coerce")

    y["country"] = y["country"].map(normalize_country_code)
    c["country"] = c["country"].map(normalize_country_code)

    y = y[y["country"].isin(TARGET_COUNTRIES)].dropna(subset=["date", "country", "yield"])
    c = c[c["country"].isin(TARGET_COUNTRIES)].dropna(subset=["date", "country"])

    y["yield"] = pd.to_numeric(y["yield"], errors="coerce")
    c["cds"] = pd.to_numeric(c["cds"], errors="coerce")

    # Unit harmonization:
    # Sovereign yields in this pipeline are in percent units (e.g., 3.5).
    # MacroMicro CDS series are commonly in basis points (e.g., 120 bp).
    # If CDS magnitudes suggest bps, convert to percent points.
    cds_median = c["cds"].dropna().median()
    if pd.notna(cds_median) and cds_median > 5:
        c["cds"] = c["cds"] / 100.0

    y = y.dropna(subset=["yield"]).sort_values(["date", "country"])
    c = c.sort_values(["date", "country"])

    # Keep last if duplicates exist in manual files.
    y = y.drop_duplicates(subset=["date", "country"], keep="last")
    c = c.drop_duplicates(subset=["date", "country"], keep="last")

    panel = y.merge(c[["date", "country", "cds"]], on=["date", "country"], how="left")
    panel = panel[["date", "country", "yield", "cds"]].sort_values(["date", "country"]).reset_index(drop=True)

    yield_wide = panel.pivot(index="date", columns="country", values="yield").sort_index()
    cds_wide = panel.pivot(index="date", columns="country", values="cds").sort_index()

    return panel, yield_wide, cds_wide


def run_data_cleaning(
    raw_dir: str | Path = "data/raw",
    processed_dir: str | Path = "data/processed",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load, clean, align, and save panel + wide matrices."""
    yields_df, cds_df = load_raw_inputs(raw_dir=raw_dir)
    panel, yield_wide, cds_wide = clean_panel(yields_df, cds_df)

    processed_dir = Path(processed_dir)
    save_csv(panel, processed_dir / "panel.csv", index=False)
    save_csv(yield_wide.reset_index(), processed_dir / "yield_wide.csv", index=False)
    save_csv(cds_wide.reset_index(), processed_dir / "cds_wide.csv", index=False)
    return panel, yield_wide, cds_wide
