# Euro-Area Sovereign Spread Decomposition (Lightweight Pipeline)

This project implements a reproducible empirical pipeline inspired by Monfort and Renne (2014), focused on:

- sovereign spread co-movement
- CDS-adjusted residual basis vs Germany
- an aggregate cross-country fragmentation factor (`L_t`)
- dispersion metrics as an extension

It is intentionally lightweight (Master's-report scope), not a full affine regime-switching replication.

## Project Goal

Approximate the paper's core stylized facts with robust public data and transparent substitutions:

1. Download sovereign yields automatically where possible
2. Build clean aligned panel data (`date,country,yield,cds`)
3. Construct spread, CDS-adjusted basis, average factor, and dispersion metrics
4. Run PCA/correlations/simple regressions
5. Export publication-ready figures, tables, and a LaTeX subsection

## Data Sources and Substitutions

- **Sovereign yields**: downloaded from FRED/OECD long-term government yield series (10Y proxy).
- **CDS spreads**: not auto-downloaded from a robust free bulk source in this pipeline.
  - The code creates `data/raw/cds_template.csv` and expects manual input.
  - No CDS data are fabricated.
- **MacroMicro import path (recommended practical workaround)**:
  - Download country CSVs from MacroMicro series pages and place them in `data/raw/macromicro/`.
  - Include country names in filenames (e.g., `italy_5y_cds.csv`, `germany_5y_cds.csv`).
  - The pipeline auto-builds `data/raw/cds_from_macromicro.csv` and uses it as CDS input.
- **Academic-graph reconstruction path** (optional):
  - The code creates `data/raw/cds_graph_anchor_points.csv`.
  - You can digitize points from published figures (e.g., WebPlotDigitizer), paste anchors,
    and the pipeline interpolates a monthly proxy to `data/raw/cds_from_paper_graphs_monthly.csv`.
  - This is an approximation for robustness checks, not a substitute for original vendor CDS data.
- **KfW-Bund spread**: optional template created at `data/raw/kfw_bund_template.csv`.

See `data/raw/download_log.csv` after running for exact status per dataset/country.

## Installation

Using pip:

```bash
pip install -r requirements.txt
```

Or with your existing `pyproject.toml` workflow:

```bash
uv sync
```

## Run

```bash
python main.py
```

If using MacroMicro CSVs, create this folder first and drop files in it:

```bash
mkdir -p data/raw/macromicro
```

Pipeline order:
1. download / ingest
2. optional graph-based CDS reconstruction
3. clean data
4. construct factors
5. run analysis
6. generate plots
7. write LaTeX subsection

## Folder Structure

- `data/raw/`: downloaded files and templates
- `data/processed/`: cleaned panel and factor outputs
- `output/figures/`: charts
- `output/tables/`: summary tables, regression results, LaTeX subsection
- `src/`: modular pipeline code

## Economic Interpretation and Cautions

- `r_tilde = yield - cds` is **not** a pure risk-free rate.
- `basis = r_tilde_i - r_tilde_DE` mixes liquidity-basis, segmentation, and other residual premia.
- `L_t` is a **liquidity-basis / fragmentation factor**, not pure liquidity.
- Dispersion metrics are exploratory reduced-form diagnostics, not structural identification.
