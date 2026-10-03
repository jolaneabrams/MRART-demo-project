#!/bin/bash



# export FREESURFER_HOME=/Applications/freesurfer/8.2.0
# export SUBJECTS_DIR="$PWD/fs_subjects"
# source "$FREESURFER_HOME/FreesurferEnv.sh"

# STILL=mrart_sub-000103_acq-standard_T1w
# MLD=mrart_sub-000103_acq-headmotion1_T1w
# MOD=mrart_sub-000103_acq-headmotion2_T1w

# RAS="9.6 38.8 4.4"

# for SID in "$STILL" "$MLD" "$MOD"; do
#   open -n "$FREESURFER_HOME/Freeview.app" --args \
#     -v "$SUBJECTS_DIR/$SID/mri/T1.mgz" \
#     -f "$SUBJECTS_DIR/$SID/surf/lh.white:edgecolor=blue" \
#        "$SUBJECTS_DIR/$SID/surf/lh.pial:edgecolor=red" \
#        "$SUBJECTS_DIR/$SID/surf/rh.white:edgecolor=blue" \
#        "$SUBJECTS_DIR/$SID/surf/rh.pial:edgecolor=red" \
#     -ras $RAS \
#     -quitbutt
# done



#!/bin/bash

export FREESURFER_HOME=/Applications/freesurfer/8.2.0
export SUBJECTS_DIR="$PWD/fs_subjects"
source "$FREESURFER_HOME/FreesurferEnv.sh"

# Subject ID (keep original naming)
SID_BASE="mrart_sub-000103"
STILL="$SUBJECTS_DIR/${SID_BASE}_acq-standard_T1w"
MLD="$SUBJECTS_DIR/${SID_BASE}_acq-headmotion1_T1w"
MOD="$SUBJECTS_DIR/${SID_BASE}_acq-headmotion2_T1w"

# Automatically extract RAS center coordinates from standard scan
# --cras output: R A S (three values in one line)
RAS_COORDS=$(mri_info --cras "$STILL/mri/orig.mgz")
echo "Extracted center RAS: $RAS_COORDS"

# Common view parameters
RAS_ARGS="-ras $RAS_COORDS"

# Open three independent Freeview windows (& lets script continue executing)
for COND in "$STILL" "$MLD" "$MOD"; do
    if [ -d "$COND" ]; then
        open -n "$FREESURFER_HOME/Freeview.app" --args \
          -v "$COND/mri/T1.mgz" \
             "$COND/mri/aseg.mgz:colormap=lut:opacity=0.35" \
          $RAS_ARGS &
    else
        echo "Warning: directory not found - $COND"
    fi
done

wait