# -*- coding: utf-8 -*-
"""
پیش‌پردازش / توکنایز / پس‌پردازش متن برای بسته‌ی ترجمه‌ی آفلاین.

نکته‌ی صداقت: فایل processor_spec.pb فقط *نام* پیش‌پردازنده‌ها را دارد
(upp_offline، b2a:mode=tokenize، lc) و کد آن‌ها داخل کتابخانه‌ی بومی ML Kit است.
رفتار آن‌ها این‌جا از روی «واژگان مدل» بازسازی شده، نه کپی از کد اصلی:
  • علائم نگارشی به‌صورت واژه‌ی جدا در vocab هستند (▁. ▁, ▁? ...) ⇒ tokenize
  • در vocab مبدأ ارقام فقط ASCII هستند، نیم‌فاصله و ؟ ، ؛ وجود ندارند
    ⇒ ارقام/علائم فارسی به ASCII و نیم‌فاصله به فاصله تبدیل می‌شود.
"""
import math
import re
import unicodedata
from typing import Dict, List, Tuple

SP = '\u2581'  # ▁

_DIGITS = {ord(c): str(i) for i, c in enumerate('۰۱۲۳۴۵۶۷۸۹')}
_DIGITS.update({ord(c): str(i) for i, c in enumerate('٠١٢٣٤٥٦٧٨٩')})
_PUNCT_FA = {ord('؟'): '?', ord('،'): ',', ord('؛'): ';', ord('٪'): '%', ord('٫'): '.', ord('٬'): ',',
             ord('ي'): 'ی', ord('ى'): 'ی', ord('ك'): 'ک', ord('ـ'): None,
             0x200c: ' ', 0x200d: None, 0x200f: None, 0x200e: None, 0x202a: None, 0x202b: None,
             0x202c: None, 0x202d: None, 0x202e: None, 0xfeff: None}
for cp in range(0x064B, 0x0653):      # اعراب
    _PUNCT_FA[cp] = None

# هر نویسه‌ی غیر حرف/عدد/فاصله یک «واژه»ی مستقل می‌شود (حالت tokenize)
_TOKENIZE_RE = re.compile(r"([^\w\s]|_)", re.UNICODE)


def preprocess(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    text = text.translate(_DIGITS).translate(_PUNCT_FA)
    text = _TOKENIZE_RE.sub(r' \1 ', text)
    return ' '.join(text.split())


class UnigramTokenizer:
    """Viterbi روی مدل unigram (مثل SentencePiece) با واژگان فایل .vocab (امتیازها احتمال‌اند → log)."""

    def __init__(self, vocab_path: str):
        self.pieces: List[str] = []
        scores: List[float] = []
        with open(vocab_path, encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line:
                    continue
                p, s = line.rsplit('\t', 1)
                self.pieces.append(p)
                scores.append(float(s))
        self.unk_id, self.bos_id, self.eos_id = 0, 1, 2
        self.piece_to_id: Dict[str, int] = {}
        self.logp: Dict[str, float] = {}
        real = []
        for i, (p, s) in enumerate(zip(self.pieces, scores)):
            if i <= 2:                       # <unk> <s> </s>
                continue
            lp = math.log(s) if s > 0 else -30.0
            self.piece_to_id[p] = i
            self.logp[p] = lp
            real.append(lp)
        self.unk_score = (min(real) if real else -20.0) - 10.0
        self.maxlen = max(len(p) for p in self.piece_to_id)

    def encode(self, text: str) -> List[int]:
        text = SP + text.replace(' ', SP)
        n = len(text)
        best = [-1e18] * (n + 1)
        back: List[Tuple[int, int]] = [(0, -1)] * (n + 1)   # (start, id or -1=unk)
        best[0] = 0.0
        for i in range(n):
            if best[i] <= -1e17:
                continue
            found = False
            for j in range(i + 1, min(n, i + self.maxlen) + 1):
                sub = text[i:j]
                pid = self.piece_to_id.get(sub)
                if pid is not None:
                    found = True
                    sc = best[i] + self.logp[sub]
                    if sc > best[j]:
                        best[j] = sc
                        back[j] = (i, pid)
            if not found or True:
                sc = best[i] + self.unk_score
                if sc > best[i + 1]:
                    best[i + 1] = sc
                    back[i + 1] = (i, -1)
        out: List[int] = []
        j = n
        while j > 0:
            i, pid = back[j]
            out.append(self.unk_id if pid < 0 else pid)
            j = i
        out.reverse()
        merged: List[int] = []
        for t in out:                         # ادغام <unk>های پشت‌سرهم
            if t == self.unk_id and merged and merged[-1] == self.unk_id:
                continue
            merged.append(t)
        return merged

    def decode_pieces(self, ids: List[int]) -> str:
        s = ''.join(self.pieces[i] for i in ids if i > 2)
        return s.replace(SP, ' ').strip()


# ---------------- پس‌پردازش خروجی انگلیسی (detokenize) ----------------

_EN_CONTR = ("'s", "n't", "'ve", "'m", "'re", "'ll", "'d")


def detokenize_en(text: str) -> str:
    t = text
    t = re.sub(r"\s+([.,;:!?%)\]}])", r"\1", t)
    t = re.sub(r"([(\[{$#@])\s+", r"\1", t)
    t = re.sub(r"\s+(n't|'s|'ve|'m|'re|'ll|'d)\b", r"\1", t)
    t = re.sub(r"\b(\w+) n'\s*t\b", r"\1n't", t)
    # گیومه‌ی راست‌خط: جفت‌جفت به هم می‌چسبند
    def fix_quotes(s, q):
        parts = s.split(q)
        if len(parts) < 3:
            return s
        out = parts[0]
        for k in range(1, len(parts)):
            seg = parts[k]
            if k % 2 == 1:
                out += q + seg.lstrip()
            else:
                out = out.rstrip() + q + seg
        return out
    t = fix_quotes(t, '"')
    t = re.sub(r"\s+-\s+", " - ", t)
    return ' '.join(t.split())


def detokenize_fa(text: str) -> str:
    t = text
    t = re.sub(r"\s+([.,;:!?%)\]}»])", r"\1", t)
    t = re.sub(r"([(\[{«])\s+", r"\1", t)
    return ' '.join(t.split())
