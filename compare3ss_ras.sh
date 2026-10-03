#!/bin/bash
# Matched slices for one subject across still, mild, and moderate recon-all runs.
# White surface is drawn in blue, pial surface in red, on T1.mgz.
#
# These volumes are LIA, so:
#   axial    varies the middle index (inferior-superior)
#   coronal  varies the third index  (anterior-posterior)
#   sagittal varies the first index  (left-right)
#
# The same voxel index is not the same place in the brain once the head has
# moved. Slice positions are chosen on the still scan and mapped into the
# other scans with talairach.lta (voxel-to-voxel, via the atlas). A file
# named <label>_axial_100.png is the axial plane through the anatomy at
# still-scan index 100, not voxel 100 in that scan.

export FREESURFER_HOME=/Applications/freesurfer/8.2.0
export SUBJECTS_DIR="$PWD/fs_subjects"
# shellcheck disable=SC1091
source "$FREESURFER_HOME/FreeSurferEnv.sh"

SID_BASE="${SID_BASE:-mrart_sub-000148}"
START="${START:-40}"
END="${END:-200}"
STEP="${STEP:-10}"
CENTER="${CENTER:-127}"

OUTDIR="$PWD/comparison/slices_${SID_BASE}"
mkdir -p "$OUTDIR"
echo "Output: $OUTDIR"

STILL="$SUBJECTS_DIR/${SID_BASE}_acq-standard_T1w"
MLD="$SUBJECTS_DIR/${SID_BASE}_acq-headmotion1_T1w"
MOD="$SUBJECTS_DIR/${SID_BASE}_acq-headmotion2_T1w"

python3 - "$OUTDIR" "$START" "$END" "$STEP" "$CENTER" \
  "$STILL" still \
  "$MLD" mld \
  "$MOD" mod << 'PY'
import os
import sys

outdir = sys.argv[1]
start, end, step, center = (int(x) for x in sys.argv[2:6])
pairs = sys.argv[6:]
if len(pairs) % 2:
    raise SystemExit("conditions must be directory/label pairs")
conds = list(zip(pairs[0::2], pairs[1::2]))

def read_lta(path):
    lines = open(path).read().splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "1 4 4":
            return [[float(x) for x in lines[i + k].split()] for k in range(1, 5)]
    raise SystemExit(f"no matrix in {path}")

def matvec(M, v):
    return [sum(M[i][j] * v[j] for j in range(4)) for i in range(4)]

def invert(M):
    n = 4
    A = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-12:
            raise SystemExit("talairach matrix is singular")
        A[col], A[piv] = A[piv], A[col]
        f = A[col][col]
        A[col] = [x / f for x in A[col]]
        for r in range(n):
            if r == col:
                continue
            g = A[r][col]
            A[r] = [A[r][c] - g * A[col][c] for c in range(2 * n)]
    return [row[n:] for row in A]

def clamp(v):
    return max(0, min(255, int(v + 0.5)))

still_dir = conds[0][0]
M_still = read_lta(f"{still_dir}/mri/transforms/talairach.lta")
planes = (
    ("axial", 1),
    ("coronal", 2),
    ("sagittal", 0),
)

coords_path = f"{outdir}/slice_coords.tsv"
with open(coords_path, "w") as coords:
    coords.write("label\tplane\tstill_index\tx\ty\tz\tpng\n")
    for subj_dir, label in conds:
        t1 = f"{subj_dir}/mri/T1.mgz"
        lta = f"{subj_dir}/mri/transforms/talairach.lta"
        surfs = [
            (f"{subj_dir}/surf/lh.white", "blue"),
            (f"{subj_dir}/surf/rh.white", "blue"),
            (f"{subj_dir}/surf/lh.pial", "red"),
            (f"{subj_dir}/surf/rh.pial", "red"),
        ]
        missing = [p for p, _ in surfs if not os.path.isfile(p)]
        missing += [p for p in (t1, lta) if not os.path.isfile(p)]
        if missing or not os.path.isdir(subj_dir):
            print(f"Missing inputs for {label}: {subj_dir}", file=sys.stderr)
            for p in missing:
                print(f"  {p}", file=sys.stderr)
            continue
        M = read_lta(lta)
        Minv = invert(M)
        cmd_path = f"{outdir}/cmd_{label}.txt"
        with open(cmd_path, "w") as cmd:
            cmd.write(f"-v {t1}\n")
            for path, color in surfs:
                cmd.write(f"-f {path}:edgecolor={color}:edgethickness=2\n")
            for plane, axis in planes:
                for idx in range(start, end + 1, step):
                    still = [center, center, center]
                    still[axis] = idx
                    tpl = matvec(M_still, still + [1.0])
                    xyz = matvec(Minv, tpl)
                    sl = [clamp(xyz[0]), clamp(xyz[1]), clamp(xyz[2])]
                    png = f"{outdir}/{label}_{plane}_{idx}.png"
                    cmd.write(
                        f"-viewport {plane} -slice {sl[0]} {sl[1]} {sl[2]} "
                        f"-viewsize 800 800 -ss {png} -noquit\n"
                    )
                    coords.write(
                        f"{label}\t{plane}\t{idx}\t{sl[0]}\t{sl[1]}\t{sl[2]}\t{png}\n"
                    )
            cmd.write("-quit\n")
        print(f"Wrote {cmd_path}")
PY

wait_for_freeview() {
  local n=0
  while pgrep -x freeview >/dev/null; do
    n=$((n + 1))
    if [ "$n" -gt 120 ]; then
      echo "A freeview process is still running. Close it, then rerun." >&2
      return 1
    fi
    sleep 0.5
  done
}

n_ok=0
for LABEL in still mld mod; do
  CMD_FILE="$OUTDIR/cmd_${LABEL}.txt"
  if [ ! -f "$CMD_FILE" ]; then
    echo "No command file for $LABEL"
    continue
  fi
  echo "Slicing $LABEL..."
  wait_for_freeview || exit 1
  freeview -cmd "$CMD_FILE" > "$OUTDIR/freeview_${LABEL}.log" 2>&1
  echo "  freeview exit $?"
  wait_for_freeview || exit 1
  n_ok=$((n_ok + 1))
done

echo "Done. Slices in $OUTDIR"
find "$OUTDIR" -name '*.png' | wc -l | awk '{print $1 " png files"}'
if [ "$n_ok" -ne 3 ]; then
  echo "Expected screenshots for still, mld, and mod." >&2
  exit 1
fi
