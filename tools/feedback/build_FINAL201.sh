#!/bin/sh
# FINAL201 = FINAL198 rebuilt from FINAL197 with 12 pt field names and values, darker field names, a header sized to its content,
# then FINAL199 (PDF all pages) and FINAL200 (PaperOrientation) on top. Run from the scratchpad that holds newV59 and the build scripts.
set -e
SRC=newV59 NEW=w60 LBL_SF=12 VAL_SF=12 HEADER_V2=1 LBL_COLOR='RGBA(70, 76, 90, 1)' python3 build_V60.py
SRC=w60 NEW=w61 python3 build_V61.py
SRC=w61 NEW=newV63 python3 build_V62.py
rm -rf w60 w61
