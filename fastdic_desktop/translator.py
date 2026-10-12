# -*- coding: utf-8 -*-
"""مترجم متن آفلاین — معادل FDOfflineTranslator + منطق WordResultViewModel.handleOfflineTranslator."""
import os
import re
from typing import Dict, List, Optional, Tuple

from .db import lang_of, replace_numbers_to_farsi, to_english_number
from .nmt import OfflineNMT, T_MAX

MAX_TRANSLATOR_WORDS = 500      # ConfigConstKt.MAX_TRANSLATOR_WORDS


def _candidate_dirs(root: str) -> List[str]:
    """ریشه + فرزندان + نوه‌ها؛ چیدمان ML Kit دو سطحی است: <root>/<pair>/translate_*/"""
    if not os.path.isdir(root):
        return []
    out = [root]
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p):
            out.append(p)
            for e in sorted(os.listdir(p)):
                p2 = os.path.join(p, e)
                if os.path.isdir(p2):
                    out.append(p2)
    return out


def discover_packages(root: str) -> Dict[str, str]:
    """پوشه‌ی root و تا دو سطح زیرپوشه‌هایش را می‌گردد؛ هر پوشه‌ای که translation_model.pb دارد
    یک بسته است. کلید خروجی مثل «fa>en» یا «en>de». (جهت از خود فایل translation_model.pb
    خوانده می‌شود؛ هم چیدمان قدیمی root/translate_faen و هم چیدمان ML Kit
    root/en_fa/translate_enfa شناسایی می‌شود.)"""
    from .nmt import ModelSpec
    found = {}
    for c in _candidate_dirs(root):
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

    def direction_for(self, text: str, target: str = 'fa') -> str:
        # FDLanguageWord.getSourceAndDestLanguage، تعمیم‌یافته به هر زبان ML Kit:
        # همهٔ مدل‌ها انگلیسی ⇄ زبان مقصد آموزش دیده‌اند؛ متن انگلیسی ⇒ en→X ؛ غیر این ⇒ X→en
        return 'en>%s' % target if lang_of(text) == 'English' else '%s>en' % target

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

    def translate(self, text: str, target: str = 'fa') -> Tuple[Optional[str], Optional[str], str]:
        """→ (نتیجه, خطا, جهت). همان رفتار اندروید: ارقام نتیجه به زبان مقصد برگردانده می‌شود.

        ``target`` زبان مقصد (مدل ML Kit) است؛ متن انگلیسی به همان زبان ترجمه می‌شود
        و متن غیرانگلیسی به انگلیسی.
        """
        text = text.strip()
        direction = self.direction_for(text, target)
        if direction not in self.packages:
            from .mlkit_models import language_name, package_info
            name = language_name(target)
            size = package_info(lang=target)['DL_SZ']
            return None, ('مدل ترجمهٔ آفلاین «%s» (%s) نصب نشده است؛ با دکمهٔ «مدل‌ها…» دانلودش کنید '
                          '(حجم دانلود: %.1f مگابایت).'
                          % (name, target, size / (1024.0 * 1024.0))), direction
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
