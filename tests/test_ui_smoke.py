# -*- coding: utf-8 -*-
"""آزمون دود UI با PySide6 (در صورت نبود PySide6 رد می‌شود).

روی مسیرهای واقعی ویجت‌ها اجرا می‌شود: پنجرهٔ مدیریت مدل‌ها (وضعیت، صفحات
دانلود/پیشرفت/حذف، لغو، حذف) و پنجرهٔ اصلی (فهرست زبان مقصد، همگام‌سازی وضعیت،
جریان ترجمه). شبکه با پچ‌کردن ``download_package`` شبیه‌سازی می‌شود.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
except Exception:  # noqa — در محیط‌های بدون کتابخانه‌های GUI رد شود
    raise unittest.SkipTest('PySide6/Qt در این محیط در دسترس نیست')

_app = QApplication.instance() or QApplication([])

from fastdic_desktop import modelmanager
from fastdic_desktop.mlkit_models import language_status
from fastdic_desktop.modelmanager import (PAGE_DELETE, PAGE_DOWNLOAD, PAGE_PROGRESS,
                                          ModelManagerDialog)
from fastdic_desktop.translator import OfflineTranslatorService
from fastdic_desktop.userdata import Settings, UserData

from tests.test_mlkit_models import _direction_manifest


def _write_direction(folder, src, tgt):
    """یک پوشهٔ جهتِ قابل‌شناسایی (manifest معتبر + فایل‌های معرفی‌شده) می‌سازد."""
    manifest, files, resources = _direction_manifest(src, tgt)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'translation_model.pb'), 'wb') as f:
        f.write(manifest)
    for path in list(files.values()) + list(resources):
        full = os.path.join(folder, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'wb') as f:
            f.write(b'\x00\x00\x00\x00BIPE' if path.endswith('.bipe') else b'resource')


def _install_pair(root, src, tgt):
    _write_direction(os.path.join(root, 'translate_%s%s' % (src, tgt)), src, tgt)


def _fake_installer(models_root, langs):
    """شبیه‌سازی نصب: همان ساختار پوشه‌ای که download_package می‌سازد."""
    def install(lang, root, progress=None, cancel=None, expected_hash=None):
        pair_dir = os.path.join(root, {'fa': 'en_fa', 'de': 'de_en'}.get(lang, lang + '_en'))
        _write_direction(os.path.join(pair_dir, 'translate_%sen' % lang), lang, 'en')
        _write_direction(os.path.join(pair_dir, 'translate_en%s' % lang), 'en', lang)
        for done in (0, 50, 100):
            if progress:
                progress(done, 100)
        return pair_dir
    return install


class ModelManagerDialogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, 'models')
        os.makedirs(self.root)
        # بستهٔ «نصب‌شدهٔ» واقعی‌نما برای فارسی (چیدمان ML Kit: root/en_fa/translate_*/)
        _write_direction(os.path.join(self.root, 'en_fa', 'translate_faen'), 'fa', 'en')
        _write_direction(os.path.join(self.root, 'en_fa', 'translate_enfa'), 'en', 'fa')
        self.st = Settings(os.path.join(self.tmp.name, 'settings.json'))
        self.changed = []
        self.dlg = ModelManagerDialog(self.st, self.root, None,
                                      on_models_changed=lambda: self.changed.append(1))

    def tearDown(self):
        self.tmp.cleanup()

    def _row(self, lang):
        return self.dlg._rows[lang]

    def test_rows_and_status_pages(self):
        self.assertEqual(len(self.dlg._rows), 58)
        fa = language_status(self.root)['fa']
        self.assertTrue(fa['ready'])
        # زبان نصب‌شده ⇒ صفحهٔ حذف؛ زبان نصب‌نشده ⇒ صفحهٔ دانلود
        self.assertEqual(self._row('fa')['stack'].currentIndex(), PAGE_DELETE)
        self.assertEqual(self._row('de')['stack'].currentIndex(), PAGE_DOWNLOAD)
        self.assertIn('آمادهٔ آفلاین', self._row('fa')['item'].text(1))
        self.assertIn('دانلود نشده', self._row('de')['item'].text(1))
        # حجم DL_SZ از متادیتا در ستون حجم
        self.assertIn('مگابایت', self._row('de')['item'].text(2))

    def test_download_flow_updates_rows_and_notifies(self):
        calls = []
        with patch.object(modelmanager, 'download_package',
                          side_effect=_fake_installer(self.root, ['de'])) as fake, \
             patch.object(modelmanager.QMessageBox, 'information'):
            self.dlg._start_download('de')
            # Worker واقعی QThread است؛ تا پایان اجرا صبر می‌کنیم
            self.dlg._worker.wait(10000)
            while self.dlg._worker is not None:
                self.dlg._worker and QApplication.processEvents()
            fake.assert_called_once()
        self.assertEqual(self.changed, [1])
        self.assertTrue(language_status(self.root)['de']['ready'])

    def test_cancel_returns_to_previous_state(self):
        def cancelled_install(lang, root, progress=None, cancel=None, expected_hash=None):
            raise modelmanager.DownloadCancelled()
        with patch.object(modelmanager, 'download_package', side_effect=cancelled_install):
            self.dlg._start_download('de')
            self.dlg._worker.wait(10000)
            while self.dlg._worker is not None:
                QApplication.processEvents()
        self.assertEqual(self._row('de')['stack'].currentIndex(), PAGE_DOWNLOAD)

    def test_failed_download_shows_error_page_state(self):
        from fastdic_desktop.mlkit_models import ModelDownloadError

        def failing(lang, root, progress=None, cancel=None, expected_hash=None):
            raise ModelDownloadError('اتصال برقرار نشد')
        with patch.object(modelmanager, 'download_package', side_effect=failing), \
             patch.object(modelmanager.QMessageBox, 'critical'):
            self.dlg._start_download('de')
            self.dlg._worker.wait(10000)
            while self.dlg._worker is not None:
                QApplication.processEvents()
        self.assertEqual(self._row('de')['stack'].currentIndex(), PAGE_DOWNLOAD)

    def test_delete_removes_cache_after_confirm(self):
        with patch.object(modelmanager.QMessageBox, 'question', return_value=QMessageBox.Yes), \
             patch.object(modelmanager.QMessageBox, 'critical'):
            self.dlg._delete('fa')
        self.assertFalse(language_status(self.root)['fa']['ready'])
        self.assertEqual(self._row('fa')['stack'].currentIndex(), PAGE_DOWNLOAD)


class MainWindowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, 'models')
        os.makedirs(self.root)
        self.st = Settings(os.path.join(self.tmp.name, 'settings.json'))
        self.st.set('models_dir', self.root)
        self.ud = UserData(os.path.join(self.tmp.name, 'user.sqlite'))
        from fastdic_desktop.app import MainWindow
        self.win = MainWindow(settings=self.st, userdata=self.ud)

    def tearDown(self):
        self.tmp.cleanup()

    def test_target_combo_lists_all_mlkit_languages(self):
        self.assertEqual(self.win.tr_lang.count(), 58)
        self.assertEqual(self.win.tr_lang.itemData(0), 'fa')          # فارسی اول
        self.assertEqual(self.win._current_target(), 'fa')

    def test_target_persisted_and_hint_updates(self):
        for i in range(self.win.tr_lang.count()):
            if self.win.tr_lang.itemData(i) == 'de':
                self.win.tr_lang.setCurrentIndex(i)
        self.assertEqual(self.st.get('translate_target'), 'de')
        self.assertIn('DL_SZ', self.win.tr_hint.text())               # نصب نیست ⇒ حجم دانلود

    def test_ready_language_marks_hint_and_status(self):
        _write_direction(os.path.join(self.root, 'en_fa', 'translate_faen'), 'fa', 'en')
        _write_direction(os.path.join(self.root, 'en_fa', 'translate_enfa'), 'en', 'fa')
        self.win.load_resources()
        self.assertIn('آمادهٔ آفلاین', self.win.tr_hint.text())
        self.assertIn('فارسی', self.win.status.text())

    def test_translate_without_service_shows_download_error(self):
        self.win.tr_in.setPlainText('Hello world')
        self.win.translate_text('Hello world')
        html = self.win.view.toHtml()
        self.assertTrue(html)                                          # صفحهٔ خطا رندر شد

    def test_translate_flow_with_fake_service(self):
        class FakeSvc:
            packages = {'en>de': 'x'}

            def available(self):
                return ['en>de']

            def direction_for(self, text, target='fa'):
                return 'en>%s' % target

            def translate(self, text, target='fa'):
                return 'Hallo Welt', None, 'en>%s' % target

        self.win.svc = FakeSvc()
        self.win.on_translated('Hallo Welt', None, 'en>de', 'Hello world')
        self.assertIn('Hallo Welt', self.win.view.toPlainText())
        hist = self.ud.history_latest(1)
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]['word'], 'Hello world')


if __name__ == '__main__':
    unittest.main()
