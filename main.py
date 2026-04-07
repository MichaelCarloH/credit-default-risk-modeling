from pathlib import Path

from src.analysis import run_analysis
from src.data_cleaning import run_data_cleaning
from src.data_download import download_data
from src.factors import run_factor_construction
from src.macromicro_import import import_macromicro_cds
from src.paper_graph_reconstruction import reconstruct_monthly_cds_from_anchors
from src.plots import generate_plots
from src.utils import ensure_dirs


LATEX_SUBSECTION = r"""
\subsection{A Cross-Country CDS-Adjusted Liquidity-Basis Factor}

As a lightweight robustness exercise inspired by Monfort and Renne (2014), we construct a cross-country factor from CDS-adjusted sovereign yields without estimating a full affine regime-switching model. Let $y_{i,t}$ denote the sovereign bond yield for country $i$ and $CDS_{i,t}$ its matched-maturity CDS spread. We define
\begin{equation}
\tilde r_{i,t}=y_{i,t}-CDS_{i,t}.
\end{equation}
In a frictionless and fully integrated setting, CDS adjustment should remove most default compensation and leave a common curve across sovereigns. In practice, however, $\tilde r_{i,t}$ remains heterogeneous because it still embeds CDS--bond basis effects, market liquidity premia, convenience yields, counterparty-risk concerns, and segmentation in investor demand.

Using Germany as benchmark, we define
\begin{equation}
basis_{i,t}=\tilde r_{i,t}-\tilde r_{DE,t},
\end{equation}
and aggregate across non-German issuers:
\begin{equation}
L_t=\sum_{i\neq DE} w_i\,basis_{i,t},
\end{equation}
with either equal or pre-specified weights. Economically, $L_t$ is not a pure liquidity measure; it is better interpreted as a liquidity-basis / fragmentation indicator that summarizes common deviations from integrated pricing.

This construction complements, rather than replaces, the KfW--Bund logic. The KfW--Bund spread is a German-specific liquidity proxy under an explicit guarantee structure, while $L_t$ uses cross-country CDS-adjusted residuals and is therefore sensitive to euro-area fragmentation beyond Germany-specific market depth. We further propose cross-sectional dispersion metrics of $basis_{i,t}$ (standard deviation, median absolute deviation, range, interquartile range). These metrics capture whether fragmentation is broad-based or concentrated in a subset of issuers. In particular, dispersion can increase even when the average factor $L_t$ is stable, indicating heterogeneous stress transmission.

Hence, the combined $(L_t,\mathrm{Dispersion}_t)$ system offers a tractable empirical extension for Master's-level research: it preserves the paper's core intuition that spreads are not pure default signals, while adding a transparent measure of cross-country fragmentation intensity. The main limitation is identification: residual wedges mix several non-default channels and should be interpreted as reduced-form evidence rather than a structural decomposition.
""".strip()


def main() -> None:
    project_dirs = ["data/raw", "data/processed", "output/figures", "output/tables"]
    ensure_dirs(project_dirs)

    # 1) Download / ingestion
    result = download_data()
    print(f"[download] Yields: {result.yields_path}")
    print(f"[download] CDS template: {result.cds_template_path}")
    print(f"[download] Graph anchor template: {result.cds_graph_anchor_template_path}")
    print(f"[download] Log: {result.log_path}")

    # 2) Optional MacroMicro CSV import (if user saved files under data/raw/macromicro/)
    mm = import_macromicro_cds()
    print(f"[macromicro] imported rows={len(mm)} non-null cds={mm['cds'].notna().sum() if not mm.empty else 0}")

    # 3) Optional paper-graph reconstruction (monthly interpolation from anchors)
    try:
        cds_proxy = reconstruct_monthly_cds_from_anchors()
        n_non_null = cds_proxy["cds"].notna().sum()
        print(f"[reconstruct] proxy rows={len(cds_proxy)}, non-null cds={n_non_null}")
    except Exception as exc:
        print(f"[reconstruct] skipped ({exc})")

    # 4) Cleaning
    panel, _, _ = run_data_cleaning()
    print(f"[cleaning] panel rows={len(panel)}")

    # 5) Factor construction
    factor_panel, factors = run_factor_construction(panel)
    print(f"[factors] factor rows={len(factors)}")

    # 6) Analysis
    analysis_outputs = run_analysis(factor_panel, factors)
    print("[analysis] tables saved to output/tables")

    # 7) Plots
    generate_plots(factor_panel, factors, analysis_outputs)
    print("[plots] figures saved to output/figures")

    # 8) LaTeX write-up output
    tex_path = Path("output/tables/latex_subsection_cross_country_factor.tex")
    tex_path.write_text(LATEX_SUBSECTION, encoding="utf-8")
    print(f"[writeup] LaTeX subsection saved: {tex_path}")
    print("\nIf CDS values are still blank, fill data/raw/cds_graph_anchor_points.csv or data/raw/cds_template.csv and rerun.")


if __name__ == "__main__":
    main()
