"""Spaghetti plot for the locked MR-ART measures.

One line per subject across still, mild, and moderate. The sample is the
16 subjects whose three scans all passed the checklist, the same trios
as the ICC. Raw thickness or volume is plotted, not percent change.

Output: tables/spaghetti.png
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icc import QC_XLSX, load_qc_status, passing_trios
from outlier_screen import MEASURES, MEASURE_ORDER, MEASURE_SHORT, load_wide

ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "tables" / "spaghetti.png"
CONDITIONS = ["still", "mild", "moderate"]
UNITS = {
    "mean_thickness_mm": "mm",
    "rmfg_mm": "mm",
    "stg_mm": "mm",
    "tpole_mm": "mm",
    "caudate_mm3": "mm³",
    "hippocampus_mm3": "mm³",
}


def plot_spaghetti(sample, out_path: Path) -> None:
    keys = []
    for short in MEASURE_ORDER:
        keys.append(next(k for k, v in MEASURE_SHORT.items() if v == short))

    fig, axes = plt.subplots(2, 3, figsize=(10.2, 6.4), constrained_layout=True)
    x = np.arange(len(CONDITIONS))
    subjects = sorted(sample["subject"].unique())

    for ax, key in zip(axes.ravel(), keys):
        wide = (
            sample.pivot(index="subject", columns="condition", values=key)
            .loc[subjects, CONDITIONS]
        )
        for subject in subjects:
            ax.plot(
                x,
                wide.loc[subject].to_numpy(),
                color="#4c78a8",
                alpha=0.45,
                linewidth=1,
                zorder=2,
            )
        mean = wide.mean(axis=0).to_numpy()
        ax.plot(x, mean, color="black", linewidth=2.2, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(CONDITIONS)
        ax.set_title(MEASURES[key], fontsize=11)
        ax.set_ylabel(UNITS[key])

    n = len(subjects)
    fig.suptitle(
        f"QC-pass trios (n={n}). Blue lines are subjects; black is the mean.",
        fontsize=12,
    )
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"wrote {out_path} ({n} subjects)")


def main() -> None:
    wide = load_wide()
    qc = load_qc_status(QC_XLSX)
    plot_spaghetti(passing_trios(wide, qc), OUT_PNG)


if __name__ == "__main__":
    main()
