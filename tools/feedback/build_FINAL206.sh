#!/bin/sh
# FINAL206 = FINAL204 rebuilt from FINAL203 with a 12 pt page header and footer (BIG_HEADER), then FINAL205 (Download PDF through the flow).
set -e
SRC=newV65 NEW=w68 BIG_HEADER=1 python3 build_V68.py
SRC=w68 NEW=newV68 python3 build_V67.py
rm -rf w68
