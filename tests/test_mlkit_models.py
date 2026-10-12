# -*- coding: utf-8 -*-
"""آزمون‌های دانلود/مدیریت مدل‌های ML Kit (بدون شبکه و بدون GUI)."""
import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastdic_desktop import mlkit_models
from fastdic_desktop.mlkit_models import (ModelDownloadError, download_package, format_bytes,
                                          installed_languages, known_languages, lang_for_pair,
                                          language_status, model_urls, pair_for, package_info,
                                          remove_language)
from fastdic_desktop.model_spec import ModelSpec
from fastdic_desktop.translator import discover_packages


BIPE_NAMES = (
    'encoder_embed_ids_0',
    'encoder_swizzled_birnn_0',
    'encoder_swizzled_birnn_1',
    'encoder_swizzled_birnn_2',
    'decoder_init_0',
    'decoder_step_embed_ids_0',
    'decoder_step_0',
)


# --------------------------------------------------------- ساخت بستهٔ آزمایشی
def _varint(value):
    out = bytearray()
    while value > 0x7f:
        out.append((value & 0x7f) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def _bytes_field(number, value):
    return _varint((number << 3) | 2) + _varint(len(value)) + value


def _direction_manifest(source, target):
    files = {name: 'resources/%s.bipe' % name for name in BIPE_NAMES}
    source_model, source_vocab = 'resources/source.model', 'resources/source.vocab'
    target_model, target_vocab = 'resources/target.model', 'resources/target.vocab'
    source_config = _bytes_field(1, source_model.encode()) + _bytes_field(2, source_vocab.encode())
    target_config = _bytes_field(1, target_model.encode()) + _bytes_field(2, target_vocab.encode())
    config = _bytes_field(1, source_config) + _bytes_field(6, target_config)
    manifest = _bytes_field(1, source.encode()) + _bytes_field(2, target.encode()) + _bytes_field(4, config)
    for name, path in files.items():
        mapping = _bytes_field(1, name.encode()) + _bytes_field(2, path.encode())
        manifest += _bytes_field(5, mapping)
    return manifest, files, (source_model, source_vocab, target_model, target_vocab)


def _mlkit_pair_archive(src='en', tgt='fa', wrapper='mlkit/', traversal=False,
                        valid_bipe=True):
    """ZIP در چیدمان بستهٔ واقعی ML Kit: هر دو جهت داخل یک پوشهٔ زوج (اختیاری پوششی)."""
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for source, target in ((src, tgt), (tgt, src)):
            manifest, files, resources = _direction_manifest(source, target)
            prefix = '%stranslate_%s%s/' % (wrapper, source, target)
            archive.writestr(prefix + 'translation_model.pb', manifest)
            for path in resources:
                archive.writestr(prefix + path, b'model-resource')
            for path in files.values():
                magic = b'\x00\x00\x00\x00BIPE' + b'fake-model-data' if valid_bipe else b'not-a-bipe-header'
                archive.writestr(prefix + path, magic)
        if traversal:
            archive.writestr('../outside.txt', b'not allowed')
    return output.getvalue()


class FakeResponse(io.BytesIO):
    def __init__(self, payload, url):
        super().__init__(payload)
        self.headers = {'Content-Length': str(len(payload))}
        self._url = url

    def geturl(self):
        return self._url


def _http_error(code):
    return urllib.error.HTTPError('https://test', code, 'err', hdrs=None, fp=io.BytesIO())


class UrlsAndCatalogTests(unittest.TestCase):
    def test_urls_match_mlkit_zzu_templates(self):
        # عین نمونهٔ مستندشده: https://dl.google.com/translate/offline/v5/high/r29/en_fa.zip
        self.assertEqual(
            model_urls('en_fa'),
            ['https://dl.google.com/translate/offline/v5/high/r29/en_fa.zip',
             'https://redirector.gvt1.com/edgedl/translate/offline/v5/high/r29/en_fa.zip'])

    def test_pair_naming_is_alphabetical(self):
        self.assertEqual(pair_for('fa'), 'en_fa')
        self.assertEqual(pair_for('de'), 'de_en')
        self.assertEqual(pair_for('ja'), 'en_ja')
        self.assertEqual(lang_for_pair('de_en'), 'de')

    def test_metadata_fields(self):
        info = package_info(lang='fa')
        self.assertEqual(info['pair'], 'en_fa')
        self.assertEqual(info['DL_SZ'], 32405428)
        self.assertEqual(info['SZ'], 39928876)
        self.assertEqual(info['RV'], 29)
        self.assertEqual(len(info['HASH']), 64)

    def test_catalog_priority_starts_with_user_languages(self):
        langs = known_languages()
        head = langs[:len(mlkit_models.PRIORITY_LANGS)]
        self.assertEqual(head, mlkit_models.PRIORITY_LANGS)
        self.assertEqual(len(langs), 58)          # ۵۸ زوج زبان بستهٔ PK_HIGH (انگلیسی ⇄ هر زبان)
        self.assertIn('fa', langs)


class DownloadInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.models_root = Path(self.temp.name) / 'models'
        self.payload = _mlkit_pair_archive()
        self.sha = hashlib.sha256(self.payload).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def _download(self, lang='fa', payload=None, sha=None, progress=None, urls=None):
        response = FakeResponse(self.payload if payload is None else payload, (urls or ['https://dl.google.com/x'])[0])
        with patch.object(mlkit_models, '_open_url', return_value=response) as open_url:
            path = download_package(lang, str(self.models_root), progress=progress, expected_hash=sha or self.sha)
            self.assertEqual(open_url.call_count, 1)
        return path

    def test_downloads_installs_both_directions_and_reports_progress(self):
        updates = []
        path = self._download('fa', progress=lambda d, t: updates.append((d, t)))
        installed = Path(path)
        self.assertEqual(installed, self.models_root / 'en_fa')
        self.assertEqual((ModelSpec(str(installed / 'translate_faen')).src_lang,
                          ModelSpec(str(installed / 'translate_faen')).tgt_lang), ('fa', 'en'))
        self.assertEqual((ModelSpec(str(installed / 'translate_enfa')).src_lang,
                          ModelSpec(str(installed / 'translate_enfa')).tgt_lang), ('en', 'fa'))
        self.assertEqual(updates[-1], (len(self.payload), len(self.payload)))

    def test_installed_state_and_cache_discovery(self):
        self._download('fa')
        status = language_status(str(self.models_root))
        self.assertTrue(status['fa']['ready'])
        self.assertFalse(status['de']['ready'])
        self.assertEqual(installed_languages(str(self.models_root)), ['fa'])
        found = discover_packages(str(self.models_root))
        self.assertEqual(found, {'fa>en': str(self.models_root / 'en_fa' / 'translate_faen'),
                                 'en>fa': str(self.models_root / 'en_fa' / 'translate_enfa')})

    def test_second_install_replaces_atomically(self):
        self._download('fa')
        marker = self.models_root / 'en_fa' / 'translate_faen' / 'old.bin'
        marker.write_bytes(b'old')
        self._download('fa')
        self.assertFalse(marker.exists())                       # بستهٔ قدیمی کامل جایگزین شده
        self.assertTrue(status_ready(self.models_root, 'fa'))

    def test_hash_mismatch_is_rejected(self):
        with self.assertRaises(ModelDownloadError):
            self._download('fa', sha='0' * 64)
        self.assertFalse((self.models_root / 'en_fa').exists())

    def test_corrupt_zip_is_rejected(self):
        bad = b'this is not a zip file'
        with self.assertRaises(ModelDownloadError):
            self._download('fa', payload=bad, sha=hashlib.sha256(bad).hexdigest())
        self.assertFalse((self.models_root / 'en_fa').exists())

    def test_zip_slip_is_rejected(self):
        bad = _mlkit_pair_archive(traversal=True)
        with self.assertRaisesRegex(ModelDownloadError, 'مسیر'):
            self._download('fa', payload=bad, sha=hashlib.sha256(bad).hexdigest())
        self.assertFalse((Path(self.temp.name) / 'outside.txt').exists())

    def test_invalid_bipe_content_is_rejected(self):
        bad = _mlkit_pair_archive(valid_bipe=False)
        with self.assertRaises(ModelDownloadError):
            self._download('fa', payload=bad, sha=hashlib.sha256(bad).hexdigest())
        self.assertFalse((self.models_root / 'en_fa').exists())

    def test_falls_back_to_redirector_when_primary_fails(self):
        calls = []

        def opener(url, timeout=None):
            calls.append(url)
            if 'dl.google.com' in url:
                raise urllib.error.URLError('blocked')
            return FakeResponse(self.payload, url)

        with patch.object(mlkit_models, '_open_url', side_effect=opener):
            download_package('fa', str(self.models_root), expected_hash=self.sha)
        self.assertEqual(len(calls), 2)
        self.assertIn('redirector.gvt1.com', calls[1])

    def test_both_servers_failing_reports_error(self):
        with patch.object(mlkit_models, '_open_url', side_effect=urllib.error.URLError('no network')):
            with self.assertRaises(ModelDownloadError):
                download_package('fa', str(self.models_root))

    def test_wrong_package_for_requested_language_is_rejected(self):
        de_payload = _mlkit_pair_archive('de', 'en')
        with self.assertRaisesRegex(ModelDownloadError, 'de_en'):
            self._download('fa', payload=de_payload, sha=hashlib.sha256(de_payload).hexdigest())

    def test_cancel_during_download(self):
        def progress(done, total):
            raise KeyboardInterrupt

        cancelled = {'flag': False}

        class Cancel:
            def __call__(self):
                return cancelled['flag']

        # لغو پیش از شروع خواندن بلوک‌ها
        with patch.object(mlkit_models, '_open_url', return_value=FakeResponse(self.payload, 'https://dl.google.com/x')):
            with self.assertRaises(mlkit_models.DownloadCancelled):
                download_package('fa', str(self.models_root), expected_hash=self.sha,
                                 cancel=lambda: True)
        self.assertFalse((self.models_root / 'en_fa').exists())

    def test_remove_language_clears_cache(self):
        self._download('fa')
        remove_language('fa', str(self.models_root))
        self.assertFalse((self.models_root / 'en_fa').exists())
        self.assertEqual(installed_languages(str(self.models_root)), [])
        with self.assertRaises(ModelDownloadError):
            remove_language('fa', str(self.models_root))


def status_ready(root, lang):
    return language_status(str(root))[lang]['ready']


class TranslatorTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.models_root = Path(self.temp.name) / 'models'

    def tearDown(self):
        self.temp.cleanup()

    def _install(self, lang):
        payload = _mlkit_pair_archive('en', lang)
        with patch.object(mlkit_models, '_open_url',
                          return_value=FakeResponse(payload, 'https://dl.google.com/x')):
            download_package(lang, str(self.models_root), expected_hash=hashlib.sha256(payload).hexdigest())

    def test_direction_for_any_target(self):
        from fastdic_desktop.translator import OfflineTranslatorService
        svc = OfflineTranslatorService(str(self.models_root))
        self.assertEqual(svc.direction_for('Hello world', 'fa'), 'en>fa')
        self.assertEqual(svc.direction_for('سلام', 'fa'), 'fa>en')
        self.assertEqual(svc.direction_for('Hello world', 'de'), 'en>de')
        self.assertEqual(svc.direction_for('سلام', 'de'), 'de>en')

    def test_translate_reports_missing_model_with_size(self):
        from fastdic_desktop.translator import OfflineTranslatorService
        svc = OfflineTranslatorService(str(self.models_root))
        result, error, direction = svc.translate('Hello world', target='de')
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('آلمانی', error)
        self.assertIn('مگابایت', error)
        self.assertEqual(direction, 'en>de')

    def test_discovery_ignores_broken_folders(self):
        self.models_root.mkdir(parents=True)
        (self.models_root / 'xx_yy' / 'broken').mkdir(parents=True)
        (self.models_root / 'xx_yy' / 'broken' / 'translation_model.pb').write_bytes(b'junk')
        self.assertEqual(discover_packages(str(self.models_root)), {})


class FormatBytesTests(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(format_bytes(32405428), '30.9 مگابایت')
        self.assertEqual(format_bytes(39928876), '38.1 مگابایت')
        self.assertEqual(format_bytes(512), '512 بایت')


if __name__ == '__main__':
    unittest.main()
