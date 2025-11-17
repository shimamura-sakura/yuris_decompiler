#!/bin/env python3
from sys import stdout
from io import TextIOBase
from os import path, makedirs
from yuris import *


def disasm(idir: str, odir: str, yscd: YSCD, key: int, renc: str, wenc: str):
    # 0. read needed files
    with open(path.join(idir, 'ysv.ybn'), 'rb') as fp:
        ysvr = YSVR(Rdr(fp.read(), renc))
    with open(path.join(idir, 'ysl.ybn'), 'rb') as fp:
        yslb = YSLB(Rdr(fp.read(), renc))
    with open(path.join(idir, 'yst_list.ybn'), 'rb') as fp:
        ystl = YSTL(Rdr(fp.read(), renc))
    # 1. create env, define global variables -> global.yst
    yenv = YEnv(yscd, ysvr)
    vinits = ysvr_varinits(yenv, ysvr, renc)
    glbs: list[str] | None = ysvr_global(yenv, ysvr, renc)
    # 2. get labels
    lbls: dict[int, list[Lbl]] = {}
    for scr in ystl.scrs:
        lbls[scr.id] = []
    for lbl in yslb.lbls:
        lbls[lbl.scr_id].append(lbl)
    # 3. disasm script files (yst%>05d.ybn) -> {path}.yst
    for scr in ystl.scrs:
        out_path = path.join(odir, scr.path.replace('\\', '/'))
        makedirs(path.dirname(out_path), exist_ok=True)
        if scr.nvar < 0:
            with open(out_path, 'w', encoding=wenc, newline='\r\n') as ft:
                if glbs:
                    print(scr.id, out_path, '- empty, we put globals here')
                    ft.writelines(glbs)
                    glbs = None
                else:
                    print(scr.id, out_path, '- empty')
                    ft.write(';')
        else:
            print(scr.id, out_path)
            with open(path.join(idir, f'yst{scr.id:0>5}.ybn'), 'rb') as fp:
                ystb = YSTB(fp, key, renc)
            with open(out_path, 'w', encoding=wenc, newline='\r\n') as ft:
                do_ystb(yenv, yscd, ystb, lbls[scr.id], vinits, ft, renc)
    # 4. no empty file to put globals, create one
    if glbs:
        print('no empty file to put global, writing to data/script/global.yst')
        makedirs(path.join(odir, 'data/script'), exist_ok=True)
        with open(path.join(odir, 'data/script/global.yst'), 'w',
                  encoding=wenc, newline='\r\n') as ft:
            ft.writelines(glbs)


def ysvr_global(yenv: YEnv, ysvr: YSVR, enc: str):
    lines: list[str] = []
    com_vars = yenv.com_vars
    cmd_name = {1: 'G_INT', 2: 'G_FLT', 3: 'G_STR'}
    for v in ysvr.vars:
        if (v.var_id in com_vars) or (v.scope != 1) or (v.typ == 0):
            continue  # compiler, non-global or non-existent
        var_cmd = cmd_name[v.typ]
        var_def = yenv.fmt_var(v.var_id, v.typ)
        var_dim = f'({','.join(map(str, v.dim))})' if len(v.dim) else ''
        match v.typ:
            case 1 | 2: var_val = '='+str(v.val) if v.val else ''
            case 3:
                ins_list = Ins.parse_buf(v.val, enc)
                var_val = '='+yenv.eval(ins_list, enc) if len(ins_list) else ''
            case typ: assert False, 'invalid typ'+str(typ)
        lines.append(f'{var_cmd}[{var_def}{var_dim}{var_val}]\n')
    return lines


TVInits = dict[int, int | float | list[Ins]]


def ysvr_varinits(yenv: YEnv, ysvr: YSVR, enc: str):
    com_vars = yenv.com_vars
    varinits: TVInits = {}
    for v in ysvr.vars:
        if (v.var_id in com_vars) or (v.typ == 0):
            continue  # compiler, non-existent
        match v.typ:
            case 1 | 2: varinits[v.var_id] = v.val
            case 3: varinits[v.var_id] = Ins.parse_buf(v.val, enc)
    return varinits


ASSIGN = {
    'LET', 'INT', 'STR', 'FLT',
    'S_INT', 'S_STR', 'S_FLT',
    'G_INT', 'G_STR', 'G_FLT',
    'F_INT', 'F_STR', 'F_FLT'}
ARI = {0: '=', 1: '+=', 2: '-=', 3: '*=', 4: '/=', 5: '%=', 6: '&=', 7: '|=', 8: '^='}
SKIP = {'IFBLEND': 0, 'RETURNCODE': 1}


def do_ystb(yenv: YEnv, yscd: YSCD, ystb: YSTB, lbls: list[Lbl], vinits: TVInits, f: TextIOBase, enc: str):
    # 0. for easy use
    exp_data = ystb.data
    # 1. count all labels
    pc_lbls: list[list[Lbl] | bool] = [False] * len(ystb.cmds)
    for lbl in lbls:
        if (l := pc_lbls[lbl.pc]) == False:
            pc_lbls[lbl.pc] = [lbl]
        else:
            l.append(lbl)
    # 2. iterate through commands
    nline = max(map(lambda c: c.line_no, ystb.cmds))
    lines: list[list[str] | bool] = [False] * nline
    for pc, (lbls, cmd) in enumerate(zip(pc_lbls, ystb.cmds)):
        # 1. create line and write labels (preferably into prev line)
        line = lines[iline := cmd.line_no-1]
        if lbls:
            lbls_segs = list(map(lambda l: '#='+l.name+';', lbls))
            if line:
                line.extend(lbls_segs)
            elif iline == 0 or lines[iline-1]:
                line = lines[iline] = lbls_segs
            else:
                lines[iline-1] = lbls_segs
        if not line:
            line = lines[iline] = []
        # 2. write current command
        cmd_desc = yscd.cmds[cmd.code]
        cmd_name = cmd_desc.name
        narg = len(args := cmd.args)
        match cmd_name:
            case x if x in SKIP: assert narg == SKIP[x]
            case 'IF' | 'ELSE' if narg == 3:  # IF/ELIF: cond then else
                assert narg == 3
                line.append(f'{cmd_name}[{fmt_exp(yenv, args[0], exp_data, True, enc)}]')
            case 'ELSE':
                assert narg == 0
                line.append('ELSE[]')
            case 'LOOP':  # LOOP: SET=times loopend:L
                assert narg == 2
                rhsv = str(get_ins(args[0], exp_data, enc))
                if rhsv == '[(u8:-0x1=-1)]':  # depends on Ins.__repr__
                    line.append(f'LOOP[]')
                else:
                    cond = fmt_exp(yenv, args[0], exp_data, True, enc)
                    line.append(f'LOOP[SET={cond}]')
            case x if x in ASSIGN:  # ASSIGN: lhs ?= rhs
                assert narg == 2
                lhs = fmt_exp(yenv, args[0], exp_data, True, enc)
                rhs = fmt_exp(yenv, args[1], exp_data, True, enc)
                if x != 'LET':
                    assert args[0].ari == 0
                    lhsi = get_ins(args[0], exp_data, enc)
                    lhs0 = lhsi[0]
                    assert (lhs0.op == 'var' and len(lhsi) == 1) or lhs0.op == 'idxbeg'
                    lhs_varid = lhs0.arg >> 8  # xxxx40/20
                    str_noinit = vinits.get(lhs_varid) == []
                    rhsv = str(get_ins(args[1], exp_data, enc))
                    num_noinit = rhsv == '[(u64:0x0=0)]'  # Ins.__repr__
                    if str_noinit or num_noinit:  # what about FLT?
                        line.append(f'{x}[{lhs}]')
                    else:
                        line.append(f'{x}[{lhs}={rhs}]')
                else:
                    line.append(f'{lhs}{ARI[args[0].ari]}{rhs}')
            case 'WORD':
                assert len(args) == 1
                w = args[0]
                assert len(word := exp_data[w.off:w.off+w.len]) == w.len
                line.append(word.decode(enc))
            case 'END' if pc+1 == len(ystb.cmds): assert narg == 0
            case _:
                cmd_segs: list[str] = []
                des_args = cmd_desc.args
                for arg in cmd.args:
                    arg_desc = des_args[arg.id]
                    arg_name = arg_desc.name
                    assert (anl := len(arg_name)) > 0 or arg.ari == 0
                    arg_exp = fmt_exp(yenv, arg, exp_data, False, enc)
                    if anl == 0:
                        cmd_segs.append(arg_exp)
                    else:
                        cmd_segs.append(arg_name+ARI[arg.ari]+arg_exp)
                line.append(f'{cmd_name}[{' '.join(cmd_segs)}]')
    # 3. write lines
    nl = len(lines)-1
    for il, line in enumerate(lines):
        if line:
            f.write(';'.join(line))
        f.write('\n') if il < nl else None


def fmt_exp(yenv: YEnv, arg: Arg, exp_data: bytes, force_exp: bool, enc: str):
    assert len(raw_data := exp_data[arg.off:arg.off+arg.len]) == arg.len
    if arg.typ == 0 and not force_exp:
        return repr(raw_data.decode(enc))
    ins_list = Ins.parse_buf(raw_data, enc)
    return yenv.eval(ins_list, enc)


def get_ins(arg: Arg, exp_data: bytes, enc: str):
    assert len(raw_data := exp_data[arg.off:arg.off+arg.len]) == arg.len
    return Ins.parse_buf(raw_data, enc)


__all__ = ['disasm']
