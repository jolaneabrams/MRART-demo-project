"""Still-to-moderate drift and Wilcoxon tests for the locked protocol.

Primary sample: subjects whose still scan and moderate scan both passed
the checklist. sub-105822 stays in, because that moderate scan passed.
The three moderate fails stay out of the median and out of the test.

For each locked measure the drift is the within-subject percent change,
100 * (moderate - still) / still, summarized as the median and the
interquartile range. The paired test is a two-sided Wilcoxon signed-rank
test of the still value against the moderate value. Holm correction is
applied across the six pre-specified tests.

One sensitivity recomputes the median and interquartile range with the
checklist fails put back. Those scans still have aparc and aseg tables.
The Wilcoxon test is not repeated on that sample.

Outputs:
  - drift_wilcoxon.csv
  - drift_boxplot.png   percent change on the QC-pass pairs
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icc import QC_XLSX, load_qc_status
from outlier_screen import MEASURES, MEASURE_ORDER, MEASURE_SHORT, load_wide

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
OUT_CSV = TABLES / "drift_wilcoxon.csv"
OUT_PNG = TABLES / "drift_boxplot.png"


def still_moderate(wide: pd.DataFrame, qc: pd.DataFrame, require_pass: bool) -> pd.DataFrame:
    """One row per subject with both a still scan and a moderate scan."""
    merged = wide.merge(qc, on="scan_id", how="left")
    if merged["qc_pass"].isna().any():
        missing = merged.loc[merged["qc_pass"].isna(), "scan_id"].tolist()
        raise SystemExit(f"checklist has no row for: {missing}")

    still = merged[merged["condition"] == "still"].set_index("subject")
    moderate = merged[merged["condition"] == "moderate"].set_index("subject")
    common = still.index.intersection(moderate.index)

    rows = []
    for subject in common:
        still_pass = bool(still.at[subject, "qc_pass"])
        moderate_pass = bool(moderate.at[subject, "qc_pass"])
        if require_pass and not (still_pass and moderate_pass):
            continue
        record = {
            "subject": subject,
            "still_pass": still_pass,
            "moderate_pass": moderate_pass,
        }
        for key in MEASURES:
            record[f"still_{key}"] = float(still.at[subject, key])
            record[f"moderate_{key}"] = float(moderate.at[subject, key])
        rows.append(record)
    return pd.DataFrame(rows)


def percent_change(pairs: pd.DataFrame, key: str) -> np.ndarray:
    still = pairs[f"still_{key}"].to_numpy()
    moderate = pairs[f"moderate_{key}"].to_numpy()
    return 100.0 * (moderate - still) / still


def summarize(pairs: pd.DataFrame) -> pd.DataFrame:
    """Median drift, Wilcoxon, then Holm across the six tests."""
    rows = []
    for key in MEASURES:
        change = percent_change(pairs, key)
        q1, median, q3 = np.percentile(change, [25, 50, 75])
        test = pg.wilcoxon(
            pairs[f"still_{key}"],
            pairs[f"moderate_{key}"],
            alternative="two-sided",
        ).iloc[0]
        rows.append(
            {
                "measure": MEASURES[key],
                "measure_key": key,
                "n_pairs": int(len(pairs)),
                "median_pct": round(float(median), 2),
                "q1_pct": round(float(q1), 2),
                "q3_pct": round(float(q3), 2),
                "n_thinner_or_smaller": int(np.sum(change < 0)),
                "n_thicker_or_larger": int(np.sum(change > 0)),
                "W": float(test["W_val"]),
                "p_raw": float(test["p_val"]),
            }
        )
    result = pd.DataFrame(rows)
    _, p_holm = pg.multicomp(result["p_raw"], method="holm")
    result["p_holm"] = p_holm
    result["holm_reject_0.05"] = result["p_holm"] < 0.05
    return result


def add_sensitivity(result: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    """Median and IQR with checklist fails included. No second Wilcoxon."""
    extra = []
    for key in MEASURES:
        change = percent_change(pairs, key)
        q1, median, q3 = np.percentile(change, [25, 50, 75])
        extra.append(
            {
                "measure_key": key,
                "n_pairs_incl_fail": int(len(pairs)),
                "median_pct_incl_fail": round(float(median), 2),
                "q1_pct_incl_fail": round(float(q1), 2),
                "q3_pct_incl_fail": round(float(q3), 2),
            }
        )
    return result.merge(pd.DataFrame(extra), on="measure_key", how="left")


def plot_drift(pairs: pd.DataFrame, out_path: Path) -> None:
    labels = []
    series = []
    for short in MEASURE_ORDER:
        key = next(k for k, v in MEASURE_SHORT.items() if v == short)
        labels.append(MEASURES[key])
        series.append(percent_change(pairs, key))

    fig, ax = plt.subplots(figsize=(8.2, 4.6), constrained_layout=True)
    positions = np.arange(1, len(series) + 1)
    ax.boxplot(
        series,
        positions=positions,
        widths=0.55,
        patch_artist=True,
        medianprops={"color": "black", "linewidth": 1.4},
        boxprops={"facecolor": "#4c78a8", "edgecolor": "black"},
        whiskerprops={"color": "black"},
        capprops={"color": "black"},
        flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "0.3"},
    )
    rng = np.random.default_rng(0)
    for position, values in zip(positions, series):
        jitter = rng.uniform(-0.12, 0.12, size=len(values))
        ax.scatter(
            np.full(len(values), position) + jitter,
            values,
            s=16,
            color="black",
            alpha=0.55,
            zorder=3,
        )
    ax.axhline(0, color="0.4", linewidth=0.8)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("percent change, still to moderate")
    n = len(pairs)
    ax.set_title(f"Still to moderate, QC-pass pairs (n={n})")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> None:
    wide = load_wide()
    qc = load_qc_status(QC_XLSX)
    primary = still_moderate(wide, qc, require_pass=True)
    sensitivity = still_moderate(wide, qc, require_pass=False)

    result = add_sensitivity(summarize(primary), sensitivity)
    key_order = {short: i for i, short in enumerate(MEASURE_ORDER)}
    result["_order"] = result["measure_key"].map(MEASURE_SHORT).map(key_order)
    result = result.sort_values("_order").drop(columns="_order")
    result.to_csv(OUT_CSV, index=False)

    excluded = sorted(set(sensitivity["subject"]) - set(primary["subject"]))
    print(f"wrote {OUT_CSV} ({len(result)} measures, {len(primary)} QC-pass pairs)")
    print("included:", ", ".join(sorted(primary["subject"])))
    print("sensitivity only:", ", ".join(excluded))
    cols = [
        "measure",
        "median_pct",
        "q1_pct",
        "q3_pct",
        "p_raw",
        "p_holm",
        "median_pct_incl_fail",
    ]
    print(result[cols].to_string(index=False))
    plot_drift(primary, OUT_PNG)


if __name__ == "__main__":
    main()
