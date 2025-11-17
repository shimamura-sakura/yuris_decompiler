#!/bin/env python3
import sys
import yuris_dump as Ydmp
import yuris_disasm as Ydis
renc = Ydis.ENC
wenc = Ydis.ENC
key = Ydis.YSTB_DEFAULT_KEY
fin = '/home/jerry/Downloads/_others/yu-ris_0488_019/システム'
with open(fin+'/system/YSCom/YSCom.ycd', 'rb') as fp:
    yscd = Ydis.YSCD(Ydis.Rdr(fp.read(), renc))
fdi_1 = fin+'/data/ysbin'
fdo_1 = '/tmp/yuris_dec_out'
fdi_2 = fdo_1+'/data/ysbin'
fdo_2 = '/tmp/yuris_recompile'
match int(sys.argv[1]):
    case 0:  # original
        Ydis.disasm(fdi_1, fdo_1, yscd, key, renc, wenc)
        Ydmp.dump(fdi_1, fdo_1, yscd, key, renc, 'utf-8')
    case 1:  # recompiled
        Ydis.disasm(fdi_2, fdo_2, yscd, key, renc, wenc)
        Ydmp.dump(fdi_2, fdo_2, yscd, key, renc, 'utf-8')
    case -1:  # original
        Ydmp.dump(fdi_1, fdo_1, yscd, key, renc, 'utf-8')
        Ydmp.dump(fdi_2, fdo_2, yscd, key, renc, 'utf-8')
    case x: assert False, x
