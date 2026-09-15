#!/usr/bin/env bash
# Run FreeSurfer's brain-scan pipeline (recon-all) on every T1 MRI in a folder.
#
# Usage:
#   ./run_reconall.sh ds004173
#   ./run_reconall.sh ds004173 1
#   ./run_reconall.sh ds004173 1 sub-000103
#
# The optional second number is how many scans to process at the same time.
# Default is 1. On a 36 GB Mac, 2 can crash (macOS kills the job). Use 1 unless
# you are watching Activity Monitor and still have lots of unused memory.
#
# The optional third argument is one subject folder name (example: sub-000103).
# Use that for a test run so the script does not queue every scan.

set -u

BIDS_DIR=${1:?Usage: ./run_reconall.sh <folder_with_subjects> [how_many_at_once] [subject_id]}
MAX_PAR=${2:-1}
ONLY_SUB=${3:-}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If the folder you passed is not an absolute path, treat it as next to this script.
case "$BIDS_DIR" in
    /*) ;;
    *) BIDS_DIR="${SCRIPT_DIR}/${BIDS_DIR}" ;;
esac

export FREESURFER_HOME=/Applications/freesurfer/8.2.0
export FS_LICENSE="${FREESURFER_HOME}/license.txt"
export SUBJECTS_DIR="${SCRIPT_DIR}/fs_subjects"
# FreeSurfer's setup file reads this variable; it must exist before we load it.
export FS_FREESURFERENV_NO_OUTPUT=1

if [ ! -d "$FREESURFER_HOME" ]; then
    echo "Cannot find FreeSurfer at $FREESURFER_HOME" >&2
    exit 1
fi
if [ ! -f "$FS_LICENSE" ]; then
    echo "Cannot find the FreeSurfer license file at $FS_LICENSE" >&2
    exit 1
fi

# Load FreeSurfer's settings so the recon-all command is available.
# Their setup file uses unset variables, so turn that safety off only while loading.
# shellcheck disable=SC1091
set +u
source "${FREESURFER_HOME}/FreeSurferEnv.sh" >/dev/null
set -u
export SUBJECTS_DIR="${SCRIPT_DIR}/fs_subjects"

if ! command -v recon-all >/dev/null 2>&1; then
    echo "FreeSurfer loaded, but the recon-all command is still missing." >&2
    exit 1
fi

LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$SUBJECTS_DIR" "$LOG_DIR"

FAILED="${LOG_DIR}/failed_subjects.txt"
SUCCEEDED="${LOG_DIR}/succeeded_subjects.txt"
BATCH_LOG="${LOG_DIR}/batch_output.log"
: > "$FAILED"
: > "$SUCCEEDED"

log() {
    local line
    line="$(printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*")"
    printf '%s\n' "$line" | tee -a "$BATCH_LOG"
}

# Count only THIS script's background jobs (not every process on the Mac).
running_jobs() {
    jobs -pr | wc -l | tr -d ' '
}

# If a previous crash left a "I am still running" note, delete it when nothing
# is actually running. That note is just a small text file FreeSurfer uses as a
# do-not-touch sign.
clear_stale_running_notes() {
    local sdir="$1"
    rm -f \
        "${sdir}/scripts/IsRunning.lh" \
        "${sdir}/scripts/IsRunning.rh" \
        "${sdir}/scripts/"IsRunning*.lock \
        "${sdir}/scripts/"IsRunning*.txt \
        2>/dev/null || true
}

wait_for_slot() {
    local told=0
    while [ "$(running_jobs)" -ge "$MAX_PAR" ]; do
        if [ "$told" -eq 0 ]; then
            log "One scan is already running. The next scan will start when it finishes (this can take several hours)."
            told=1
        fi
        sleep 60
    done
}

log "Scan folder     = $BIDS_DIR"
log "Output folder   = $SUBJECTS_DIR"
log "Log folder      = $LOG_DIR"
log "At once         = $MAX_PAR"
log "Only subject    = ${ONLY_SUB:-all}"
log "FreeSurfer      = $FREESURFER_HOME"

if [ -n "$ONLY_SUB" ]; then
    case "$ONLY_SUB" in
        sub-*) ;;
        *) ONLY_SUB="sub-${ONLY_SUB}" ;;
    esac
fi

shopt -s nullglob
if [ -n "$ONLY_SUB" ]; then
    t1_files=("$BIDS_DIR"/"$ONLY_SUB"/anat/*_T1w.nii.gz)
else
    t1_files=("$BIDS_DIR"/sub-*/anat/*_T1w.nii.gz)
fi
shopt -u nullglob

if [ "${#t1_files[@]}" -eq 0 ]; then
    log "No scan files found. Expected: ${BIDS_DIR}/sub-*/anat/*_T1w.nii.gz"
    exit 1
fi

# Run the still scan first when it exists (cleaner test than starting with motion).
std_files=()
other_files=()
for t1 in "${t1_files[@]}"; do
    case "$t1" in
        *acq-standard*) std_files+=("$t1") ;;
        *) other_files+=("$t1") ;;
    esac
done
t1_files=("${std_files[@]}" "${other_files[@]}")

log "Found ${#t1_files[@]} scan file(s)"

total=0
launched=0
skipped=0

for t1 in "${t1_files[@]}"; do
    total=$((total + 1))

    base="$(basename "$t1" .nii.gz)"
    sid="mrart_${base}"
    sdir="${SUBJECTS_DIR}/${sid}"
    done_flag="${sdir}/scripts/recon-all.done"
    log_file="${LOG_DIR}/${sid}.log"
    ec_file="${LOG_DIR}/${sid}.exitcode"

    # A crash can leave a "done" note next to an error note. Only skip true successes.
    if [ -f "$done_flag" ] && [ ! -f "${sdir}/scripts/recon-all.error" ]; then
        log "[skip] $sid already finished"
        skipped=$((skipped + 1))
        continue
    fi
    if [ -f "${sdir}/scripts/recon-all.error" ]; then
        log "[retry] $sid previously failed; will resume or restart"
    fi

    wait_for_slot

    # A leftover folder from a crash must not be started with "-i" again.
    # "-i" means "here is a new scan." If the folder already has the converted
    # image, we continue the unfinished job instead.
    extra_args=()
    if [ -f "${sdir}/mri/orig.mgz" ]; then
        clear_stale_running_notes "$sdir"
        extra_args=(-no-isrunning)
        log "[resume] $sid (unfinished folder found; continuing without importing the scan again)"
        log "[run  ] $sid"
        (
            recon-all -s "$sid" -all "${extra_args[@]}" >"$log_file" 2>&1
            echo $? >"$ec_file"
            clear_stale_running_notes "$sdir"
        ) &
    else
        if [ -d "$sdir" ]; then
            log "[fresh] $sid (leftover folder had no usable image; deleting it and starting over)"
            rm -rf "$sdir"
        fi
        log "[run  ] $sid"
        (
            recon-all -i "$t1" -s "$sid" -all >"$log_file" 2>&1
            echo $? >"$ec_file"
            clear_stale_running_notes "$sdir"
        ) &
    fi

    launched=$((launched + 1))
done

log "Queued everything (found=$total, started_or_resumed=$launched, already_done=$skipped). Waiting for jobs to finish..."
wait

pass=0
fail=0
missing=0
for t1 in "${t1_files[@]}"; do
    base="$(basename "$t1" .nii.gz)"
    sid="mrart_${base}"
    ec_file="${LOG_DIR}/${sid}.exitcode"
    done_flag="${SUBJECTS_DIR}/${sid}/scripts/recon-all.done"

    if [ -f "$done_flag" ]; then
        echo "$sid" >>"$SUCCEEDED"
        pass=$((pass + 1))
        continue
    fi

    if [ -f "$ec_file" ]; then
        code="$(cat "$ec_file" 2>/dev/null || echo 999)"
        echo "$sid (exit ${code})" >>"$FAILED"
        fail=$((fail + 1))
    else
        echo "$sid (no exit record)" >>"$FAILED"
        missing=$((missing + 1))
    fi
done

log "=================================================="
log "Finished OK : $pass"
log "Failed      : $fail"
log "No record   : $missing"
log "Fail list   : $FAILED"
log "OK list     : $SUCCEEDED"
log "Batch log   : $BATCH_LOG"
log "=================================================="

if [ "$fail" -gt 0 ] || [ "$missing" -gt 0 ]; then
    exit 1
fi
exit 0
