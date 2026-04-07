from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd
from pandas_datareader import data as web

from .paper_graph_reconstruction import create_graph_anchor_template
from .utils import TARGET_COUNTRIES, ensure_dirs, save_csv


FRED_10Y_SERIES = {
    "DE": ["IRLTLT01DEM156N"],
    "IT": ["IRLTLT01ITM156N"],
    "ES": ["IRLTLT01ESM156N"],
    "FR": ["IRLTLT01FRM156N"],
    "BE": ["IRLTLT01BEM156N"],
    "NL": ["IRLTLT01NLM156N"],
    "AT": ["IRLTLT01ATM156N"],
    "FI": ["IRLTLT01FIM156N"],
}


@dataclass
class DownloadResult:
    yields_path: Path
    cds_template_path: Path
    cds_graph_anchor_template_path: Path
    kfw_template_path: Path
    log_path: Path


def _fetch_fred_series(series_ids: List[str], start_date: str, end_date: str) -> pd.Series | None:
    """Try a list of FRED series IDs and return first successful series."""
    for sid in series_ids:
        try:
            s = web.DataReader(sid, "fred", start=start_date, end=end_date)[sid]
            s = s.dropna()
            if not s.empty:
                s.name = sid
                return s
        except Exception:
            continue
    return None


def _build_cds_template(dates: pd.Series, countries: List[str]) -> pd.DataFrame:
    """Create blank CDS template without inventing data."""
    date_df = pd.DataFrame({"date": sorted(pd.to_datetime(dates).dropna().unique())})
    date_df["tmp"] = 1
    countries_df = pd.DataFrame({"country": countries, "tmp": 1})
    template = date_df.merge(countries_df, on="tmp", how="inner").drop(columns=["tmp"])
    template["cds"] = pd.NA
    return template.sort_values(["date", "country"]).reset_index(drop=True)


def _ensure_template_exists(path: Path, df: pd.DataFrame) -> bool:
    """
    Create template only if it does not already exist.
    Returns True if created, False if preserved.
    """
    if path.exists():
        return False
    save_csv(df, path, index=False)
    return True


def download_data(
    start_date: str = "2005-01-01",
    end_date: str = "2025-12-31",
    raw_dir: str | Path = "data/raw",
) -> DownloadResult:
    """
    Download what is publicly and robustly available.

    Notes:
    - Sovereign yields are pulled from FRED/OECD long-term government yields.
    - Free, legally robust CDS bulk time series are typically unavailable.
      We therefore create a required local template CSV for manual CDS input.
    - KfW-Bund spread is also provided as a local template unless user supplies data.
    """
    raw_dir = Path(raw_dir)
    ensure_dirs([raw_dir])

    yield_rows = []
    log_rows: List[Dict[str, str]] = []

    for country in TARGET_COUNTRIES:
        series_ids = FRED_10Y_SERIES.get(country, [])
        series = _fetch_fred_series(series_ids, start_date, end_date)
        if series is None:
            log_rows.append(
                {
                    "dataset": "sovereign_yield",
                    "country": country,
                    "status": "missing",
                    "source": "FRED",
                    "details": f"No series found from candidates={series_ids}",
                }
            )
            continue

        tmp = series.reset_index()
        tmp.columns = ["date", "yield"]
        tmp["country"] = country
        tmp["source_series"] = series.name
        yield_rows.append(tmp)
        log_rows.append(
            {
                "dataset": "sovereign_yield",
                "country": country,
                "status": "downloaded",
                "source": "FRED",
                "details": f"series={series.name}",
            }
        )

    if yield_rows:
        yields = pd.concat(yield_rows, ignore_index=True)
        yields["maturity"] = "10Y_proxy"
        yields = yields.sort_values(["date", "country"])
    else:
        yields = pd.DataFrame(columns=["date", "country", "yield", "source_series", "maturity"])

    yields_path = raw_dir / "sovereign_yields_fred.csv"
    save_csv(yields, yields_path, index=False)

    # CDS template (required manual fill if no licensed free API is integrated).
    cds_template = _build_cds_template(yields["date"], TARGET_COUNTRIES)
    cds_template_path = raw_dir / "cds_template.csv"
    created_cds_template = _ensure_template_exists(cds_template_path, cds_template)

    cds_graph_anchor_template_path = raw_dir / "cds_graph_anchor_points.csv"
    if cds_graph_anchor_template_path.exists():
        created_anchor_template = False
    else:
        cds_graph_anchor_template_path = create_graph_anchor_template(yields, raw_dir=raw_dir)
        created_anchor_template = True

    log_rows.append(
        {
            "dataset": "cds",
            "country": "ALL",
            "status": "manual_required" if created_cds_template else "manual_required_preserved",
            "source": "template",
            "details": "Fill data/raw/cds_template.csv (date,country,cds). Existing file is preserved on rerun.",
        }
    )
    log_rows.append(
        {
            "dataset": "cds_graph_reconstruction",
            "country": "ALL",
            "status": "template_created" if created_anchor_template else "template_preserved",
            "source": "paper_figures",
            "details": "Optional: fill data/raw/cds_graph_anchor_points.csv with chart-digitized anchors; file is preserved on rerun.",
        }
    )

    # KfW-Bund proxy template.
    kfw_template = pd.DataFrame(
        {
            "date": sorted(pd.to_datetime(yields["date"]).dropna().unique()),
            "kfw_bund_spread": pd.NA,
        }
    )
    kfw_template_path = raw_dir / "kfw_bund_template.csv"
    created_kfw_template = _ensure_template_exists(kfw_template_path, kfw_template)
    log_rows.append(
        {
            "dataset": "kfw_bund",
            "country": "DE",
            "status": "manual_optional" if created_kfw_template else "manual_optional_preserved",
            "source": "template",
            "details": "Optional input: data/raw/kfw_bund_template.csv (preserved on rerun).",
        }
    )

    log_df = pd.DataFrame(log_rows)
    log_path = raw_dir / "download_log.csv"
    save_csv(log_df, log_path, index=False)

    return DownloadResult(
        yields_path=yields_path,
        cds_template_path=cds_template_path,
        cds_graph_anchor_template_path=cds_graph_anchor_template_path,
        kfw_template_path=kfw_template_path,
        log_path=log_path,
    )
