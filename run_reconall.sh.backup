#!/usr/bin/env bash
# Batch recon-all for MR-ART (ds004173) subset
# Usage: ./run_reconall.sh <bids_dir> [max_parallel]

BIDS_DIR=${1:?Usage: run_reconall.sh <bids_dir> [max_parallel]}
MAX_PAR=${2:-2}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SUBJECTS_DIR="${SCRIPT_DIR}/fs_subjects"

export FREESURFER_HOME=/Applications/freesurfer/8.2.0
export FS_FREESURFERENV_NO_OUTPUT=1
export PS1="$ "
source $FREESURFER_HOME/FreeSurferEnv.sh >/dev/null 2>&1

LOG_DIR="${SCRIPT_DIR}/logs"; mkdir -p "$LOG_DIR"
FAILED="$LOG_DIR/failed_subjects.txt"; : > "$FAILED"

for t1 in "$BIDS_DIR"/sub-*/anat/*_T1w.nii.gz; do
    base=$(basename "$t1" .nii.gz)
    sid="mrart_${base}"

    if [ -f "$SUBJECTS_DIR/$sid/scripts/recon-all.done" ]; then
        echo "[skip] $sid already complete"; continue
    fi

    echo "[run ] $sid"
    ( recon-all -i "$t1" -s "$sid" -all \
        > "$LOG_DIR/${sid}.log" 2>&1 ) &

    while [ "$(jobs -rp | wc -l)" -ge "$MAX_PAR" ]; do sleep 60; done
done
wait

for sdir in "$SUBJECTS_DIR"/mrart_*; do
    s=$(basename "$sdir")
    [ -f "$sdir/scripts/recon-all.done" ] || echo "$s" >> "$FAILED"
done
echo "Done. Failures (if any) listed in $FAILED"
