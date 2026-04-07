from __future__ import annotations

from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .utils import save_csv


def _pca_from_wide(wide_df: pd.DataFrame, standardize: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    x = wide_df.dropna(axis=0, how="any")
    if x.shape[0] < 3 or x.shape[1] < 2:
        return pd.DataFrame(), pd.DataFrame()

    values = x.values
    if standardize:
        values = StandardScaler().fit_transform(values)

    pca = PCA()
    pcs = pca.fit_transform(values)
    pc_df = pd.DataFrame({"date": x.index, "PC1": pcs[:, 0]})
    var_df = pd.DataFrame(
        {"component": [f"PC{i + 1}" for i in range(len(pca.explained_variance_ratio_))], "explained_ratio": pca.explained_variance_ratio_}
    )
    return pc_df, var_df


def _run_ols(df: pd.DataFrame, y_col: str, x_cols: list[str]) -> pd.DataFrame:
    d = df[[y_col] + x_cols].dropna().copy()
    if d.empty:
        return pd.DataFrame({"metric": [f"{y_col}~{'+'.join(x_cols)}"], "note": ["insufficient data"]})

    X = sm.add_constant(d[x_cols], has_constant="add")
    y = d[y_col]
    model = sm.OLS(y, X).fit()

    rows = []
    for param in model.params.index:
        rows.append(
            {
                "model": f"{y_col}~{'+'.join(x_cols)}",
                "term": param,
                "coef": model.params[param],
                "tstat": model.tvalues[param],
                "pvalue": model.pvalues[param],
                "r2": model.rsquared,
                "nobs": model.nobs,
            }
        )
    return pd.DataFrame(rows)


def run_analysis(
    factor_panel: pd.DataFrame,
    factors: pd.DataFrame,
    tables_dir: str | Path = "output/tables",
) -> dict[str, pd.DataFrame]:
    """
    Run lightweight empirical checks aligned with paper stylized facts.
    """
    tables_dir = Path(tables_dir)

    # A) Co-movement of raw spreads.
    spreads_wide = (
        factor_panel[factor_panel["country"] != "DE"]
        .pivot(index="date", columns="country", values="spread_vs_de")
        .sort_index()
    )
    spread_corr = spreads_wide.corr()
    spread_pca_pc1, spread_pca_var = _pca_from_wide(spreads_wide, standardize=True)

    # E) PCA on basis.
    basis_wide = (
        factor_panel[factor_panel["country"] != "DE"]
        .pivot(index="date", columns="country", values="basis")
        .sort_index()
    )
    basis_pca_pc1, basis_pca_var = _pca_from_wide(basis_wide, standardize=True)
    basis_pca_source = "cds_adjusted_basis"
    if basis_pca_var.empty:
        basis_proxy_wide = (
            factor_panel[factor_panel["country"] != "DE"]
            .pivot(index="date", columns="country", values="basis_proxy_spread_only")
            .sort_index()
        )
        basis_pca_pc1, basis_pca_var = _pca_from_wide(basis_proxy_wide, standardize=True)
        basis_pca_source = "spread_only_proxy"

    # C/F) Correlations and extension checks.
    analysis_df = factors.copy()
    if not basis_pca_pc1.empty:
        analysis_df = analysis_df.merge(basis_pca_pc1, on="date", how="left")
        analysis_df["basis_pca_source"] = basis_pca_source
    if not spread_pca_pc1.empty:
        analysis_df = analysis_df.merge(spread_pca_pc1.rename(columns={"PC1": "spread_PC1"}), on="date", how="left")

    corr_cols = [
        c
        for c in [
            "L_t_equal",
            "L_t_proxy_spread_only",
            "std_basis_t",
            "std_basis_proxy_t",
            "avg_spread_t",
            "PC1",
            "spread_PC1",
        ]
        if c in analysis_df.columns
    ]
    corr_table = analysis_df[corr_cols].corr() if corr_cols else pd.DataFrame()

    # D/F) Simple regressions (lightweight and interpretable).
    reg_frames = []
    if {"std_basis_t", "L_t_equal"}.issubset(analysis_df.columns):
        reg_frames.append(_run_ols(analysis_df, "std_basis_t", ["L_t_equal"]))
    if {"std_basis_proxy_t", "L_t_proxy_spread_only"}.issubset(analysis_df.columns):
        reg_frames.append(_run_ols(analysis_df, "std_basis_proxy_t", ["L_t_proxy_spread_only"]))
    if {"avg_spread_t", "L_t_equal", "std_basis_t"}.issubset(analysis_df.columns):
        reg_frames.append(_run_ols(analysis_df, "avg_spread_t", ["L_t_equal", "std_basis_t"]))
    if {"avg_spread_t", "L_t_proxy_spread_only", "std_basis_proxy_t"}.issubset(analysis_df.columns):
        reg_frames.append(_run_ols(analysis_df, "avg_spread_t", ["L_t_proxy_spread_only", "std_basis_proxy_t"]))

    # Simple crisis dummy for 2010-2012 stress period.
    if not analysis_df.empty:
        analysis_df["crisis_dummy"] = (
            (pd.to_datetime(analysis_df["date"]) >= pd.Timestamp("2010-01-01"))
            & (pd.to_datetime(analysis_df["date"]) <= pd.Timestamp("2012-12-31"))
        ).astype(int)
        if {"L_t_equal", "std_basis_t", "crisis_dummy"}.issubset(analysis_df.columns):
            reg_frames.append(_run_ols(analysis_df, "crisis_dummy", ["L_t_equal", "std_basis_t"]))
        if {"L_t_proxy_spread_only", "std_basis_proxy_t", "crisis_dummy"}.issubset(analysis_df.columns):
            reg_frames.append(_run_ols(analysis_df, "crisis_dummy", ["L_t_proxy_spread_only", "std_basis_proxy_t"]))

    regressions = pd.concat(reg_frames, ignore_index=True) if reg_frames else pd.DataFrame()

    # Summary stats for key series.
    key_cols = [
        c
        for c in [
            "L_t_equal",
            "L_t_proxy_spread_only",
            "cds_pair_ratio",
            "std_basis_t",
            "std_basis_proxy_t",
            "mad_basis_t",
            "range_basis_t",
            "iqr_basis_t",
            "avg_spread_t",
        ]
        if c in analysis_df.columns
    ]
    summary = analysis_df[key_cols].describe().T if key_cols else pd.DataFrame()

    # Save tables.
    save_csv(spread_corr.reset_index(), tables_dir / "spread_correlation_matrix.csv", index=False)
    save_csv(spread_pca_var, tables_dir / "pca_spreads_explained_variance.csv", index=False)
    if not basis_pca_var.empty:
        basis_pca_var = basis_pca_var.copy()
        basis_pca_var["source"] = basis_pca_source
    else:
        basis_pca_var = pd.DataFrame(
            {"component": [], "explained_ratio": [], "source": []}
        )
    save_csv(basis_pca_var, tables_dir / "pca_basis_explained_variance.csv", index=False)
    save_csv(corr_table.reset_index(), tables_dir / "factor_correlations.csv", index=False)
    save_csv(summary.reset_index().rename(columns={"index": "series"}), tables_dir / "summary_statistics.csv", index=False)
    save_csv(regressions, tables_dir / "regression_results.csv", index=False)

    return {
        "analysis_df": analysis_df,
        "spread_corr": spread_corr,
        "spread_pca_var": spread_pca_var,
        "basis_pca_var": basis_pca_var,
        "corr_table": corr_table,
        "summary": summary,
        "regressions": regressions,
    }
