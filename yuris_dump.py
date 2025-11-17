#!/bin/env python3
from sys import stdout
from io import TextIOBase
from os import path, makedirs
from yuris import *


def dump(idir: str, odir: str, yscd: YSCD, key: int, renc: str, wenc: str):
    with open(path.join(idir, 'yst_list.ybn'), 'rb') as fp:
        ystl = YSTL(Rdr(fp.read(), renc))
    for scr in ystl.scrs:
        if scr.nvar < 0:
            continue
        with open(path.join(idir, f'yst{scr.id:0>5}.ybn'), 'rb') as fp:
            ystb = YSTB(fp, key, renc)
        out_path = path.join(odir, scr.path.replace('\\', '/')+'.dump')
        makedirs(path.dirname(out_path), exist_ok=True)
        print(scr.id, out_path)
        with open(out_path, 'w', encoding=wenc) as ft:
            do_ystb(yscd, ystb, ft, renc)


ASSIGN = {
    'LET', 'INT', 'STR', 'FLT',
    'S_INT', 'S_STR', 'S_FLT',
    'G_INT', 'G_STR', 'G_FLT',
    'F_INT', 'F_STR', 'F_FLT'}


def do_ystb(yscd: YSCD, ystb: YSTB, f: TextIOBase, enc: str):
    l: list[str] = []
    exp_data = ystb.data
    for pc, cmd in enumerate(ystb.cmds):
        cmd_desc = yscd.cmds[cmd.code]
        cmd_name = cmd_desc.name
        narg = len(args := cmd.args)  # to compare structure only, comment out PC
        l.append(f'PC={pc} L={cmd.line_no} {cmd_desc.name} narg={len(cmd.args)}\n')
        match cmd_name:
            case 'RETURNCODE':
                assert narg == 1 and args[0].off == 0
                l.append(f'- code: {do_arg(args[0], exp_data, False, False, enc)}\n')
            case 'IF' | 'ELSE' if narg == 3:
                assert narg == 3
                l.append(f'- cond: {do_arg(args[0], exp_data, True, True, enc)}\n')
                l.append(f'- then: {do_arg(args[1], exp_data, False, False, enc)}\n')
                l.append(f'- else: {do_arg(args[2], exp_data, False, False, enc)}\n')
            case 'LOOP':
                assert narg == 2
                l.append(f'- cond: {do_arg(args[0], exp_data, True, True, enc)}\n')
                l.append(f'- loop: {do_arg(args[1], exp_data, False, False, enc)}\n')
            case x if x in ASSIGN:
                assert narg == 2
                l.append(f'- lhs: {do_arg(args[0], exp_data, True, True, enc)}\n')
                l.append(f'- rhs: {do_arg(args[1], exp_data, True, True, enc)}\n')
            case 'WORD':
                assert narg == 1
                l.append(do_arg(args[0], exp_data, False, True, enc)+'\n')
            case _:
                des_args = cmd_desc.args
                for arg in cmd.args:
                    arg_desc = des_args[arg.id]
                    arg_name = arg_desc.name
                    l.append(f'{arg_name}: {do_arg(arg, exp_data, False, True, enc)}\n')
    f.writelines(l)


def do_arg(arg: Arg, exp_data: bytes, force_exp: bool, disasm: bool, enc: str):
    k0 = f'id={arg.id} typ={arg.typ} ari={arg.ari} off={arg.off} len={arg.len}'
    if not disasm:
        return k0
    assert len(raw_data := exp_data[arg.off:arg.off+arg.len]) == arg.len
    if arg.typ == 0 and not force_exp:
        return f'{k0}: {raw_data.decode(enc)}'
    ins_list = Ins.parse_buf(raw_data, enc)
    return f'{k0}: {ins_list}'
