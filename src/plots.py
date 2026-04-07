from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _save_fig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def generate_plots(
    factor_panel: pd.DataFrame,
    factors: pd.DataFrame,
    analysis_outputs: dict[str, pd.DataFrame],
    figures_dir: str | Path = "output/figures",
) -> None:
    """Generate and save requested figures for the report."""
    figures_dir = Path(figures_dir)
    plt.style.use("seaborn-v0_8-whitegrid")

    # 1) Sovereign spreads vs DE.
    fig, ax = plt.subplots(figsize=(11, 5))
    for c, g in factor_panel[factor_panel["country"] != "DE"].groupby("country"):
        ax.plot(pd.to_datetime(g["date"]), g["spread_vs_de"], label=c, linewidth=1.25)
    ax.set_title("Sovereign Spreads vs Germany")
    ax.set_ylabel("Spread")
    ax.legend(ncol=4, fontsize=8)
    _save_fig(figures_dir / "01_spreads_vs_de.png")

    # 2) CDS-adjusted yields.
    fig, ax = plt.subplots(figsize=(11, 5))
    for c, g in factor_panel.groupby("country"):
        ax.plot(pd.to_datetime(g["date"]), g["r_tilde"], label=c, linewidth=1.25)
    ax.set_title("CDS-adjusted Yields")
    ax.set_ylabel("r_tilde = yield - cds")
    ax.legend(ncol=4, fontsize=8)
    _save_fig(figures_dir / "02_cds_adjusted_yields.png")

    # 3) Basis by country.
    fig, ax = plt.subplots(figsize=(11, 5))
    for c, g in factor_panel[factor_panel["country"] != "DE"].groupby("country"):
        ax.plot(pd.to_datetime(g["date"]), g["basis"], label=c, linewidth=1.25)
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Basis vs Germany")
    ax.set_ylabel("basis = r_tilde_i - r_tilde_DE")
    ax.legend(ncol=4, fontsize=8)
    _save_fig(figures_dir / "03_basis_by_country.png")

    # 4) L_t factor.
    if "L_t_equal" in factors.columns:
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(pd.to_datetime(factors["date"]), factors["L_t_equal"], color="tab:red", linewidth=1.8)
        if "L_t_proxy_spread_only" in factors.columns:
            ax.plot(pd.to_datetime(factors["date"]), factors["L_t_proxy_spread_only"], color="tab:orange", linewidth=1.2, alpha=0.8)
        ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
        ax.set_title("Aggregate Factor (CDS-adjusted and spread-only proxy)")
        ax.set_ylabel("L_t_equal")
        _save_fig(figures_dir / "04_L_t.png")

    # 5) Dispersion metrics.
    disp_cols = [c for c in ["std_basis_t", "mad_basis_t", "range_basis_t", "iqr_basis_t"] if c in factors.columns]
    if factors.get("std_basis_t", pd.Series(dtype=float)).notna().sum() == 0:
        disp_cols = [c for c in ["std_basis_proxy_t", "mad_basis_proxy_t", "range_basis_proxy_t", "iqr_basis_proxy_t"] if c in factors.columns]
    if disp_cols:
        fig, ax = plt.subplots(figsize=(11, 5))
        for col in disp_cols:
            ax.plot(pd.to_datetime(factors["date"]), factors[col], label=col, linewidth=1.4)
        ax.set_title("Cross-sectional Dispersion (basis or spread-only proxy)")
        ax.legend(ncol=2, fontsize=8)
        _save_fig(figures_dir / "05_dispersion_metrics_basis.png")

    # 6) PCA scree raw spreads.
    spread_var = analysis_outputs.get("spread_pca_var", pd.DataFrame())
    if not spread_var.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(spread_var["component"], spread_var["explained_ratio"])
        ax.set_title("PCA Scree: Raw Spreads vs DE")
        ax.set_ylabel("Explained variance ratio")
        _save_fig(figures_dir / "06_pca_scree_spreads.png")

    # 7) PCA scree basis.
    basis_var = analysis_outputs.get("basis_pca_var", pd.DataFrame())
    if not basis_var.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(basis_var["component"], basis_var["explained_ratio"])
        ax.set_title("PCA Scree: Basis Matrix")
        ax.set_ylabel("Explained variance ratio")
        _save_fig(figures_dir / "07_pca_scree_basis.png")

    # 8) Correlation heatmap.
    corr = analysis_outputs.get("corr_table", pd.DataFrame())
    if not corr.empty:
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(corr.values, aspect="auto")
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.index)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.index)
        ax.set_title("Correlation Heatmap")
        fig.colorbar(im, ax=ax)
        _save_fig(figures_dir / "08_correlation_heatmap.png")

    # 9) L_t vs std_basis.
    if {"L_t_equal", "std_basis_t"}.issubset(factors.columns):
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(pd.to_datetime(factors["date"]), factors["L_t_equal"], label="L_t_equal", linewidth=1.5)
        std_series = "std_basis_t"
        if factors["std_basis_t"].notna().sum() == 0 and "std_basis_proxy_t" in factors.columns:
            std_series = "std_basis_proxy_t"
        ax.plot(pd.to_datetime(factors["date"]), factors[std_series], label=std_series, linewidth=1.5)
        ax.set_title("Average Factor vs Dispersion Metric")
        ax.legend()
        _save_fig(figures_dir / "09_L_t_vs_std_basis.png")
