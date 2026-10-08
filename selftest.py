# -*- coding: utf-8 -*-
"""خودآزمایی بدون رابط گرافیکی:  python selftest.py <fastdic_plain.sqlite> <پوشه‌ی مدل‌ها>"""
import sys, time
from fastdic_desktop.db import FDDatabase, pe_to_number
from fastdic_desktop.translator import OfflineTranslatorService

db_path, models = sys.argv[1], sys.argv[2]
db = FDDatabase(db_path)
rows = db.q("SELECT persian_word, word_in_number FROM persian_words LIMIT 20000")
bad = [(w, n) for w, n in ((r['persian_word'], r['word_in_number']) for r in rows) if pe_to_number(w) != n]
print('[DB] word_in_number: %d بررسی، %d اختلاف' % (len(rows), len(bad)))
print('[DB] جستجوی «a»:', [x['word'] for x in db.search('a', 3)])
svc = OfflineTranslatorService(models)
print('[مترجم] بسته‌ها:', svc.available())
for s in ('من به مدرسه می‌روم.', 'هوا امروز خیلی خوب است.'):
    t = time.time(); r, e, d = svc.translate(s); print('[مترجم]', s, '→', r or e, '(%.2fs)' % (time.time() - t))
