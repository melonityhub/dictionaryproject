# -*- coding: utf-8 -*-
"""
اجرای بسته‌ی ترجمه‌ی عصبی آفلاین گوگل (فرمت ML Kit: *.bipe + resources/*) با مفسر TFLite.

خط لوله (نقش هر فایل از روی نام تنسورها و شکل‌ها فهمیده شده):

  متن ──preprocess──► توکن‌ها (SentencePiece-like، src_wpm_model.vocab)
     encoder_embed_ids_0      : جدول embedding (6000×192) — شناسه ← بردار ۱۹۲تایی
     encoder_swizzled_birnn_0 : لایه‌ی ۱ BiLSTM  (fwd + bak در یک فراخوانی، یک گام زمانی)
     encoder_swizzled_birnn_1 : لایه‌ی ۲ BiLSTM  (ورودی ۳۸۴ = الحاق fwd/bak لایه‌ی قبل)
     encoder_swizzled_birnn_2 : پروژکشن نهایی ۳۸۴→۱۹۲ (tanh) ⇒ src_enc  [۷۲, ۴, ۱۹۲]
     decoder_init_0           : آماده‌سازی توجه (attention) از src_enc
     decoder_step_embed_ids_0 : embedding توکن قبلی (4000×192)
     decoder_step_0           : یک گام LSTM دولایه + توجه ⇒ log_probs [۸, ۴۰۰۰]
  beam search بیرون از مدل (روی CPU، همین‌جا) انجام می‌شود.

شکل‌های ثابت مدل: طول منبع ۷۲ توکن، batch=۴، ۸ فرضیه (hypothesis).
همه‌ی فعال‌سازی‌ها uint8 (zero-point=128، scale=1/128) و حالت سلول‌ها int16 هستند؛
بین مدل‌ها همان بایت‌های خام بدون dequantize رد و بدل می‌شود.
"""
import os
import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from .bipe import load_bipe_file, build_tflite
from .textproc import (UnigramTokenizer, preprocess, detokenize_en, detokenize_fa)

T_MAX = 72      # حداکثر طول منبع (شکل ثابت مدل)
B = 4           # batch ثابت مدل
H = 8           # تعداد فرضیه‌ها (hypotheses) ثابت مدل
D = 192
VT = 4000       # اندازه‌ی واژگان مقصد
ZP = 128        # zero-point فعال‌سازی‌ها


def _make_interpreter(model_bytes: bytes):
    """مفسر TFLite از اولین بسته‌ی موجود؛ delegate پیش‌فرض (XNNPACK) خاموش است
    چون روی چند گره‌ی TRANSPOSE این مدل‌ها شکست می‌خورد."""
    last = None
    for modname in ('ai_edge_litert.interpreter', 'tflite_runtime.interpreter', 'tensorflow.lite.python.interpreter'):
        try:
            mod = __import__(modname, fromlist=['Interpreter'])
            Interpreter = mod.Interpreter
            kwargs = {}
            ort = getattr(mod, 'OpResolverType', None)
            if ort is not None:
                kwargs['experimental_op_resolver_type'] = ort.BUILTIN_WITHOUT_DEFAULT_DELEGATES
            it = Interpreter(model_content=model_bytes, **kwargs)
            it.allocate_tensors()
            return it
        except Exception as e:  # noqa
            last = e
    raise RuntimeError('هیچ مفسر TFLite کار نکرد. «pip install ai-edge-litert» را اجرا کنید.\n' + str(last))


class BipeModel:
    def __init__(self, path: str):
        prog = load_bipe_file(path)
        self.name = prog.name
        self.it = _make_interpreter(build_tflite(prog))
        ins = {d['name']: d for d in self.it.get_input_details()}
        outs = {d['name']: d for d in self.it.get_output_details()}
        self.in_idx = {short: (ins[full]['index'], ins[full]['dtype']) for short, full in prog.inputs}
        self.out_idx = {short: outs[full]['index'] for short, full in prog.outputs}

    def run(self, **kw) -> Dict[str, np.ndarray]:
        for k, v in kw.items():
            idx, dt = self.in_idx[k]
            self.it.set_tensor(idx, np.ascontiguousarray(v, dtype=dt))
        self.it.invoke()
        return {k: self.it.get_tensor(i).copy() for k, i in self.out_idx.items()}


# --- پارس دستی translation_model.pb / processor_spec.pb (protobuf wire format) ---

def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1
        r |= (c & 0x7f) << s; s += 7
        if not c & 0x80:
            return r, i


def parse_pb(b: bytes) -> List[tuple]:
    """فهرست (field, wiretype, value) — بازگشتی برای پیام‌های تو در تو (اگر معتبر باشند)."""
    i = 0; out = []
    while i < len(b):
        k, i = _varint(b, i)
        f, w = k >> 3, k & 7
        if w == 0:
            v, i = _varint(b, i)
        elif w == 1:
            v = b[i:i + 8]; i += 8
        elif w == 5:
            v = b[i:i + 4]; i += 4
        elif w == 2:
            l, i = _varint(b, i); v = b[i:i + l]; i += l
        else:
            raise ValueError('wire type')
        out.append((f, w, v))
    return out


class ModelSpec:
    """محتوای translation_model.pb: زبان‌ها، مسیر vocab ها و فایل‌های مدل."""

    def __init__(self, folder: str):
        raw = open(os.path.join(folder, 'translation_model.pb'), 'rb').read()
        top = parse_pb(raw)
        self.src_lang = next(v for f, w, v in top if f == 1).decode()
        self.tgt_lang = next(v for f, w, v in top if f == 2).decode()
        self.files: Dict[str, str] = {}
        for f, w, v in top:
            if f == 5:
                m = {ff: vv for ff, ww, vv in parse_pb(v)}
                self.files[m[1].decode()] = m[2].decode()
        f4 = parse_pb(next(v for f, w, v in top if f == 4))
        src = parse_pb(next(v for f, w, v in f4 if f == 1))
        tgt = parse_pb(next(v for f, w, v in f4 if f == 6))
        self.src_model = next(v for f, w, v in src if f == 1).decode()
        self.src_vocab = next(v for f, w, v in src if f == 2).decode()
        self.tgt_model = next(v for f, w, v in tgt if f == 1).decode()
        self.tgt_vocab = next(v for f, w, v in tgt if f == 2).decode()


class OfflineNMT:
    """مترجم آفلاین یک جهت (مثلاً fa→en) از روی پوشه‌ی بسته‌ی گوگل."""

    def __init__(self, folder: str, beam: int = 4, alpha: float = 0.6, residual: str = 'none'):
        self.folder = folder
        self.spec = ModelSpec(folder)
        self.beam = max(1, min(beam, H))
        self.alpha = alpha
        self.residual = residual
        self.src_tok = UnigramTokenizer(os.path.join(folder, self.spec.src_vocab))
        self.tgt_tok = UnigramTokenizer(os.path.join(folder, self.spec.tgt_vocab))
        load = lambda n: BipeModel(os.path.join(folder, self.spec.files[n]))
        self.enc_embed = load('encoder_embed_ids_0')
        self.enc_l = [load('encoder_swizzled_birnn_0'), load('encoder_swizzled_birnn_1')]
        self.enc_proj = load('encoder_swizzled_birnn_2')
        self.dec_init = load('decoder_init_0')
        self.dec_embed = load('decoder_step_embed_ids_0')
        self.dec_step = load('decoder_step_0')

    # ---------------------------------------------------------------- انکودر
    def encode(self, ids: List[int]):
        L = len(ids)
        assert 0 < L <= T_MAX
        tok = np.zeros((T_MAX, B), np.int32)
        tok[:L, :] = np.array(ids, np.int32)[:, None]
        pad = np.zeros((T_MAX, B), np.uint8)
        pad[L:, :] = 255                       # 255/255 = 1.0 ⇒ «پَد»
        emb = np.empty((T_MAX, B, D), np.uint8)
        for t in range(T_MAX):
            emb[t] = self.enc_embed.run(input=tok[t].reshape(1, B))['output'].reshape(B, D)
        feats = emb
        outs_f = outs_b = None
        for li, m in enumerate(self.enc_l):
            of = np.empty((T_MAX, B, D), np.uint8)
            ob = np.empty((T_MAX, B, D), np.uint8)
            zc = np.zeros((B, D), np.int16)
            zm = np.full((B, D), ZP, np.uint8)
            sf = (zm.copy(), zc.copy()); sb = (zm.copy(), zc.copy())
            for t in range(T_MAX):
                u = T_MAX - 1 - t
                if li == 0:
                    xin_f, xin_b = feats[t].reshape(1, B, D), feats[u].reshape(1, B, D)
                else:
                    xin_f = np.concatenate([outs_f[t], outs_b[t]], axis=-1).reshape(1, B, 2 * D)
                    xin_b = np.concatenate([outs_f[u], outs_b[u]], axis=-1).reshape(1, B, 2 * D)
                r = m.run(**{
                    'input_fwd': xin_f, 'input_bak': xin_b,
                    'padding_fwd': pad[t].reshape(1, B, 1), 'padding_bak': pad[u].reshape(1, B, 1),
                    'encoder_state:fwd_rnn_m:00': sf[0], 'encoder_state:fwd_rnn_c:00': sf[1],
                    'encoder_state:bak_rnn_m:00': sb[0], 'encoder_state:bak_rnn_c:00': sb[1],
                })
                of[t] = r['output_fwd'].reshape(B, D)
                ob[u] = r['output_bak'].reshape(B, D)
                sf = (r['encoder_state:fwd_rnn_m:00'], r['encoder_state:fwd_rnn_c:00'])
                sb = (r['encoder_state:bak_rnn_m:00'], r['encoder_state:bak_rnn_c:00'])
            outs_f, outs_b = of, ob
        enc = np.empty((T_MAX, B, D), np.uint8)
        for t in range(T_MAX):
            x = np.concatenate([outs_f[t], outs_b[t]], axis=-1).reshape(1, B, 2 * D)
            r = self.enc_proj.run(input_fwd=x, padding_fwd=pad[t].reshape(1, B, 1))
            enc[t] = list(r.values())[0].reshape(B, D)
        return enc, pad

    # ---------------------------------------------------------------- دیکودر + beam
    def decode(self, enc, pad, max_steps: Optional[int] = None):
        ri = self.dec_init.run(src_enc=enc, src_enc_padding=pad)
        src_ctx = ri['atten_init:source_contexts:00']
        src_pad = ri['atten_init:source_padding:00']
        src_vec = ri['atten_init:source_vecs:00']
        zm = np.full((H, D), ZP, np.uint8)
        zc = np.zeros((H, D), np.int16)
        st = {
            'beam_state:atten_context:00': ri['beam_state:atten_context:00'],
            'beam_state:rnn_state_0_c:00': zc.copy(), 'beam_state:rnn_state_0_m:00': zm.copy(),
            'beam_state:rnn_state_1_c:00': zc.copy(), 'beam_state:rnn_state_1_m:00': zm.copy(),
        }
        K = self.beam
        Lsrc = int((pad[:, 0] == 0).sum())
        if max_steps is None:
            max_steps = min(T_MAX + 10, int(Lsrc * 2 + 10))
        hyps = [[self.tgt_tok.bos_id]] + [[self.tgt_tok.bos_id]] * 0
        scores = np.array([0.0])
        prev_ids = np.full((H, 1), self.tgt_tok.bos_id, np.int32)
        finished: List[Tuple[float, List[int]]] = []
        active = [(0.0, [self.tgt_tok.bos_id])]
        order = list(range(1))            # slot ↔ فرضیه‌ی فعال
        for step in range(max_steps):
            ids = np.full((H, 1), self.tgt_tok.bos_id, np.int32)
            for slot, (_, seq) in enumerate(active):
                ids[slot, 0] = seq[-1]
            emb = self.dec_embed.run(step_ids=ids)['embs']
            r = self.dec_step.run(**{
                'atten_init:source_contexts:00': src_ctx, 'atten_init:source_padding:00': src_pad,
                'atten_init:source_vecs:00': src_vec, **st, 'embs': emb})
            lp = (r['log_probs'].astype(np.float32) - 255.0) * 0.0625          # (H, VT)
            cands = []
            for slot, (sc, seq) in enumerate(active):
                row = lp[slot].copy()
                row[self.tgt_tok.bos_id] = -1e9
                row[self.tgt_tok.unk_id] -= 0.0
                top = np.argpartition(-row, K)[:K * 2]
                for tkn in top:
                    cands.append((sc + float(row[tkn]), slot, int(tkn)))
            cands.sort(key=lambda x: -x[0])
            new_active = []; src_slots = []
            for sc, slot, tkn in cands:
                seq = active[slot][1] + [tkn]
                if tkn == self.tgt_tok.eos_id:
                    finished.append((sc, seq))
                else:
                    new_active.append((sc, seq)); src_slots.append(slot)
                if len(new_active) >= K:
                    break
            # شرط توقف: بهترین تمام‌شده از بهترین فعال (با نرمال‌سازی) بهتر باشد
            def norm(sc, seq):
                lpn = ((5 + len(seq) - 1) / 6.0) ** self.alpha
                return sc / lpn
            if finished and (not new_active or max(norm(s, q) for s, q in finished) >=
                             max(norm(s, q) for s, q in new_active)) and len(finished) >= K:
                break
            if not new_active:
                break
            # مرتب‌سازی حالت‌ها بر اساس فرضیه‌های جدید
            def reorder(a):
                out = a.copy()
                for new_slot, old in enumerate(src_slots):
                    out[new_slot] = a[old]
                return out
            st = {k: reorder(r[k]) for k in st}
            active = new_active
        if not finished:
            finished = [(sc, seq + [self.tgt_tok.eos_id]) for sc, seq in active]
        best = max(finished, key=lambda x: x[0] / (((5 + len(x[1]) - 1) / 6.0) ** self.alpha))
        return [t for t in best[1] if t > 2]

    # ---------------------------------------------------------------- API
    def translate_sentence(self, text: str) -> str:
        pre = preprocess(text)
        if not pre:
            return ''
        ids = self.src_tok.encode(pre)[:T_MAX - 1] + [self.src_tok.eos_id]
        enc, pad = self.encode(ids)
        out = self.decode(enc, pad)
        s = self.tgt_tok.decode_pieces(out)
        return detokenize_en(s) if self.spec.tgt_lang == 'en' else detokenize_fa(s)
