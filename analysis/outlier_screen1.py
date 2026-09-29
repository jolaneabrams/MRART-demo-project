"""Diagnostic outlier screen for the locked MR-ART thickness protocol.

Flags are a re-review list. They do not change inclusion.
Inclusion changes only when a scan fails the written surface/WM checklist
or recon-all did not finish.

Screen, applied separately to still→mild and still→moderate:
  Iglewicz–Hoaglin modified z, |0.6745 * (x - median) / MAD| > 3.5
  on within-subject percent change from the still scan.
Locked measures only: bilateral mean thickness, rostral middle frontal,
superior temporal, temporal pole, caudate (L+R), hippocampus (L+R).
Tukey 1.5×IQR and ENIGMA ±2.698 SD are recorded alongside, not used as
a second exclusion rule.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
OUT = TABLES / "outlier_screen.csv"

MEASURES = {
    "mean_thickness_mm": "global mean thickness",
    "rmfg_mm": "rostral middle frontal",
    "stg_mm": "superior temporal",
    "tpole_mm": "temporal pole",
    "caudate_mm3": "caudate (L+R)",
    "hippocampus_mm3": "hippocampus (L+R)",
}

COND = {"standard": "still", "headmotion1": "mild", "headmotion2": "moderate"}


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
                "surface_holes": float(vol["SurfaceHoles"]),
                "cortex_vol_mm3": float(vol["CortexVol"]),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    wide = load_wide()
    still = wide[wide["condition"] == "still"].set_index("subject")
    records = []
    for condition in ("mild", "moderate"):
        block = wide[wide["condition"] == condition]
        paired = block[block["subject"].isin(still.index)].copy()
        for key in MEASURES:
            change = 100.0 * (paired[key].to_numpy() - still.loc[paired["subject"], key].to_numpy()) / still.loc[
                paired["subject"], key
            ].to_numpy()
            mz = modified_z(change)
            q1, q3 = np.percentile(change, [25, 75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mu = float(np.mean(change))
            sd = float(np.std(change, ddof=1))
            for i, (_, row) in enumerate(paired.iterrows()):
                pct = float(change[i])
                enigma_z = (pct - mu) / sd if sd else 0.0
                robust = abs(mz[i]) > 3.5
                tukey = pct < lo or pct > hi
                enigma = abs(enigma_z) > 2.698
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
                        "robust_flag": robust,
                        "tukey_flag": tukey,
                        "enigma_flag": enigma,
                        "surface_holes_motion": row["surface_holes"],
                    }
                )
    out = pd.DataFrame(records)
    out.to_csv(OUT, index=False)
    flagged = out[out["robust_flag"]]
    print(f"wrote {OUT} ({len(out)} rows)")
    print(f"robust flags: {len(flagged)}")
    if len(flagged):
        print(
            flagged[
                ["subject", "condition", "measure", "pct_change", "modified_z"]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
