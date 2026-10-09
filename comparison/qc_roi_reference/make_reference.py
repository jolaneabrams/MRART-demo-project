#!/usr/bin/env python3
"""Marked reference images for the six locked QC regions.

The example is sub-016504 still, a scan where every consensus slice
actually contains the label. The index in each filename is the still-scan
index used in comparison/slices_mrart_*/.
"""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl-qc-roi")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SID = "mrart_sub-016504_acq-standard_T1w"

CORTEX = tuple(
    i
    for i in list(range(1001, 1036)) + list(range(2001, 2036))
    if i not in (1004, 2004)
)

# color, short slug, display name, (axial, coronal, sag L, sag R), label ids, note
ROIS = [
    (
        "#2F6FED",
        "mean-thickness",
        "Bilateral mean thickness",
        (110, 120, 170, 90),
        CORTEX,
        "The whole cortical ribbon. The medial wall is not included.",
    ),
    (
        "#C98400",
        "rostral-middle-frontal",
        "Rostral middle frontal",
        (80, 170, 160, 100),
        (1027, 2027),
        "Lateral frontal cortex, above the Sylvian fissure and behind the frontal pole.",
    ),
    (
        "#0E8A8A",
        "superior-temporal",
        "Superior temporal",
        (110, 120, 180, 80),
        (1030, 2030),
        "Lateral temporal gyrus along the Sylvian fissure.",
    ),
    (
        "#C43B78",
        "temporal-pole",
        "Temporal pole",
        (140, 150, 150, 100),
        (1033, 2033),
        "Anterior tip of the temporal lobe, beside the orbits. Not the cerebellum.",
    ),
    (
        "#E05A00",
        "caudate",
        "Caudate",
        (100, 140, 140, 110),
        (11, 50),
        "Gray bulge in the lateral wall of the frontal horn. Not drawn on the slice screenshots.",
    ),
    (
        "#3E8E2F",
        "hippocampus",
        "Hippocampus",
        (130, 120, 150, 100),
        (17, 53),
        "Medial temporal gray under the choroid fissure, behind the temporal pole.",
    ),
]


def load():
    base = ROOT / "fs_subjects" / SID / "mri"
    t1 = np.asanyarray(nib.load(base / "T1.mgz").dataobj).astype(np.float32)
    lab = np.asanyarray(nib.load(base / "aparc+aseg.mgz").dataobj)
    pos = t1[t1 > 0]
    lo, hi = np.percentile(pos, (1, 99.2))
    return t1, lab, float(lo), float(hi)


def plane(vol, kind, index):
    """Return a 2D view matching the FreeView screenshots.

    Axial: anterior at top, patient right on the left of the image.
    Coronal: superior at top, patient right on the left of the image.
    Sagittal: superior at top, anterior on the right of the image.
    """
    if kind == "axial":
        sl = vol[:, index, :]
        return sl.T[::-1, :]
    if kind == "coronal":
        sl = vol[:, :, index]
        return sl.T
    if kind == "sagittal":
        return vol[index, :, :]
    raise ValueError(kind)


def crop(img, mask, pad=14):
    brain = img > 10
    ys, xs = np.where(brain | mask)
    if len(ys) == 0:
        return img, mask
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(img.shape[0], int(ys.max()) + pad + 1)
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(img.shape[1], int(xs.max()) + pad + 1)
    return img[y0:y1, x0:x1], mask[y0:y1, x0:x1]


def draw(ax, img, mask, color, title, kind):
    view, marked = crop(img, mask)
    ax.imshow(view, cmap="gray", vmin=LO, vmax=HI, interpolation="nearest")
    if marked.any():
        overlay = np.zeros((*marked.shape, 4))
        rgb = tuple(int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
        overlay[marked] = (*rgb, 0.50)
        ax.imshow(overlay, interpolation="nearest")
        ax.contour(
            marked.astype(float),
            levels=[0.5],
            colors=[color],
            linewidths=1.1,
        )
    ax.set_title(title, loc="left", fontsize=11, color="#1c1c1c", pad=6)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#d0d0d0")
    marks = {
        "axial": (("R", 0.04, 0.50, "left", "center"), ("L", 0.96, 0.50, "right", "center"),
                  ("A", 0.50, 0.96, "center", "top"), ("P", 0.50, 0.05, "center", "bottom")),
        "coronal": (("R", 0.04, 0.50, "left", "center"), ("L", 0.96, 0.50, "right", "center"),
                    ("S", 0.50, 0.96, "center", "top"), ("I", 0.50, 0.05, "center", "bottom")),
        "sagittal": (("P", 0.04, 0.50, "left", "center"), ("A", 0.96, 0.50, "right", "center"),
                     ("S", 0.50, 0.96, "center", "top"), ("I", 0.50, 0.08, "center", "bottom")),
    }[kind]
    for text, x, y, ha, va in marks:
        ax.text(
            x, y, text, transform=ax.transAxes, color="white", fontsize=8,
            ha=ha, va=va, clip_on=False,
            bbox={"boxstyle": "round,pad=0.12", "fc": "black", "ec": "none", "alpha": 0.55},
        )


def main():
    global LO, HI
    t1, lab, LO, HI = load()
    saved = []
    for color, slug, name, indices, ids, note in ROIS:
        mask3 = np.isin(lab, ids)
        axial_i, coronal_i, sag_l, sag_r = indices
        panels = [
            ("axial", axial_i, f"Axial {axial_i}", f"{slug}-axial.png"),
            ("coronal", coronal_i, f"Coronal {coronal_i}", f"{slug}-coronal.png"),
            ("sagittal", sag_l, f"Left sagittal {sag_l}", f"{slug}-sagittal-left.png"),
            ("sagittal", sag_r, f"Right sagittal {sag_r}", f"{slug}-sagittal-right.png"),
        ]
        for kind, index, title, filename in panels:
            img = plane(t1, kind, index)
            marked = plane(mask3, kind, index)
            n = int(marked.sum())
            if n == 0:
                raise SystemExit(f"{name} {title} has no labeled voxels")
            fig, ax = plt.subplots(figsize=(4.4, 4.6), dpi=140)
            fig.patch.set_facecolor("white")
            draw(ax, img, marked, color, f"{name}\n{title}", kind)
            fig.tight_layout()
            path = OUT / filename
            fig.savefig(path, dpi=140, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            saved.append((slug, name, color, note, title, filename, n, kind, index))
            print(f"{filename:42} {n:5d} voxels")
    print(f"wrote {len(saved)} images")


if __name__ == "__main__":
    main()
