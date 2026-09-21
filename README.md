# MRART_Demo_Project
FreeSurfer recon-all on 20 subjects × 3 motion conditions from the MR-ART dataset (ds004173), quantifying how cortical thickness estimates drift under increasing head motion.

**Author:** Jolane Abrams  
**Contact:** jkabrams@alumni.usc.edu | /Users/jolaneabrams/Desktop/GitHub/MRART_Demo_Project | 
https://www.linkedin.com/in/jolane-abrams-309b3412/

---

## Abstract

Head motion degrades structural MRI morphometry, but the magnitude of that degradation is rarely shown end-to-end with a public dataset. This project runs FreeSurfer recon-all on 20 subjects × 3 motion conditions from the MR-ART dataset (ds004173) and quantifies how cortical thickness estimates drift under increasing head motion.

---

## Data

**Dataset:** MR-ART (Movement-Related ARTefacts)  
**Repository:** [OpenNeuro ds004173](https://openneuro.org/datasets/ds004173)  
**DOI:** [Insert DOI once verified]

The MR-ART dataset contains T1-weighted 3D structural MRI images of 148 healthy adults, each scanned three times under increasing head motion (still, mild, moderate). All scans are anonymized, BIDS-organized, and defaced.

**Subset used:** First 20 subjects, **59 T1 scans** (not 60). `sub-105822` has no `acq-headmotion1` (mild) scan. Subject labels are non-sequential 6-digit IDs (e.g., `sub-000103`).

### Download Command

```bash
source ~/venvs/neuro/bin/activate
openneuro-py download --dataset ds004173 --include sub-000103  # repeat for each of 20 subjects
Pipeline Overview

[BLOCK FOR PIPELINE FLOWCHART IMAGE]

Insert flowchart image here after batch begins running:

    Input: BIDS-formatted T1 scans (sub-*/anat/*_T1w.nii.gz)
    Processing: FreeSurfer recon-all -all (v8.2.0)
    Output: Per-subject aparc.stats / aseg.stats tables
    Aggregation: Python extraction to tidy CSV
    Analysis: Drift metrics (percent change), reliability (ICC)

Environment
Software Versions
Component	Version	Installation
macOS	26.6.2
Python	3.12.2	Homebrew / python.org
FreeSurfer	8.2.0	freesurfer.net
XQuartz   2.8.6	xquartz.org
openneuro-py  2026.7.1
pandas   3.0.5	
matplotlib   3.11.1
seaborn   0.13.2
pingouin  0.6.1	
nibabel	  5.4.2 

Virtual Environment Setup
python3 -m venv ~/venvs/neuro
source ~/venvs/neuro/bin/activate
python3 -m pip install openneuro-py pandas matplotlib seaborn pingouin nibabel
Environment Variables
export SUBJECTS_DIR=$HOME/mrart_demo/fs_subjects
export FREESURFER_HOME=/usr/local/freesurfer/8.2.0  # Adjust to your install
source $FREESURFER_HOME/SetUpFreeSurfer.sh
Directory Structure
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
Quality Control Protocol
Inclusion Criteria

    Surface/white-matter boundary alignment visually inspected in FreeView
    Coronal/sagittal/axial slice coverage adequate
    No segmentation errors (pial surface outside skull, etc.)

Exclusion Criteria

    Failed recon-all (no recon-all.done marker)
    QC flag: surface misalignment > 1mm visible
    Corrupted or incomplete output files

Failure Log

Per-subject logs stored in logs/. Batch-generated failure list: logs/failed_subjects.txt (empty if all succeed).
Status

    ✅ Environment configured (XQuartz, FreeSurfer 8.2.0, Python venv)
    ✅ 20 subjects downloaded (59 T1 scans; no mild scan for sub-105822)
    ✅ Subject ID schema verified (6-digit non-sequential)
    ✅ recon-all -all finished on all 59 scans (FreeSurfer 8.2.0, MAX_PAR=1)
    ✅ Mean scan time 1.7 h (range 83–134 min); batch wall clock 90 h for 55 scans (17–21 Sep 2026)
    ⏳ Visual QC in FreeView
    ⏳ Thickness/volume tables → tidy CSV and drift/ICC analysis
    📁 Raw data: ds004173/ (local, not in git)
    📁 Outputs: fs_subjects/ (local, ~25 GB, not in git)
    📋 Success list: logs/succeeded_subjects.txt

Next Steps

    Visual QC of white/pial surfaces in FreeView
    Extract thickness tables using aparcstats2table / asegstats2table
    Generate tidy CSV with motion-condition mapping
    Compute drift metrics (% change per ROI)
    Calculate ICC(3,1) reliability per region
    Generate figures (box plots, spaghetti plot, ICC bar chart)
    Draft limitations and contact section

Limitations

Demo-scale sample (~20 subjects); not powered for statistical inference. Single dataset, single scanner vendor. Intended as a pipeline-competence artifact rather than a novel publication.
Contact

Jolane Abrams — jkabrams@alumni.usc.edu
Open to collaboration on imaging QC / PTSD morphometry / ENIGMA working groups.
References

    MR-ART Dataset: OpenNeuro ds004173
    FreeSurfer: Fischl B. NeuroImage 2012
    ICC computation: McGraw KO, Wong SP. Journal of Educational Measurement 1996



