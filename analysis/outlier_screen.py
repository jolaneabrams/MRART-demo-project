"""Diagnostic outlier screen for the locked MR-ART thickness protocol.

Flags are a re-review list. They do not change inclusion.
Inclusion changes only when a scan fails the written surface/WM checklist
or recon-all did not finish.

Screen, applied separately to still->mild and still->moderate:
  Iglewicz-Hoaglin modified z, |0.6745 * (x - median) / MAD| > 3.5
  on within-subject percent change from the still scan.
Locked measures only: bilateral mean thickness, rostral middle frontal,
superior temporal, temporal pole, caudate (L+R), hippocampus (L+R).
Tukey 1.5xIQR and ENIGMA +/-2.698 SD are recorded alongside, not used as
a second exclusion rule.

Also produces:
  - outlier_screen.csv        long format (subject x condition x measure)
  - outlier_screen_pivot.csv  wide format (subject x condition)
  - outlier_screen_heatmap.png  modified z heatmap, one panel per condition
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
OUT_LONG = TABLES / "outlier_screen.csv"
OUT_PIVOT = TABLES / "outlier_screen_pivot.csv"
OUT_PNG = TABLES / "outlier_screen_heatmap.png"

MEASURES = {
    "mean_thickness_mm": "global mean thickness",
    "rmfg_mm": "rostral middle frontal",
    "stg_mm": "superior temporal",
    "tpole_mm": "temporal pole",
    "caudate_mm3": "caudate (L+R)",
    "hippocampus_mm3": "hippocampus (L+R)",
}

MEASURE_SHORT = {
    "mean_thickness_mm": "mean_thick",
    "rmfg_mm": "rmfg",
    "stg_mm": "stg",
    "tpole_mm": "tpole",
    "caudate_mm3": "caudate",
    "hippocampus_mm3": "hippocampus",
}
MEASURE_ORDER = ["mean_thick", "rmfg", "stg", "tpole", "caudate", "hippocampus"]
CONDITION_ORDER = ["mild", "moderate"]

COND = {"standard": "still", "headmotion1": "mild", "headmotion2": "moderate"}


# ---------------------------------------------------------------------------
# Long-format diagnostic screen
# ---------------------------------------------------------------------------

def parse_scan(scan_id: str) -> tuple[str, str]:
    subject = scan_id.split("_acq-")[0].replace("mrart_", "")
    acq = scan_id.split("_acq-")[1].replace("_T1w", "")
    return subject, COND[acq]


def modified_z(values: np.ndarray) -> np.ndarray:
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    if mad == 0:
        return np.zeros_like(values, dtype=float)
    return 0.6745 * (values - med) / mad


def load_wide() -> pd.DataFrame:
    lh = pd.read_csv(TABLES / "lh.aparc.thickness.csv")
    rh = pd.read_csv(TABLES / "rh.aparc.thickness.csv")
    aseg = pd.read_csv(TABLES / "aseg.volume.csv")
    lh_id, rh_id, aseg_id = lh.columns[0], rh.columns[0], aseg.columns[0]
    rh = rh.set_index(rh_id)
    aseg = aseg.set_index(aseg_id)
    rows = []
    for _, left in lh.iterrows():
        scan_id = left.iloc[0]
        subject, condition = parse_scan(scan_id)
        right = rh.loc[scan_id]
        vol = aseg.loc[scan_id]

        def bilateral(label: str) -> float:
            return 0.5 * (float(left[f"lh_{label}"]) + float(right[f"rh_{label}"]))

        rows.append(
            {
                "scan_id": scan_id,
                "subject": subject,
                "condition": condition,
                "mean_thickness_mm": bilateral("MeanThickness_thickness"),
                "rmfg_mm": bilateral("rostralmiddlefrontal_thickness"),
                "stg_mm": bilateral("superiortemporal_thickness"),
                "tpole_mm": bilateral("temporalpole_thickness"),
                "caudate_mm3": float(vol["Left-Caudate"]) + float(vol["Right-Caudate"]),
                "hippocampus_mm3": float(vol["Left-Hippocampus"])
                + float(vol["Right-Hippocampus"]),
            }
        )
    return pd.DataFrame(rows)


def build_long(wide: pd.DataFrame) -> pd.DataFrame:
    """Run the modified-z / Tukey / ENIGMA screen; return long-format rows."""
    still = wide[wide["condition"] == "still"].set_index("subject")

    records = []
    for condition in ("mild", "moderate"):
        block = wide[wide["condition"] == condition]
        paired = block[block["subject"].isin(still.index)].copy()
        for key in MEASURES:
            change = 100.0 * (
                paired[key].to_numpy()
                - still.loc[paired["subject"], key].to_numpy()
            ) / still.loc[paired["subject"], key].to_numpy()

            mz = modified_z(change)

            q1, q3 = np.percentile(change, [25, 75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr

            mu = float(np.mean(change))
            sd = float(np.std(change, ddof=1))

            for i, (_, row) in enumerate(paired.iterrows()):
                pct = float(change[i])
                enigma_z = (pct - mu) / sd if sd else 0.0
                records.append(
                    {
                        "subject": row["subject"],
                        "condition": condition,
                        "measure": MEASURES[key],
                        "measure_key": key,
                        "still_value": round(float(still.loc[row["subject"], key]), 3),
                        "motion_value": round(float(row[key]), 3),
                        "pct_change": round(pct, 2),
                        "modified_z": round(float(mz[i]), 2),
                        "robust_flag": bool(abs(mz[i]) > 3.5),
                        "tukey_flag": bool(pct < lo or pct > hi),
                        "enigma_flag": bool(abs(enigma_z) > 2.698),
                    }
                )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Pivot to subject x condition
# ---------------------------------------------------------------------------

def build_pivot(df: pd.DataFrame) -> pd.DataFrame:
    pct = df.pivot_table(
        index=["subject", "condition"],
        columns="measure_key",
        values="pct_change",
    ).rename(columns=MEASURE_SHORT)

    mz = df.pivot_table(
        index=["subject", "condition"],
        columns="measure_key",
        values="modified_z",
    ).rename(columns={k: f"{v}_z" for k, v in MEASURE_SHORT.items()})

    robust = df.pivot_table(
        index=["subject", "condition"],
        columns="measure_key",
        values="robust_flag",
    ).rename(columns={k: f"{v}_flag" for k, v in MEASURE_SHORT.items()})

    tukey = df.pivot_table(
        index=["subject", "condition"],
        columns="measure_key",
        values="tukey_flag",
    ).rename(columns={k: f"{v}_tukey" for k, v in MEASURE_SHORT.items()})

    enigma = df.pivot_table(
        index=["subject", "condition"],
        columns="measure_key",
        values="enigma_flag",
    ).rename(columns={k: f"{v}_enigma" for k, v in MEASURE_SHORT.items()})

    out = pd.concat([pct, mz, robust, tukey, enigma], axis=1).reset_index()

    flag_cols = [c for c in out.columns if c.endswith("_flag")]
    tukey_cols = [c for c in out.columns if c.endswith("_tukey")]
    enigma_cols = [c for c in out.columns if c.endswith("_enigma")]

    out["n_robust"] = out[flag_cols].sum(axis=1).astype(int)
    out["n_tukey"] = out[tukey_cols].sum(axis=1).astype(int)
    out["n_enigma"] = out[enigma_cols].sum(axis=1).astype(int)
    out["n_any_robust_or_tukey"] = (
        out[flag_cols + tukey_cols].any(axis=1).astype(int)
    )

    z_cols = [c for c in out.columns if c.endswith("_z")]
    out["max_abs_z"] = out[z_cols].abs().max(axis=1).round(2)
    out["worst_measure"] = (
        out[z_cols].abs().idxmax(axis=1).str.replace("_z", "", regex=False)
    )

    first = [
        "subject", "condition",
        "n_robust", "n_tukey", "n_enigma", "max_abs_z", "worst_measure",
    ]
    rest = [c for c in out.columns if c not in first]
    return out[first + rest].sort_values(
        ["condition", "n_robust", "max_abs_z"],
        ascending=[True, False, False],
    )


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

def plot_heatmap(df: pd.DataFrame, out_path: Path) -> None:
    conditions = [c for c in CONDITION_ORDER if c in df["condition"].unique()]
    n_cond = len(conditions)
    if n_cond == 0:
        print("no conditions to plot; skipping heatmap")
        return

    z_cols = [f"{m}_z" for m in MEASURE_ORDER]
    vmax = float(np.nanmax(np.abs(df[z_cols].to_numpy())))
    vmax = max(vmax, 3.5)

    fig, axes = plt.subplots(
        nrows=1, ncols=n_cond,
        figsize=(4.2 * n_cond + 1.5, 8.5),
        constrained_layout=True,
    )
    if n_cond == 1:
        axes = [axes]

    for ax, cond in zip(axes, conditions):
        sub = df[df["condition"] == cond].copy()
        sub = sub.sort_values("max_abs_z", ascending=False)
        mat = sub[z_cols].to_numpy(dtype=float)

        im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)

        ax.set_xticks(range(len(MEASURE_ORDER)))
        ax.set_xticklabels(MEASURE_ORDER, rotation=45, ha="right")
        ax.set_yticks(range(len(sub)))
        ax.set_yticklabels(sub["subject"], fontsize=8)
        ax.set_title(f"still \u2192 {cond}", fontsize=11)
        ax.set_xlabel("measure")

        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                val = mat[i, j]
                if np.isnan(val):
                    continue
                flagged = abs(val) > 3.5
                color = "white" if abs(val) > 0.6 * vmax else "black"
                label = f"{val:.1f}" + ("*" if flagged else "")
                ax.text(
                    j, i, label,
                    ha="center", va="center",
                    fontsize=7, color=color,
                    fontweight="bold" if flagged else "normal",
                )

        ax.set_xticks(np.arange(-0.5, len(MEASURE_ORDER), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(sub), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.5)
        ax.tick_params(which="minor", length=0)

    cbar = fig.colorbar(im, ax=axes, shrink=0.5, pad=0.02)
    cbar.set_label("modified z (pct change from still)")
    fig.suptitle(
        "Modified z of within-subject percent change; * = |z| > 3.5",
        fontsize=12,
    )

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    wide = load_wide()
    long = build_long(wide)
    long.to_csv(OUT_LONG, index=False)
    print(f"wrote {OUT_LONG} ({len(long)} rows)")

    pivot = build_pivot(long)
    pivot.to_csv(OUT_PIVOT, index=False)
    print(
        f"wrote {OUT_PIVOT} ({len(pivot)} rows: "
        f"{pivot['subject'].nunique()} subjects x "
        f"{pivot['condition'].nunique()} conditions)"
    )

    print("\n=== Re-review shortlist: subjects with >=1 robust flag ===")
    shortlist = pivot[pivot["n_robust"] > 0].copy()
    if shortlist.empty:
        print("(none)")
    else:
        cols = [
            "subject", "condition", "n_robust", "max_abs_z", "worst_measure",
        ]
        print(shortlist[cols].to_string(index=False))

    print("\n=== Secondary: Tukey-only flags (no robust flag) ===")
    tukey_only = pivot[(pivot["n_robust"] == 0) & (pivot["n_tukey"] > 0)].copy()
    if tukey_only.empty:
        print("(none)")
    else:
        cols = [
            "subject", "condition", "n_tukey", "max_abs_z", "worst_measure",
        ]
        print(
            tukey_only[cols]
            .sort_values("n_tukey", ascending=False)
            .to_string(index=False)
        )

    plot_heatmap(pivot, OUT_PNG)


if __name__ == "__main__":
    main()