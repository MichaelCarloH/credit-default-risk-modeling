from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .utils import save_csv


def _median_absolute_deviation(values: pd.Series) -> float:
    med = values.median()
    return (values - med).abs().median()


def build_factor_panel(panel: pd.DataFrame, germany_code: str = "DE") -> pd.DataFrame:
    """
    Build spread, CDS-adjusted yield, and basis series in long format.

    Economic caution:
    r_tilde = yield - CDS is not a pure risk-free yield. It still embeds basis,
    liquidity, segmentation, and market-pricing frictions.
    """
    d = panel.copy()
    d = d.dropna(subset=["date", "country", "yield"]).sort_values(["date", "country"])

    de = (
        d[d["country"] == germany_code][["date", "yield", "cds"]]
        .rename(columns={"yield": "yield_de", "cds": "cds_de"})
        .drop_duplicates(subset=["date"], keep="last")
    )
    out = d.merge(de, on="date", how="inner")

    out["spread_vs_de"] = out["yield"] - out["yield_de"]
    out["r_tilde"] = out["yield"] - out["cds"]
    out["r_tilde_de"] = out["yield_de"] - out["cds_de"]
    out["basis"] = out["r_tilde"] - out["r_tilde_de"]
    # Fallback proxy when CDS is missing: uses raw spread only.
    # This is NOT a CDS-adjusted basis; it is a spread-only fragmentation proxy.
    out["basis_proxy_spread_only"] = out["spread_vs_de"]
    out["has_cds_pair"] = out["cds"].notna() & out["cds_de"].notna()

    return out


def aggregate_L_t(factor_panel: pd.DataFrame, weight_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Compute average non-German basis factor L_t.
    """
    d = factor_panel[factor_panel["country"] != "DE"].copy()

    eq = d.groupby("date", as_index=False).agg(
        L_t_equal=("basis", "mean"),
        L_t_proxy_spread_only=("basis_proxy_spread_only", "mean"),
        cds_pair_ratio=("has_cds_pair", "mean"),
        n_countries_l_t=("basis", lambda x: x.notna().sum()),
        n_countries_proxy=("basis_proxy_spread_only", lambda x: x.notna().sum()),
    )

    if weight_df is None or weight_df.empty:
        return eq

    w = weight_df.copy()
    w["country"] = w["country"].astype(str).str.upper().str.strip()
    if "weight" not in w.columns:
        raise ValueError("weight_df must contain a 'weight' column.")

    merged = d.merge(w[["country", "weight"]], on="country", how="inner").dropna(subset=["weight", "basis"])
    merged["wb"] = merged["weight"] * merged["basis"]
    weighted = merged.groupby("date", as_index=False).agg(wb=("wb", "sum"), w=("weight", "sum"))
    weighted = weighted[weighted["w"] > 0]
    weighted["L_t_weighted"] = weighted["wb"] / weighted["w"]
    return eq.merge(weighted[["date", "L_t_weighted"]], on="date", how="left")


def compute_dispersion_metrics(factor_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cross-sectional dispersion metrics for basis and spreads.
    """
    d = factor_panel[factor_panel["country"] != "DE"].copy()

    def _agg(x: pd.Series) -> pd.Series:
        x = x.dropna()
        if x.empty:
            return pd.Series(
                {
                    "std": np.nan,
                    "mad": np.nan,
                    "range": np.nan,
                    "iqr": np.nan,
                }
            )
        return pd.Series(
            {
                "std": x.std(ddof=1),
                "mad": _median_absolute_deviation(x),
                "range": x.max() - x.min(),
                "iqr": x.quantile(0.75) - x.quantile(0.25),
            }
        )

    basis_disp = d.groupby("date")["basis"].apply(_agg).unstack()
    basis_disp.columns = [f"{c}_basis_t" for c in basis_disp.columns]
    basis_disp = basis_disp.reset_index()

    spread_disp = d.groupby("date")["spread_vs_de"].apply(_agg).unstack()
    spread_disp.columns = [f"{c}_spread_t" for c in spread_disp.columns]
    spread_disp = spread_disp.reset_index()

    out = basis_disp.merge(spread_disp, on="date", how="outer").sort_values("date")
    # Explicit spread-only fallback metrics for periods without CDS.
    out["std_basis_proxy_t"] = out["std_spread_t"]
    out["mad_basis_proxy_t"] = out["mad_spread_t"]
    out["range_basis_proxy_t"] = out["range_spread_t"]
    out["iqr_basis_proxy_t"] = out["iqr_spread_t"]
    return out


def run_factor_construction(
    panel: pd.DataFrame,
    processed_dir: str | Path = "data/processed",
    weight_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build full factor output and save `data/processed/factors.csv`.
    """
    factor_panel = build_factor_panel(panel)
    L_t = aggregate_L_t(factor_panel, weight_df=weight_df)
    disp = compute_dispersion_metrics(factor_panel)

    factors = (
        L_t.merge(disp, on="date", how="outer")
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Also add average spread for compact analysis tables.
    avg_spread = (
        factor_panel[factor_panel["country"] != "DE"]
        .groupby("date", as_index=False)["spread_vs_de"]
        .mean()
        .rename(columns={"spread_vs_de": "avg_spread_t"})
    )
    factors = factors.merge(avg_spread, on="date", how="left")

    save_csv(factors, Path(processed_dir) / "factors.csv", index=False)
    return factor_panel, factors
