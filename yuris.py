#!/bin/env python3
from io import RawIOBase
from struct import Struct
ENC = 'shift-jis'
Tf64 = Struct('<d')
Tu32x2 = Struct('<2I')
Tu32x3 = Struct('<3I')
Tu32x7 = Struct('<7I')


class Rdr:
    idx: int
    buf: bytes
    enc: str

    def __init__(self, data: bytes, enc: str):
        self.idx = 0
        self.buf = data
        self.enc = enc

    def skip(self, n: int):
        assert n > 0
        assert (j := self.idx + n) <= len(self.buf)
        self.idx = j

    def byte(self):
        b = self.buf[self.idx]
        self.idx += 1
        return b

    def read(self, n: int):
        i = self.idx
        j = i + n
        assert len(b := self.buf[i:j]) == n
        self.idx = j
        return b

    def str(self, n: int):
        return self.read(n).decode(self.enc)

    def bz(self):
        i = self.idx
        j = self.buf.index(0, i)
        self.idx = j + 1
        return self.buf[i:j]

    def sz(self):
        return self.bz().decode(self.enc)

    def ui(self, n: int):
        return int.from_bytes(self.read(n), 'little', signed=False)

    def si(self, n: int):
        return int.from_bytes(self.read(n), 'little', signed=True)

    def unpack(self, t: Struct):
        return t.unpack(self.read(t.size))


class Err:
    id: int
    msg: str

    def __init__(self, r: Rdr):
        self.id = r.ui(4)
        self.msg = r.sz()


class MArg:
    name: str
    chk_typ: int
    chk_val: int

    def __init__(self, r: Rdr):
        self.name = r.sz()
        self.chk_typ, self.chk_val = r.read(2)


class MCmd:
    name: str
    args: list[MArg]

    def __init__(self, r: Rdr):
        self.name = r.sz()
        narg = r.byte()
        self.args = [MArg(r) for _ in range(narg)]


class YSCM:
    ver: int
    pad: int
    cmds: list[MCmd]
    errs: list[str]
    b256: bytearray

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSCM'
        self.ver, ncmd, self.pad = r.unpack(Tu32x3)
        self.cmds = [MCmd(r) for _ in range(ncmd)]
        errs: list[str] = []
        end = len(r.buf) - 256
        while r.idx < end:
            errs.append(r.sz())
        assert r.idx == end
        self.errs = errs
        self.b256 = r.read(256)


Tcfg0 = Struct('<6I')
Tcfg1 = Struct('<9IH')


class YSCF:
    ver: int
    pad1: int
    compile: int
    screen_width: int
    screen_height: int
    enable: int
    image_type_slots: list[int]  # [8]
    sound_type_slots: list[int]  # [4]
    thread: int
    debug_mode: int
    sound: int
    window_resize: int
    window_frame: int
    file_priority_dev: int
    file_priority_debug: int
    file_priority_release: int
    pad2: int
    caption: str

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSCF'
        (self.ver,
         self.pad1,
         self.compile,
         self.screen_width,
         self.screen_height,
         self.enable) = r.unpack(Tcfg0)
        self.image_type_slots = list(r.read(8))
        self.sound_type_slots = list(r.read(4))
        (self.thread,
         self.debug_mode,
         self.sound,
         self.window_resize,
         self.window_frame,
         self.file_priority_dev,
         self.file_priority_debug,
         self.file_priority_release,
         self.pad2, cap_len) = r.unpack(Tcfg1)
        self.caption = r.str(cap_len)


class YSER:
    ver: int
    pad: int
    errs: list[Err]

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSER'
        self.ver, nerr, self.pad = r.unpack(Tu32x3)
        self.errs = [Err(r) for _ in range(nerr)]


TLbl = Struct('<IIHH')


class Lbl:
    name: str
    id: int
    pc: int
    scr_id: int
    pad: int

    def __init__(self, r: Rdr):
        self.name = r.str(r.byte())
        self.id, self.pc, self.scr_id, self.pad = r.unpack(TLbl)


class YSLB:
    ver: int
    lbls: list[Lbl]

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSLB'
        self.ver, nlbl = r.unpack(Tu32x2)
        r.skip(4 * 256)
        self.lbls = [Lbl(r) for _ in range(nlbl)]


class YSTD:
    ver: int
    nvar: int
    ntext: int

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSTD'
        self.ver, self.nvar, self.ntext = r.unpack(Tu32x3)


TScr = Struct('<Q3i')


class Scr:
    id: int
    path: int
    time: int
    nvar: int
    nlbl: int
    ntext: int

    def __init__(self, r: Rdr):
        self.id, path_len = r.unpack(Tu32x2)
        self.path = r.str(path_len)
        self.time, self.nvar, self.nlbl, self.ntext = r.unpack(TScr)


class YSTL:
    ver: int
    scrs: list[Scr]

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSTL'
        self.ver, nscr = r.unpack(Tu32x2)
        self.scrs = [Scr(r) for _ in range(nscr)]


TArg = Struct('<HBB2I')


class Arg:
    id: int
    typ: int
    ari: int
    len: int
    off: int

    def __init__(self, r: Rdr):
        self.id, self.typ, self.ari, self.len, self.off = r.unpack(TArg)


TCmd = Struct('<BBH')


class Cmd:
    code: int
    args: list[Arg]
    lbl_idx: int
    line_no: int

    def __init__(self, r: Rdr, r_arg: Rdr, r_lno: Rdr):
        self.code, narg, self.lbl_idx = r.unpack(TCmd)
        self.args = [Arg(r_arg) for _ in range(narg)]
        self.line_no = r_lno.ui(4)


YSTB_DEFAULT_KEY = 0xD36FAC96


def xor_trans(bs: bytearray, key: int):
    o = len(bs) & ~3
    b0, b1, b2, b3 = k = key.to_bytes(4, 'big')
    for i in range(0, o, 4):
        bs[i+0] ^= b0
        bs[i+1] ^= b1
        bs[i+2] ^= b2
        bs[i+3] ^= b3
    for j in range(len(bs) & 3):
        bs[o+j] ^= k[j]
    return bs


class YSTB:
    ver: int
    pad: int
    cmds: list[Cmd]
    data: bytearray

    def __init__(self, f: RawIOBase, key=YSTB_DEFAULT_KEY, enc=ENC):
        assert f.read(4) == b'YSTB'
        self.ver, ncmd, lcmd, larg, lexp, llno, self.pad = Tu32x7.unpack(f.read(28))
        assert ncmd * TCmd.size == lcmd
        assert larg % TArg.size == 0
        assert ncmd * 4 == llno
        assert f.readinto(d_cmd := bytearray(lcmd)) == lcmd
        assert f.readinto(d_arg := bytearray(larg)) == larg
        assert f.readinto(d_exp := bytearray(lexp)) == lexp
        assert f.readinto(d_lno := bytearray(llno)) == llno
        r_cmd = Rdr(xor_trans(d_cmd, key), enc)
        r_arg = Rdr(xor_trans(d_arg, key), enc)
        r_lno = Rdr(xor_trans(d_lno, key), enc)
        self.data = xor_trans(d_exp, key)
        self.cmds = [Cmd(r_cmd, r_arg, r_lno) for _ in range(ncmd)]


TVar454 = Struct('<BHHBB')
TVar455 = Struct('<BBHHBB')


class Var:
    scope: int
    g: int
    scr_id: int
    var_id: int
    dim: list[int]
    typ: int
    val: None | int | float | bytes

    def __init__(self, r: Rdr, v: int):
        if v > 454:
            self.scope, self.g, self.scr_id, self.var_id, self.typ, ndim = r.unpack(TVar455)
        else:
            self.scope, self.scr_id, self.var_id, self.typ, ndim = r.unpack(TVar454)
            self.g = 1
        self.dim = [r.ui(4) for _ in range(ndim)]
        assert 1 <= self.scope <= 3  # 1:g 2:s 3:f
        assert self.scope == 1 or self.g == 1, f'scope={self.scope}, g={self.g}'
        match (typ := self.typ):
            case 0: self.val = None
            case 1: self.val = r.si(8)
            case 2: self.val = r.unpack(Tf64)[0]
            case 3:
                expr_len = r.ui(2)
                self.val = r.read(expr_len)
            case x: assert False, f'unknown type: {x}'


Tysvr = Struct('<IH')


class YSVR:
    ver: int
    vars: list[Var]

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSVR'
        ver, nvar = r.unpack(Tysvr)
        self.ver = ver
        self.vars = [Var(r, ver) for _ in range(nvar)]


class DArg:
    name: str
    unk4: bytes

    def __init__(self, r: Rdr):
        self.name = r.sz()
        self.unk4 = r.read(4)


class DCmd:
    name: str
    args: list[DArg]

    def __init__(self, r: Rdr):
        self.name = r.sz()
        narg = r.byte()
        self.args = [DArg(r) for _ in range(narg)]


class DVar:
    name: str
    typ: int
    dim: list[int]

    def __init__(self, r: Rdr):
        self.name = r.sz()
        self.typ, ndim = r.read(2)
        self.dim = [r.ui(4) for _ in range(ndim)]


class YSCD:
    ver: int
    cmds: list[DCmd]
    pad1: int
    vars: list[DVar]
    pad2: int
    errs: list[Err]
    pad3: int
    yser: list[str]
    blok: list[bytes]
    pad4: int
    b800: bytes

    def __init__(self, r: Rdr):
        assert r.read(4) == b'YSCD'
        self.ver, ncmd, self.pad1 = r.unpack(Tu32x3)
        self.cmds = [DCmd(r) for _ in range(ncmd)]
        nvar, self.pad2 = r.unpack(Tu32x2)
        self.vars = [DVar(r) for _ in range(nvar)]
        nerr, self.pad3 = r.unpack(Tu32x2)
        self.errs = [Err(r) for _ in range(nerr)]
        self.yser = [r.sz() for _ in range(37)]
        blok, self.pad4 = r.unpack(Tu32x2)
        self.blok = [r.read(blok) for _ in range(blok)]
        self.b800 = r.read(0x800)


InsDesc: dict[int, tuple[int, str]] = {
    0x21: (0, '!='),
    0x25: (0, '%'),
    0x26: (0, '&&'),
    0x29: (1, 'idxend'),
    0x2A: (0, '*'),
    0x2B: (0, '+'),
    0x2C: (0, 'nop'),
    0x2D: (0, '-'),
    0x2F: (0, '/'),
    0x3C: (0, '<'),
    0x3D: (0, '=='),
    0x3E: (0, '>'),
    0x41: (0, '&'),
    0x42: (1, 'u8'),
    0x46: (8, 'f64'),
    0x48: (3, 'var'),
    0x49: (4, 'u32'),
    0x4C: (8, 'u64'),
    0x4D: (-1, 'str'),
    0x4F: (0, '|'),
    0x52: (0, 'neg'),
    0x53: (0, '<='),
    0x56: (3, 'idxbeg'),
    0x57: (2, 'u16'),
    0x5A: (0, '>='),
    0x5E: (0, '^'),
    0x69: (0, '@'),  # to_num
    0x73: (0, '$'),  # to_str
    0x76: (3, 'arr'),
    0x7C: (0, '||'),
}

TIns = Struct('<BH')


class Ins:
    op: str
    arg: None | int | float | str

    def __init__(self, r: Rdr):
        code, size = r.unpack(TIns)
        dsiz, self.op = InsDesc[code]
        assert dsiz < 0 or dsiz == size
        match code:
            case 0x46: self.arg = r.unpack(Tf64)[0]
            case 0x4d: self.arg = r.str(size)
            case x: self.arg = r.si(size) if size > 0 else None

    def __repr__(self):
        if (a := self.arg) == None:
            return self.op
        if isinstance(a, str):
            return f'({self.op}:{a})'
        if isinstance(a, int):
            return f'({self.op}:{hex(a)}={a})'
        return f'({self.op}:{a}f)'

    @classmethod
    def parse_buf(cls, b: bytes, enc: str):
        l = len(b)
        r = Rdr(b, enc)
        e: list[Ins] = []
        while r.idx < l:
            e.append(Ins(r))
        return e


VTypCh = {-1: '@', 1: '@', 2: '@', 3: '$'}
VScopeCh = {0: 'v', 1: 'g', 2: 's', 3: 'f'}
VTypName = {-1: 'Num', 1: 'Int', 2: 'Fl', 3: 'Str'}


def make_var_name(scope: int, vid: int, typ: int):
    return VScopeCh[scope] + VTypName[typ] + str(vid)


InsVTyp = {0x23: 3, 0x24: 3, 0x40: -1, 0x60: -1}
BinOps = {'*', '/', '%', '+', '-', '<', '>', '<=', '>=', '==', '!=', '&', '^', '|', '&&', '||'}
NeedSpace = {'&'}


class YEnv:
    com_vars: set[int]
    vars: dict[int, str]

    def __init__(self, yscd: YSCD, ysvr: YSVR):
        self.vars = vars = {}
        self.com_vars = set(range(len(yscd.vars)))
        for i, var in enumerate(yscd.vars):
            self.vars[i] = VTypCh[var.typ]+var.name
        for i, var in enumerate(ysvr.vars):
            if (vid := var.var_id) in vars:
                continue
            if (typ := var.typ) == 0:  # not exist
                continue
            self.fmt_var(vid, typ)

    def fmt_var(self, i: int, typ: int):
        if i in self.vars:
            assert (v := self.vars[i])[0] == VTypCh[typ]  # check type
        else:
            self.vars[i] = v = VTypCh[typ]+make_var_name(0, i, typ)
        return v

    def fmt_ins_var(self, x: int):
        match x & 255:
            case 0x23: typ, ptr = 3, '&'
            case 0x24: typ, ptr = 3, ''
            case 0x60: typ, ptr = -1, '&'
            case 0x40: typ, ptr = -1, ''
            case x: assert False, f'unknown ins var type {hex(x)}'
        return ptr+self.fmt_var(x >> 8, typ)

    def eval(self, code: list[Ins], enc: str) -> str:
        stk: list[str | None] = []
        for i, ins in enumerate(code):
            match ins.op:
                case 'nop': assert ins.arg == None
                case '$' | '@' as op: stk.append(f'{op}({stk.pop()})')
                case 'u8' | 'u16' | 'u32' | 'u64' | 'f64':
                    if (a := ins.arg) >= 0:
                        stk.append(str(a))
                    else:
                        stk.append(f'({a})')
                case 'str': stk.append(ins.arg)
                case 'var': stk.append(self.fmt_ins_var(ins.arg))
                case 'arr': stk.append(self.fmt_ins_var(ins.arg)+'()')
                case 'neg': stk.append(f'(-{stk.pop()})')
                case op if op in BinOps:
                    rhs = stk.pop()
                    if len(stk) == 0:
                        # & : as seen in 0.494's sample デバッグ定義.txt
                        # !=: as seen in some NatsuzoraAsterism's scenarios
                        assert i == len(code)-1
                        return f'{op}{rhs}'
                    lhs = stk.pop()
                    if op in NeedSpace:
                        stk.append(f'({lhs} {op} {rhs})')
                    else:
                        stk.append(f'({lhs}{op}{rhs})')
                case 'idxbeg':
                    stk.append(self.fmt_ins_var(ins.arg))
                    stk.append(None)
                case 'idxend':
                    dims: list[str] = []
                    while None != (d := stk.pop()):
                        dims.append(d)
                    stk.append(f'{stk.pop()}({','.join(reversed(dims))})')
                case _: assert False, 'unhandled: '+repr(ins)
        assert len(stk) == 1
        return stk[0]
