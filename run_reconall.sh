#B. BATCH RECON-ALL SCRIPT (Save as run_reconall.sh) 

!/usr/bin/env bash 
# Batch recon-all for MR-ART (ds004173) subset 

# Usage: ./run_reconall.sh <bids_dir> [max_parallel] 

set -u 
BIDS_DIR=${1:?Usage: run_reconall.sh <bids_dir> [max_parallel]} MAX_PAR=${2:-2}
 # parallel jobs; match your CPU cores conservatively 
export FREESURFER_HOME=/usr/local/freesurfer/8.2.0 
source $FREESURFER_HOME/SetUpFreeSurfer.sh >/dev/null export 
SUBJECTS_DIR=$HOME/mrart_demo/fs_subjects 
LOG_DIR=$HOME/mrart_demo/logs; mkdir -p "$LOG_DIR" 
FAILED="$LOG_DIR/failed_subjects.txt"; : > "$FAILED" count=0 for t1 in "$BIDS_DIR"/sub-*/anat/*_T1w.nii.gz; do base=$(basename "$t1" .nii.gz) 
# e.g. sub-01_acq-motion1_T1w sid="mrart_${base}" 
# unique FreeSurfer subject ID; skip if this recon already finished 
if [ -f "$SUBJECTS_DIR/$sid/scripts/recon-all.done" ]; then echo "[skip] $sid already complete"; continue fi echo "[run ] $sid" ( recon-all -i "$t1" -s "$sid" -all \ > "$LOG_DIR/${sid}.log" 2>&1 ) & 
# Throttle parallel jobs 
while [ "$(jobs -rp | wc -l)" -ge "$MAX_PAR" ]; do sleep 60; done done wait # Final sweep: report anything that didn't finish for sdir in "$SUBJECTS_DIR"/mrart_*; do s=$(basename "$sdir") [ -f "$sdir/scripts/recon-all.done" ] || echo "$s" >> "$FAILED" done echo "Done. Failures (if any) listed in $FAILED"