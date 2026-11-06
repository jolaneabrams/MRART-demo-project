"""ICC(3,1) for the locked MR-ART thickness protocol.

One coefficient per locked measure, on subjects with a passing still,
mild, and moderate scan. Checklist fails and the missing mild scan
for sub-105822 stay out. Raw thickness or volume is the rating.
Subjects are the targets. The three motion conditions are the fixed
raters.

Pingouin 0.6.1 labels this coefficient ICC(C,1). That row is McGraw
and Wong's ICC(3,1): consistency, single measurement,
(MS_subjects - MS_error) / (MS_subjects + (k - 1) * MS_error).

Outputs:
  - icc.csv      one row per measure, with the 95% interval
  - icc_bar.png  the same coefficients
"""

import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outlier_screen import MEASURES, MEASURE_ORDER, MEASURE_SHORT, load_wide

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
QC_XLSX = ROOT / "qc_reference" / "QC_checklist.xlsx"
OUT_CSV = TABLES / "icc.csv"
OUT_PNG = TABLES / "icc_bar.png"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ICC_ROW = "ICC(C,1)"


def load_qc_status(path: Path) -> pd.DataFrame:
    """Return scan_id and whether the checklist cell begins with Pass."""
    with zipfile.ZipFile(path) as workbook:
        shared = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        strings = [
            "".join(node.text or "" for node in item.findall(".//m:t", NS))
            for item in shared.findall("m:si", NS)
        ]
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

    records = []
    for row in sheet.findall("m:sheetData/m:row", NS):
        cells = {}
        for cell in row.findall("m:c", NS):
            column = "".join(ch for ch in cell.attrib.get("r", "") if ch.isalpha())
            value = cell.find("m:v", NS)
            if value is None or value.text is None:
                cells[column] = ""
            elif cell.attrib.get("t") == "s":
                cells[column] = strings[int(value.text)]
            else:
                cells[column] = value.text
        scan_id = cells.get("A", "")
        if not scan_id.startswith("mrart_"):
            continue
        status = cells.get("B", "").strip()
        records.append(
            {
                "scan_id": scan_id,
                "qc_status": status,
                "qc_pass": status.lower().startswith("pass"),
            }
        )
    return pd.DataFrame(records)


def passing_trios(wide: pd.DataFrame, qc: pd.DataFrame) -> pd.DataFrame:
    """Keep subjects whose still, mild, and moderate scans all passed."""
    merged = wide.merge(qc, on="scan_id", how="left")
    missing = merged.loc[merged["qc_pass"].isna(), "scan_id"]
    if not missing.empty:
        raise SystemExit(f"checklist has no row for: {missing.tolist()}")

    kept = []
    for subject, block in merged.groupby("subject"):
        conditions = set(block["condition"])
        if conditions == {"still", "mild", "moderate"} and bool(block["qc_pass"].all()):
            kept.append(subject)
    return merged[merged["subject"].isin(kept)].copy()


def icc_one(block: pd.DataFrame, measure_key: str) -> dict:
    """ICC(3,1) and its 95% interval for one measure."""
    long = block[["subject", "condition", measure_key]].rename(
        columns={measure_key: "rating"}
    )
    stats = pg.intraclass_corr(
        data=long, targets="subject", raters="condition", ratings="rating"
    )
    row = stats.loc[stats["Type"] == ICC_ROW].iloc[0]
    low, high = row["CI95"]
    return {
        "measure": MEASURES[measure_key],
        "measure_key": measure_key,
        "n_subjects": int(long["subject"].nunique()),
        "n_conditions": int(long["condition"].nunique()),
        "icc_3_1": round(float(row["ICC"]), 3),
        "ci95_low": round(float(low), 3),
        "ci95_high": round(float(high), 3),
        "F": round(float(row["F"]), 2),
        "df1": int(row["df1"]),
        "df2": int(row["df2"]),
        "pval": float(row["pval"]),
        "pingouin_type": ICC_ROW,
    }


def plot_icc(result: pd.DataFrame, out_path: Path) -> None:
    order = [MEASURE_SHORT[key] for key in MEASURES]
    short = result["measure_key"].map(MEASURE_SHORT)
    result = result.set_index(short).loc[order].reset_index(drop=True)
    y = np.arange(len(result))
    icc = result["icc_3_1"].to_numpy()
    low = result["ci95_low"].to_numpy()
    high = result["ci95_high"].to_numpy()

    fig, ax = plt.subplots(figsize=(7.2, 4.2), constrained_layout=True)
    ax.barh(y, icc, color="#4c78a8", height=0.62, zorder=2)
    ax.errorbar(
        icc,
        y,
        xerr=[icc - low, high - icc],
        fmt="none",
        ecolor="black",
        elinewidth=1,
        capsize=3,
        zorder=3,
    )
    ax.axvline(0, color="0.4", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(result["measure"])
    ax.set_xlabel("ICC(3,1)")
    ax.set_xlim(min(-0.05, float(low.min()) - 0.05), 1.02)
    ax.invert_yaxis()
    n = int(result["n_subjects"].iloc[0])
    ax.set_title(f"ICC(3,1) on QC-pass trios (n={n})")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> None:
    wide = load_wide()
    qc = load_qc_status(QC_XLSX)
    sample = passing_trios(wide, qc)
    subjects = sorted(sample["subject"].unique())
    excluded = sorted(set(wide["subject"]) - set(subjects))

    rows = [icc_one(sample, key) for key in MEASURES]
    result = pd.DataFrame(rows)
    key_order = {short: i for i, short in enumerate(MEASURE_ORDER)}
    result["_order"] = result["measure_key"].map(MEASURE_SHORT).map(key_order)
    result = result.sort_values("_order").drop(columns="_order")
    result.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(result)} measures, {len(subjects)} trios)")
    print("included:", ", ".join(subjects))
    print("excluded:", ", ".join(excluded))
    print(result[["measure", "icc_3_1", "ci95_low", "ci95_high", "pval"]].to_string(index=False))
    plot_icc(result, OUT_PNG)


if __name__ == "__main__":
    main()
