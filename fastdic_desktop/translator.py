# -*- coding: utf-8 -*-
"""مترجم متن آفلاین — معادل FDOfflineTranslator + منطق WordResultViewModel.handleOfflineTranslator."""
import os
import re
from typing import Dict, List, Optional, Tuple

from .db import lang_of, replace_numbers_to_farsi, to_english_number
from .nmt import OfflineNMT, T_MAX

MAX_TRANSLATOR_WORDS = 500      # ConfigConstKt.MAX_TRANSLATOR_WORDS


def discover_packages(root: str) -> Dict[str, str]:
    """پوشه‌ی root و زیرپوشه‌هایش را می‌گردد؛ هر پوشه‌ای که translation_model.pb دارد یک بسته است.
    کلید خروجی مثل «fa>en». (جهت از خود فایل translation_model.pb خوانده می‌شود.)"""
    from .nmt import ModelSpec
    found = {}
    cands = [root] + [os.path.join(root, d) for d in sorted(os.listdir(root))] if os.path.isdir(root) else []
    for c in cands:
        if os.path.isfile(os.path.join(c, 'translation_model.pb')):
            try:
                s = ModelSpec(c)
                found['%s>%s' % (s.src_lang, s.tgt_lang)] = c
            except Exception:
                pass
    return found


_SENT_SPLIT = re.compile(r'(?<=[.!?؟۔…])\s+')


class OfflineTranslatorService:
    def __init__(self, models_root: str, beam: int = 4):
        self.models_root = models_root
        self.packages = discover_packages(models_root) if models_root else {}
        self.beam = beam
        self._loaded: Dict[str, OfflineNMT] = {}

    def available(self) -> List[str]:
        return sorted(self.packages)

    def direction_for(self, text: str) -> str:
        # FDLanguageWord.getSourceAndDestLanguage: انگلیسی ⇒ en→fa ؛ غیر این ⇒ fa→en
        return 'en>fa' if lang_of(text) == 'English' else 'fa>en'

    def _model(self, direction: str) -> OfflineNMT:
        if direction not in self.packages:
            raise FileNotFoundError(direction)
        if direction not in self._loaded:
            self._loaded[direction] = OfflineNMT(self.packages[direction], beam=self.beam)
        return self._loaded[direction]

    def _chunks(self, model: OfflineNMT, line: str) -> List[str]:
        """جمله‌ها را کنار هم می‌گذارد تا هر تکه ≤ ظرفیت مدل (۷۲ توکن) باشد؛ جمله‌ی خیلی بلند را روی ویرگول/پنجره می‌شکند."""
        from .textproc import preprocess
        limit = T_MAX - 4
        ntok = lambda s: len(model.src_tok.encode(preprocess(s)))
        out, cur = [], ''
        for sent in [s for s in _SENT_SPLIT.split(line) if s.strip()]:
            parts = [sent]
            if ntok(sent) > limit:
                parts = [p for p in re.split(r'(?<=[,،;؛:])\s+', sent) if p.strip()]
                fixed = []
                for p in parts:
                    if ntok(p) > limit:                      # آخرین راه: برش بر اساس واژه
                        words, buf = p.split(), ''
                        for w in words:
                            if buf and ntok(buf + ' ' + w) > limit:
                                fixed.append(buf); buf = w
                            else:
                                buf = (buf + ' ' + w).strip()
                        if buf:
                            fixed.append(buf)
                    else:
                        fixed.append(p)
                parts = fixed
            for p in parts:
                cand = (cur + ' ' + p).strip()
                if cur and ntok(cand) > limit:
                    out.append(cur); cur = p
                else:
                    cur = cand
        if cur:
            out.append(cur)
        return out

    def translate(self, text: str) -> Tuple[Optional[str], Optional[str], str]:
        """→ (نتیجه, خطا, جهت). همان رفتار اندروید: ارقام نتیجه به زبان مقصد برگردانده می‌شود."""
        text = text.strip()
        direction = self.direction_for(text)
        if direction not in self.packages:
            return None, ('بسته‌ی ترجمه‌ی آفلاین «%s» پیدا نشد. پوشه‌ی translate_%s را در مسیر مدل‌ها بگذارید.'
                          % (direction.replace('>', '→'), direction.replace('>', ''))), direction
        model = self._model(direction)
        lines_out = []
        for line in text.split('\n'):
            if not line.strip():
                lines_out.append('')
                continue
            lines_out.append(' '.join(model.translate_sentence(c) for c in self._chunks(model, line)))
        result = '\n'.join(lines_out).strip()
        if not result:
            return None, 'ترجمه‌ای تولید نشد.', direction
        # handleOfflineTranslator$lambda$0: مقصد فارسی ⇒ ارقام فارسی ؛ مقصد انگلیسی ⇒ ارقام انگلیسی
        result = replace_numbers_to_farsi(result) if direction.endswith('fa') else to_english_number(result)
        return result, None, direction
