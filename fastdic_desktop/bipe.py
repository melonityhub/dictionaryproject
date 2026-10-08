# -*- coding: utf-8 -*-
"""
خواندن فایل‌های .bipe (کانتینر FlatBuffer با شناسه‌ی «BIPE») بسته‌ی ترجمه‌ی آفلاین ML Kit.

ساختار (به‌دست‌آمده با مهندسی معکوس، نه از مستندات رسمی):

  ریشه (Root)
   ├─ slot0 : نام مدل (مثلاً "encoder_embed_ids_0")
   └─ slot1 : وکتور Program
        ├─ slot0 : نام
        ├─ slot1 : {"tflite", "generic", ...}  توصیف موتور اجرا
        ├─ slot2 : وکتور Segment (یکی)
        │     ├─ slot1 : ورودی‌ها  [(نام کوتاه, نام تنسور در گراف)]
        │     ├─ slot2 : خروجی‌ها  [(نام کوتاه, نام تنسور در گراف)]
        │     ├─ slot5 : {"tflite_flatbuffer", <بایت‌های مدل TFLite — بدون وزن‌ها>}
        │     └─ slot6 : جدول نگاشت [(slot0 = شماره‌ی بلوب (پیش‌فرض 0), slot1 = شماره‌ی تنسور TFLite)]
        └─ slot3 : وکتور بلوب‌های وزن (هر کدام یک آرایه‌ی بایت)

مدل TFLite داخل فایل «وزن‌هایش خالی» است؛ هنگام بارگذاری، بلوب‌ها طبق جدول نگاشت
داخل بافر تنسور مربوطه گذاشته می‌شوند. این ماژول دقیقاً همین کار را انجام می‌دهد.
"""
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def _u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def _i32(b, o):
    return struct.unpack_from('<i', b, o)[0]


def _u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def _fpos(b, table, slot):
    """آدرس مطلق فیلد slot در جدول FlatBuffer (یا None اگر نبود)."""
    vt = table - _i32(b, table)
    vsize = _u16(b, vt)
    n = (vsize - 4) // 2
    if slot >= n:
        return None
    off = _u16(b, vt + 4 + 2 * slot)
    return table + off if off else None


def _deref(b, pos):
    return pos + _u32(b, pos)


def _vec_tables(b, pos):
    v = _deref(b, pos)
    n = _u32(b, v)
    return [v + 4 + 4 * i + _u32(b, v + 4 + 4 * i) for i in range(n)]


def _read_str(b, pos):
    t = _deref(b, pos)
    return bytes(b[t + 4:t + 4 + _u32(b, t)]).decode('utf-8')


def _read_bytes(b, pos):
    v = _deref(b, pos)
    n = _u32(b, v)
    return bytes(b[v + 4:v + 4 + n])


@dataclass
class BipeProgram:
    name: str
    tflite: bytes                      # مدل TFLite بدون وزن
    inputs: List[Tuple[str, str]]
    outputs: List[Tuple[str, str]]
    mapping: List[Tuple[int, int]]     # (blob_index, tensor_index)
    blobs: List[bytes] = field(default_factory=list)


def parse_bipe(data: bytes) -> BipeProgram:
    if data[4:8] != b'BIPE':
        raise ValueError('امضای BIPE پیدا نشد')
    root = _u32(data, 0)
    prog = _vec_tables(data, _fpos(data, root, 1))[0]
    name = _read_str(data, _fpos(data, prog, 0))
    seg = _vec_tables(data, _fpos(data, prog, 2))[0]

    tf_tab = _deref(data, _fpos(data, seg, 5))
    tflite = _read_bytes(data, _fpos(data, tf_tab, 1))

    def io(slot):
        pos = _fpos(data, seg, slot)
        res = []
        if pos is None:
            return res
        for e in _vec_tables(data, pos):
            res.append((_read_str(data, _fpos(data, e, 0)), _read_str(data, _fpos(data, e, 3))))
        return res

    mapping = []
    mpos = _fpos(data, seg, 6)
    if mpos is not None:
        for e in _vec_tables(data, mpos):
            p0, p1 = _fpos(data, e, 0), _fpos(data, e, 1)
            mapping.append((data[p0] if p0 else 0, _u32(data, p1)))

    blobs = []
    bpos = _fpos(data, prog, 3)
    if bpos is not None:
        for e in _vec_tables(data, bpos):
            blobs.append(_read_bytes(data, _fpos(data, e, 0)))

    return BipeProgram(name, tflite, io(1), io(2), mapping, blobs)


# ----- پچ کردن بافرهای TFLite (بدون نیاز به کتابخانه‌ی tflite) -----------------

def _tensor_buffer_index(tfl: bytes, tensor_idx: int) -> int:
    root = _u32(tfl, 0)
    sg = _vec_tables(tfl, _fpos(tfl, root, 2))[0]            # Model.subgraphs[0]
    t = _vec_tables(tfl, _fpos(tfl, sg, 0))[tensor_idx]       # SubGraph.tensors[i]
    p = _fpos(tfl, t, 2)                                      # Tensor.buffer (uint32)
    return _u32(tfl, p) if p else 0


def _buffers_vector(tfl: bytes) -> int:
    root = _u32(tfl, 0)
    return _deref(tfl, _fpos(tfl, root, 4))                   # Model.buffers


def build_tflite(p: BipeProgram) -> bytes:
    """وزن‌ها را در بافر تنسورها می‌گذارد و یک مدل کامل TFLite برمی‌گرداند.

    FlatBuffer مستقل از موقعیت است؛ بنابراین برای هر بافر یک جدول Buffer تازه
    (+ وکتور داده) به انتهای فایل اضافه می‌کنیم و فقط اشاره‌گر درایه‌ی مربوطه در
    وکتور buffers را عوض می‌کنیم. (uoffset همیشه رو به جلو است ⇒ معتبر.)
    """
    out = bytearray(p.tflite)
    vec = _buffers_vector(p.tflite)
    for blob_idx, tensor_idx in p.mapping:
        data = p.blobs[blob_idx]
        buf_idx = _tensor_buffer_index(p.tflite, tensor_idx)
        # vtable (6 بایت + 2 بایت پد) سپس جدول (soffset + uoffset)
        while (len(out) + 8) % 4:
            out.append(0)
        vt_pos = len(out)
        out += struct.pack('<HHH', 6, 8, 4) + b'\0\0'
        tab_pos = len(out)
        out += struct.pack('<i', tab_pos - vt_pos) + struct.pack('<I', 0)
        # وکتور داده — شروع داده روی مرز ۱۶ بایت (مثل builder رسمی TFLite)
        while (len(out) + 4) % 16:
            out.append(0)
        v_pos = len(out)
        out += struct.pack('<I', len(data)) + data
        while len(out) % 4:
            out.append(0)
        struct.pack_into('<I', out, tab_pos + 4, v_pos - (tab_pos + 4))
        elem = vec + 4 + 4 * buf_idx
        struct.pack_into('<I', out, elem, tab_pos - elem)
    return bytes(out)


def load_bipe_file(path: str) -> BipeProgram:
    with open(path, 'rb') as f:
        return parse_bipe(f.read())
