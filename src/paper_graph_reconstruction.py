from __future__ import annotations

from pathlib import Path

import pandas as pd

from .utils import TARGET_COUNTRIES, save_csv


def create_graph_anchor_template(
    yields_df: pd.DataFrame,
    raw_dir: str | Path = "data/raw",
    freq: str = "MS",
) -> Path:
    """
    Create a monthly anchor template for CDS reconstruction from paper charts.

    Fill selected rows manually with values digitized from academic figures.
    """
    raw_dir = Path(raw_dir)
    d = yields_df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    min_date = d["date"].min()
    max_date = d["date"].max()
    if pd.isna(min_date) or pd.isna(max_date):
        min_date = pd.Timestamp("2005-01-01")
        max_date = pd.Timestamp("2025-12-01")

    monthly = pd.date_range(min_date, max_date, freq=freq)
    grid = pd.MultiIndex.from_product([monthly, TARGET_COUNTRIES], names=["date", "country"]).to_frame(index=False)
    grid["cds"] = pd.NA
    grid["source_note"] = pd.NA

    out_path = raw_dir / "cds_graph_anchor_points.csv"
    save_csv(grid, out_path, index=False)
    return out_path


def reconstruct_monthly_cds_from_anchors(
    raw_dir: str | Path = "data/raw",
    min_anchor_points_per_country: int = 3,
) -> pd.DataFrame:
    """
    Build monthly CDS proxy by interpolating manually digitized anchor points.

    This is explicitly an approximation from published charts, not original vendor data.
    """
    raw_dir = Path(raw_dir)
    path = raw_dir / "cds_graph_anchor_points.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing anchor file: {path}")

    anchors = pd.read_csv(path)
    anchors["date"] = pd.to_datetime(anchors["date"], errors="coerce")
    anchors["country"] = anchors["country"].astype(str).str.upper().str.strip()
    anchors["cds"] = pd.to_numeric(anchors["cds"], errors="coerce")
    anchors = anchors[anchors["country"].isin(TARGET_COUNTRIES)].copy()

    frames = []
    for c, g in anchors.groupby("country"):
        g = g.sort_values("date").copy()
        n = g["cds"].notna().sum()
        if n < min_anchor_points_per_country:
            # Keep NA series if insufficient anchors; avoids silent fabrication.
            frames.append(g[["date", "country", "cds"]])
            continue
        g["cds"] = g["cds"].interpolate(method="time", limit_direction="both")
        frames.append(g[["date", "country", "cds"]])

    out = pd.concat(frames, ignore_index=True).sort_values(["date", "country"])
    out_path = raw_dir / "cds_from_paper_graphs_monthly.csv"
    save_csv(out, out_path, index=False)
    return out
