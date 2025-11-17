#!/bin/env python3
from yuris import *
from sys import stdout
from io import TextIOBase


def run(fdr: str, f: TextIOBase, enc: str):
    with open(fdr+'/yscfg.ybn', 'rb') as fp:
        y = YSCF(Rdr(fp.read(), enc))
        f.write('- yscfg.ybn -\n')
        for k in sorted(y.__dict__.keys()):
            f.write(f'{k}: {getattr(y, k)}\n')
    with open(fdr+'/ysl.ybn', 'rb') as fp:
        y = YSLB(Rdr(fp.read(), enc))
        f.write('- ysl.ybn -\n')
        for i, l in enumerate(y.lbls):
            f.write(f'[{i}] id={hex(l.id)} pc={l.pc} scr_id={l.scr_id} pad={l.pad} {l.name}\n')
    with open(fdr+'/yst_list.ybn', 'rb') as fp:
        y = YSTL(Rdr(fp.read(), enc))
        f.write('- yst_list.ybn -\n')
        for i, s in enumerate(y.scrs):  # omit s.time
            f.write(f'[{i}] {s.path} id={s.id} nvar={s.nvar} nlbl={s.nlbl} ntext={s.ntext}\n')
    with open(fdr+'/ysv.ybn', 'rb') as fp:
        y = YSVR(Rdr(fp.read(), enc))
        f.write('- ysv.ybn -\n')
        for i, v in enumerate(y.vars):
            f.write(f'[{i}] scope={v.scope} scr_id={v.scr_id} var_id={v.var_id} dim={v.dim} typ={v.typ} val=')
            match v.typ:
                case 0: f.write('None\n')
                case 1 | 2: f.write(str(v.val)+'\n')
                case 3: f.write(str(Ins.parse_buf(v.val, enc))+'\n')


if 1:
    with open('ybns_org.txt', 'w') as ft:
        run('ysbin-natsu', ft, ENC)
    with open('ybns_dec.txt', 'w') as ft:
        run('/tmp/natsu_dec_out/data/ysbin', ft, ENC)
else:
    with open('ybns_org.txt', 'w') as ft:
        run('/home/jerry/Downloads/_others/yu-ris_0488_019/システム/data/ysbin', ft, ENC)
    with open('ybns_dec.txt', 'w') as ft:
        run('/tmp/yuris_dec_out/data/ysbin', ft, ENC)
