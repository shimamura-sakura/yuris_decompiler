#!/bin/sh

set -ue

python main_official.py 0

CURDIR="$PWD"
cd /tmp/yuris_dec_out
LC_ALL=ja_JP.UTF-8 wine yu-ris.exe
cd "$CURDIR"

python main_official.py 1