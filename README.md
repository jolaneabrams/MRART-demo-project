# MRART_Demo_Project

FreeSurfer recon-all on 20 subjects × 3 motion conditions from the MR-ART dataset (ds004173), quantifying how cortical thickness estimates drift under increasing head motion. This is a partial replication of Reuter et al. (2015; doi: [10.1016/j.neuroimage.2014.12.006](https://doi.org/10.1016/j.neuroimage.2014.12.006)). Intended as a pipeline-competence artifact rather than a novel publication.

**Author:** Jolane Abrams  
**Contact:** [jkabrams@alumni.usc.edu](mailto:jkabrams@alumni.usc.edu) | /Users/jolaneabrams/Desktop/GitHub/MRART_Demo_Project | [https://www.linkedin.com/in/jolane-abrams-309b3412/](https://www.linkedin.com/in/jolane-abrams-309b3412/)

---

## Abstract

Head motion degrades structural MRI morphometry, but the magnitude of that degradation is rarely shown end-to-end with a public dataset. This project runs FreeSurfer recon-all on 20 subjects × 3 motion conditions from the MR-ART dataset (ds004173) and quantifies how cortical thickness estimates drift under increasing head motion, attempting to reproduce the directional finding in Reuter et al. (2015): head motion during acquisition reduces gray-matter volume and thickness estimates, and that bias remains after scans that fail quality control are excluded.

---

## Replication context

This project is a partial replication of:

Reuter M, Tisdall MD, Qureshi A, Buckner RL, van der Kouwe AJW, Fischl B. Head motion during MRI acquisition reduces gray matter volume and thickness estimates. *NeuroImage*. 2015;107:107-115. doi:[10.1016/j.neuroimage.2014.12.006](https://doi.org/10.1016/j.neuroimage.2014.12.006)

### Original study

Reuter et al. scanned 12 healthy volunteers within a single session under different motion conditions (still, nod, shake, free motion). Using FreeSurfer 5.3, VBM8 SPM, and FSL Siena 5.0.7, they found an average apparent volume loss of roughly 0.7%/mm/min of subject motion, with effects varying across regions. Critically, the bias remained significant after excluding scans that failed a rigorous quality check — motion bias is directional, not just added noise.

### This project

- Dataset: MR-ART (OpenNeuro ds004173), 20 subjects × 3 motion conditions (still, mild, moderate)
- Software: FreeSurfer 8.2.0 (vs. 5.3 in the original)
- Estimand: within-subject percent change from the still scan
- QC: pre-specified outlier screen (Iglewicz–Hoaglin modified z on percent change) plus a written surface/WM/topology checklist
- Separation of flags (re-review) from fails (checklist-based exclusion), motivated by the original finding that bias survives QC exclusion

### What's different

- Larger sample (20 vs. 12)
- Condition labels rather than mm/min motion quantification — effect sizes are not directly comparable
- FreeSurfer-only (original tested three pipelines)
- Pre-specified measures (six locked ROIs) rather than whole-brain morphometry
- Explicit flag-vs-exclusion documentation

### What replicates

- Direction of effect: motion → thinner cortex, smaller volumes
- Regional variation: temporal pole shows the largest drift in this sample (−20.9% median under moderate motion), consistent with regional specificity in the original
- QC exclusion does not eliminate the bias

---

## Data

**Dataset:** MR-ART (Movement-Related ARTefacts)  
**Repository:** [OpenNeuro ds004173](https://openneuro.org/datasets/ds004173)  
**DOI:** [Insert DOI once verified]

The MR-ART dataset contains T1-weighted 3D structural MRI images of 148 healthy adults, each scanned three times under increasing head motion (still, mild, moderate). All scans are anonymized, BIDS-organized, and defaced.

**Subset used:** First 20 subjects, **59 T1 scans** (not 60). `sub-105822` has no `acq-headmotion1` (mild) scan. Subject labels are non-sequential 6-digit IDs (e.g., `sub-000103`).

### Download command

```bash
source ~/venvs/neuro/bin/activate
openneuro-py download --dataset ds004173 --include sub-000103  # repeat for each of 20 subjects
```

## Pipeline overview

[BLOCK FOR PIPELINE FLOWCHART IMAGE]

Insert flowchart image here after batch begins running:

- Input: BIDS-formatted T1 scans (`sub-*/anat/*_T1w.nii.gz`)
- Processing: FreeSurfer `recon-all -all` (v8.2.0)
- Output: Per-subject `aparc.stats` / `aseg.stats` tables
- Aggregation: Python extraction to tidy CSV
- Analysis: Drift metrics (percent change), reliability (ICC)

## Environment

### Software versions

| Component | Version | Installation |
| --- | --- | --- |
| macOS | 26.6.2 | |
| Python | 3.12.2 | Homebrew / python.org |
| FreeSurfer | 8.2.0 | freesurfer.net |
| XQuartz | 2.8.6 | xquartz.org |
| openneuro-py | 2026.7.1 | |
| pandas | 3.0.5 | |
| matplotlib | 3.11.1 | |
| seaborn | 0.13.2 | |
| pingouin | 0.6.1 | |
| nibabel | 5.4.2 | |

### Virtual environment setup

```bash
python3 -m venv ~/venvs/neuro
source ~/venvs/neuro/bin/activate
python3 -m pip install openneuro-py pandas matplotlib seaborn pingouin nibabel
```

### Environment variables

```bash
export SUBJECTS_DIR=$HOME/mrart_demo/fs_subjects
export FREESURFER_HOME=/usr/local/freesurfer/8.2.0  # Adjust to your install
source $FREESURFER_HOME/SetUpFreeSurfer.sh
```

### Directory structure

```text
~/mrart_demo/
├── ds004173/                 # Raw BIDS data (downloaded)
│   ├── sub-000103/
│   │   └── anat/
│   │       ├── *_acq-standard_T1w.nii.gz
│   │       ├── *_acq-headmotion1_T1w.nii.gz
│   │       └── *_acq-headmotion2_T1w.nii.gz
│   ├── sub-000148/
│   └── ... (19 more subjects)
├── fs_subjects/              # FreeSurfer outputs
│   ├── mrart_sub-000103_acq-standard/
│   ├── mrart_sub-000103_acq-headmotion1/
│   └── ... (57 more subjects)
├── logs/                     # Per-subject recon-all logs
├── run_reconall.sh           # Batch script
├── README.md                 # This file
└── .gitignore
```

## Quality control

Inclusion changes only when a scan fails the written checklist below, or when `recon-all` did not finish. The quantitative outlier screen is a re-review list. It does not fail a scan.

The screen is `analysis/outlier_screen.py`. It is applied separately to still→mild and still→moderate percent change, `100 × (motion − still) / still`, on six locked measures: bilateral mean thickness, rostral middle frontal, superior temporal, temporal pole, caudate (L+R), and hippocampus (L+R). A robust flag is an Iglewicz–Hoaglin modified z above 3.5 (`0.6745 × (x − median) / MAD`), with the median and MAD taken inside that measure and that contrast. Tukey 1.5×IQR and an ENIGMA-style z (±2.698) are stored alongside and are not a second exclusion rule. Outputs: `tables/outlier_screen.csv`, `tables/outlier_screen_pivot.csv`, and `tables/outlier_screen_heatmap.png`.

Pass/fail calls from FreeView are recorded in `analysis/QC_checklist.xlsx`. The written criteria are in `analysis/FreeSurfer_QC_checklist.docx` and below.

### Surface QC checklist

**Purpose:** Pass/fail criteria applied during visual inspection of FreeSurfer recon-all outputs in FreeView. A scan fails only when one or more criteria below are met.

**Scope:** White surface, pial surface, white-matter boundaries, topology. Applied to all scans in the analysis set.

**Reviewer:** Jolane Abrams  
**Date:** 21–29 September 2026  
**FreeSurfer version:** 8.2.0  
**Viewer:** FreeView (XQuartz 2.8.6)

#### Procedure

For each scan, load recon-all outputs in FreeView and inspect:

- `orig` volume with white and pial surfaces overlaid
- `wm` (white-matter mask) against `orig`
- `aparc` and `aparc+aseg` segmentations
- Surface topology (holes, handles, non-manifold edges)

Inspect in coronal, sagittal, and axial planes. Pan through the full volume rather than sampling slices.

#### Pass criteria

A scan passes when all of the following hold.

**White surface**

- White surface follows the gray/white boundary in all lobes
- No regions where the white surface intrudes into gray matter or CSF
- No regions where the white surface excludes visible white matter
- Medial wall and midline structures correctly excluded

**Pial surface**

- Pial surface follows the outer gray matter boundary (CSF/gray interface)
- No regions where the pial surface extends into the skull, dura, or venous sinuses
- No regions where the pial surface collapses into white matter
- No large regions of over- or under-estimated cortical thickness

**White-matter boundaries**

- `wm` mask captures white matter without including gray matter or CSF
- Subcortical structures (caudate, putamen, thalamus, hippocampus, amygdala, ventricles) correctly segmented in `aseg`
- No obvious mislabeling at boundaries (for example hippocampus/amygdala confusion, or ventricle/white-matter confusion)

**Topology**

- No surface holes (defects) beyond incidental
- No handles or non-manifold edges
- `recon-all.done` marker present

#### Fail criteria

A scan fails when any of the following hold:

- `recon-all.done` marker absent (pipeline did not complete)
- White surface misalignment visible and not attributable to a known anatomical variant
- Pial surface extends outside the brain (into skull, dura, or sinus)
- `wm` mask includes non-white-matter tissue in a region that affects a pre-specified ROI
- Subcortical segmentation error in a region that affects a pre-specified ROI
- Topology defect (hole, handle) that affects a pre-specified ROI

A scan is not failed for minor surface imperfections that do not affect pre-specified ROIs. Surface reconstruction is imperfect in all scans; the question is whether the imperfection biases the measures being analyzed.

#### Pre-specified ROIs (for fail decisions)

A segmentation or topology error triggers a fail only when it affects one or more of:

- Bilateral mean thickness
- Rostral middle frontal thickness
- Superior temporal thickness
- Temporal pole thickness
- Caudate volume (L+R)
- Hippocampus volume (L+R)

Errors outside these regions are noted but do not change inclusion.

#### Flag vs. fail

A flag from the quantitative outlier screen sends a scan to re-review. It does not fail the scan. A fail requires one or more of the criteria above. The decision rests on the checklist, not on the size of the percent change.

This separation is deliberate: scans can have large percent changes for real biological reasons, or because the still scan was unusual, and scans can have small percent changes despite a segmentation error. The checklist is the inclusion rule; the screen is a triage tool.

### Failure log

Per-subject logs are stored in `logs/`. Batch-generated failure list: `logs/failed_subjects.txt` (empty if all succeed).

## Status

- Environment configured (XQuartz, FreeSurfer 8.2.0, Python venv)
- 20 subjects downloaded (59 T1 scans; no mild scan for `sub-105822`)
- Subject ID schema verified (6-digit non-sequential)
- `recon-all -all` finished on all 59 scans (FreeSurfer 8.2.0, `MAX_PAR=1`)
- Mean scan time 1.7 h (range 83–134 min); batch wall clock 90 h for 55 scans (17–21 Sep 2026)
- Thickness and volume tables extracted: `tables/lh.aparc.thickness.csv`, `tables/rh.aparc.thickness.csv`, `tables/aseg.volume.csv`
- Outlier screen run (234 rows: 6 measures × 19 mild pairs + 6 × 20 moderate pairs)
- Surface QC checklist written (21–29 Sep 2026); FreeView pass/fail calls go in `analysis/QC_checklist.xlsx`
- Raw data: `ds004173/` (local, not in git)
- Outputs: `fs_subjects/` (local, ~25 GB, not in git)
- Success list: `logs/succeeded_subjects.txt`

## Next steps

- Finish visual QC of white/pial surfaces in FreeView and record each call in `analysis/QC_checklist.xlsx`
- Calculate ICC(3,1) reliability per region
- Generate figures (box plots, spaghetti plot, ICC bar chart)

## Limitations

Demo-scale sample (~20 subjects); not powered for statistical inference. Single dataset, single scanner vendor. Condition labels rather than mm/min motion, so effect sizes are not directly comparable to Reuter et al. (2015). Intended as a pipeline-competence artifact rather than a novel publication.

## Contact

Jolane Abrams — jkabrams@alumni.usc.edu  
Open to collaboration on imaging QC / PTSD morphometry / ENIGMA working groups.

## References

- Reuter M, Tisdall MD, Qureshi A, Buckner RL, van der Kouwe AJW, Fischl B. Head motion during MRI acquisition reduces gray matter volume and thickness estimates. *NeuroImage*. 2015;107:107-115. doi:10.1016/j.neuroimage.2014.12.006
- MR-ART dataset: OpenNeuro ds004173
- FreeSurfer: Fischl B. *NeuroImage*. 2012
- Modified z-score: Iglewicz B, Hoaglin DC. *How to Detect and Handle Outliers*. ASQC Quality Press; 1993
- ICC computation: McGraw KO, Wong SP. *Journal of Educational Measurement*. 1996
