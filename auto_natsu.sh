#!/bin/sh

set -ue

python main_natsu.py 0

CURDIR="$PWD"
cd /tmp/natsu_dec_out
LC_ALL=ja_JP.UTF-8 wine yu-ris.exe
cd "$CURDIR"

python main_natsu.py 1