# -*- coding: utf-8 -*-
"""ابزار بررسی فایل‌های .bipe:  python tools/inspect_bipe.py <پوشه یا فایل> [--extract خروجی]
  • نام/ورودی‌ها/خروجی‌ها، بلوب‌های وزن و جدول نگاشت بلوب←تنسور را چاپ می‌کند
  • با --extract مدل کامل TFLite (با وزن‌های جاگذاری‌شده) را به‌صورت .tflite ذخیره می‌کند"""
import argparse, glob, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastdic_desktop.bipe import load_bipe_file, build_tflite

ap = argparse.ArgumentParser(); ap.add_argument('path'); ap.add_argument('--extract')
a = ap.parse_args()
files = sorted(glob.glob(os.path.join(a.path, '*.bipe'))) if os.path.isdir(a.path) else [a.path]
for f in files:
    p = load_bipe_file(f)
    print('=' * 70); print(os.path.basename(f), '| name =', p.name)
    print('  tflite (بدون وزن): %d بایت | بلوب‌ها: %s' % (len(p.tflite), [len(b) for b in p.blobs]))
    print('  نگاشت (blob → tensor):', p.mapping)
    print('  ورودی‌ها :', [s for s, _ in p.inputs]); print('  خروجی‌ها:', [s for s, _ in p.outputs])
    if a.extract:
        os.makedirs(a.extract, exist_ok=True)
        out = os.path.join(a.extract, os.path.basename(f).replace('.bipe', '.tflite'))
        open(out, 'wb').write(build_tflite(p)); print('  →', out)
