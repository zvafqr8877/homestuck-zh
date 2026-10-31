# -*- coding: utf-8 -*-
"""最小 SWF 讀寫工具：解壓、切成 tag、重組、壓縮。只處理 CWS/FWS。"""
import struct, zlib


def read_swf(path):
    b = open(path, "rb").read()
    sig = b[:3]
    if sig == b"CWS":
        body = zlib.decompress(b[8:])
    elif sig == b"FWS":
        body = b[8:]
    else:
        raise ValueError("不支援的 SWF 格式 " + repr(sig))
    ver = b[3]
    nb = body[0] >> 3
    hlen = (5 + nb * 4 + 7) // 8
    header = body[:hlen + 4]          # RECT + frame rate + frame count
    tags = []
    p = hlen + 4
    while p < len(body):
        h = struct.unpack_from("<H", body, p)[0]; p += 2
        code, ln = h >> 6, h & 63
        if ln == 63:
            ln = struct.unpack_from("<I", body, p)[0]; p += 4
        tags.append([code, body[p:p + ln]])
        p += ln
        if code == 0:
            break
    return ver, header, tags


def write_swf(path, ver, header, tags, compress=True):
    out = bytearray(header)
    for code, data in tags:
        ln = len(data)
        if ln < 63 and code != 0 or (code == 0 and ln == 0):
            out += struct.pack("<H", (code << 6) | ln)
        else:
            out += struct.pack("<HI", (code << 6) | 63, ln)
        out += data
    body = bytes(out)
    total = 8 + len(body)
    if compress:
        open(path, "wb").write(b"CWS" + bytes([ver]) + struct.pack("<I", total) + zlib.compress(body, 9))
    else:
        open(path, "wb").write(b"FWS" + bytes([ver]) + struct.pack("<I", total) + body)


def cstr(d, q):
    e = d.index(0, q)
    return d[q:e].decode("utf-8", "replace"), e + 1


def rect_end(d, q):
    n = d[q] >> 3
    return q + (5 + n * 4 + 7) // 8


def parse_edit(d):
    """DefineEditText -> dict（含各欄位位置，方便改寫）"""
    q = 0
    cid = struct.unpack_from("<H", d, q)[0]; q += 2
    rs = q; q = rect_end(d, q); bounds = d[rs:q]
    f1, f2 = d[q], d[q + 1]; q += 2
    r = dict(id=cid, bounds=bounds, f1=f1, f2=f2, font=None, fclass=None, fh=None)
    if f1 & 1:
        r["font"] = struct.unpack_from("<H", d, q)[0]; q += 2
        if f2 & 0x80:
            r["fclass"], q = cstr(d, q)
        r["fh"] = struct.unpack_from("<H", d, q)[0]; q += 2
    elif f2 & 0x80:
        r["fclass"], q = cstr(d, q)
    r["color"] = d[q:q + 4] if f1 & 4 else None
    if f1 & 4: q += 4
    r["maxlen"] = struct.unpack_from("<H", d, q)[0] if f1 & 2 else None
    if f1 & 2: q += 2
    r["layout"] = d[q:q + 9] if f2 & 0x20 else None
    if f2 & 0x20: q += 9
    r["var"], q = cstr(d, q)
    r["text"] = ""
    if f1 & 0x80:
        r["text"], q = cstr(d, q)
    return r


def build_edit(r):
    f1, f2 = r["f1"], r["f2"]
    out = struct.pack("<H", r["id"]) + r["bounds"] + bytes([f1, f2])
    if f1 & 1:
        out += struct.pack("<H", r["font"])
        if f2 & 0x80:
            out += r["fclass"].encode() + b"\0"
        out += struct.pack("<H", r["fh"])
    elif f2 & 0x80:
        out += r["fclass"].encode() + b"\0"
    if f1 & 4: out += r["color"]
    if f1 & 2: out += struct.pack("<H", r["maxlen"])
    if f2 & 0x20: out += r["layout"]
    out += r["var"].encode() + b"\0"
    if f1 & 0x80:
        out += r["text"].encode("utf-8") + b"\0"
    return out


def parse_static(d, code):
    """DefineText(11)/DefineText2(33) -> 第一段文字的位置/顏色/大小（用來換成 DefineEditText）"""
    cid = struct.unpack_from("<H", d, 0)[0]
    q = rect_end(d, 2)
    bits = "".join(f"{b:08b}" for b in d[q:q + 40])
    pos = 0
    def rb(n):
        nonlocal pos
        v = int(bits[pos:pos + n] or "0", 2); pos += n; return v
    def sb(n):
        v = rb(n); return v - (1 << n) if n and v >= (1 << (n - 1)) else v
    if rb(1):
        n = rb(5); rb(n); rb(n)
    if rb(1):
        n = rb(5); rb(n); rb(n)
    n = rb(5); tx, ty = sb(n), sb(n)
    q += (pos + 7) // 8
    q += 2                       # glyph bits / advance bits
    f = d[q]; q += 1
    font = struct.unpack_from("<H", d, q)[0]; q += 2
    nc = 4 if code == 33 else 3
    col = d[q:q + 3]; q += nc
    xo = yo = 0
    if f & 1: xo = struct.unpack_from("<h", d, q)[0]; q += 2
    if f & 2: yo = struct.unpack_from("<h", d, q)[0]; q += 2
    h = struct.unpack_from("<H", d, q)[0]
    return dict(id=cid, tx=tx, ty=ty, color=bytes(col), xo=xo, yo=yo, h=h)
