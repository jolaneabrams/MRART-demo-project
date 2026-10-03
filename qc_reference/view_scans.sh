 
# Viewing scans 

# python3 -m venv ~/venvs/neuro
# source ~/venvs/neuro/bin/activate

# cd Desktop/GitHub/MRART_Demo_Project

export FREESURFER_HOME=/Applications/freesurfer/8.2.0
export SUBJECTS_DIR="$PWD/fs_subjects"
source "$FREESURFER_HOME/FreesurferEnv.sh"

SID=mrart_sub-000103_acq-standard_T1w
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

# To load still and motion scans together

STILL=$SUBJECTS_DIR/mrart_sub-122916_acq-standard_T1w
MOT=$SUBJECTS_DIR/mrart_sub-122916_acq-headmotion2_T1w
open -n "$FREESURFER_HOME/Freeview.app" --args \
  -v "$STILL/mri/T1.mgz" \
     "$STILL/mri/aseg.mgz:colormap=lut:opacity=0.35" \
  -ras 9.6 38.8 4.4
open -n "$FREESURFER_HOME/Freeview.app" --args \
  -v "$MOT/mri/T1.mgz" \
     "$MOT/mri/aseg.mgz:colormap=lut:opacity=0.35" \
  -ras 9.6 38.8 4.4

  
