#!/bin/env python3
import yuris_dump as Ydmp
import yuris_disasm as Ydis
renc = Ydis.ENC  # shift-jis
wenc = Ydis.ENC  # shift-jis, would anyone ever use other?
key = Ydis.YSTB_DEFAULT_KEY  # 0xD36FAC96
# where yu-ris.exe is placed
# download from https://yu-ris.net/download/index.html
folder = 'yu-ris_0488_019/システム' # reads SHISUTEMU [=system]
# need official compiler definition
with open(folder+'/system/YSCom/YSCom.ycd', 'rb') as fp:
    yscd = Ydis.YSCD(Ydis.Rdr(fp.read(), renc))
# set DEBUGMODE=0 in data/config/projectconfig.txt and run once to compile
folder_i = folder+'/data/ysbin'
# will create data/script under this due to yst_list.ybn
folder_o = '/tmp/yuris_decompile_out'
# run!
Ydis.disasm(folder_i, folder_o, yscd, key, renc, wenc)
# now you have this folder structure
# /
#    data/
#        script/(...)
#        ! copy all other folders except [script] and [ysbin] to here
#    ! from [システム] copy these folders and files:
#    ! [system/] [yscfg.dat] [yu-ris.exe] [エンジン設定.exe]
# ok, run [yu-ris.exe] and see it compile and run
# ---
# similar, but it writes disassembly to [.yst/.txt].dump
# it's intended to be read by a human, so use utf-8, our favorite
Ydmp.dump(folder_i, folder_o, yscd, key, renc, 'utf-8')
# one usage:
# 1. dump the commands from compiled files [e.g. from YSbin.ypf of your game]
# 2. decompile, recompile and dump again
# 3. see the difference between two versions and maybe discover decompiler bugs
