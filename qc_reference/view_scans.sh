 
# Viewing scans 

# python3 -m venv ~/venvs/neuro
# source ~/venvs/neuro/bin/activate

cd Desktop/GitHub/MRART_Demo_Project

# export FREESURFER_HOME=/Applications/freesurfer/8.2.0
# source "$FREESURFER_HOME/FreesurferEnv.sh"
# export SUBJECTS_DIR="$PWD/fs_subjects"

# SID=mrart_sub-000103_acq-standard_T1w
freeview \
  -v "$SUBJECTS_DIR/$SID/mri/T1.mgz" \
  -f "$SUBJECTS_DIR/$SID/surf/lh.white:edgecolor=blue" \
     "$SUBJECTS_DIR/$SID/surf/lh.pial:edgecolor=red" \
     "$SUBJECTS_DIR/$SID/surf/rh.white:edgecolor=blue" \
     "$SUBJECTS_DIR/$SID/surf/rh.pial:edgecolor=red" 

SID=mrart_sub-000103_acq-headmotion2_T1w
freeview \
  -v "$SUBJECTS_DIR/$SID/mri/T1.mgz" \
  -f "$SUBJECTS_DIR/$SID/surf/lh.white:edgecolor=blue" \
     "$SUBJECTS_DIR/$SID/surf/lh.pial:edgecolor=red" \
     "$SUBJECTS_DIR/$SID/surf/rh.white:edgecolor=blue" \
     "$SUBJECTS_DIR/$SID/surf/rh.pial:edgecolor=red"      