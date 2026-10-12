# -*- coding: utf-8 -*-
"""پنجرهٔ «مدل‌های ترجمهٔ آفلاین» — انتخاب زبان مقصد از فهرست، دانلود از سرورهای خود
ML Kit (dl.google.com) با نمایش پیشرفت و حجم DL_SZ، وضعیت «آمادهٔ آفلاین»، دکمهٔ حذف
و استفادهٔ بدون اینترنت از کش محلی در اجراهای بعدی."""
import threading

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
                               QMessageBox, QProgressBar, QPushButton, QStackedWidget,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .mlkit_models import (DownloadCancelled, ModelDownloadError, download_package, format_bytes,
                           known_languages, language_name, language_native, model_urls,
                           pair_for, remove_language)

# صفحات ستون «عملیات»
PAGE_DOWNLOAD, PAGE_PROGRESS, PAGE_DELETE = 0, 1, 2

STATUS_READY = '✔ آمادهٔ آفلاین'
STATUS_PARTIAL = 'نصب ناقص'
STATUS_NONE = 'دانلود نشده'
STATUS_DOWNLOADING = 'در حال دانلود…'


class DownloadWorker(QThread):
    """دانلود یک بستهٔ زبان در پس‌زمینه (مثل ModelManager.download در ML Kit)."""
    progress = Signal(str, int, int)          # lang, received, total
    installed = Signal(str, str)              # lang, path
    failed = Signal(str, str)                 # lang, error
    cancelled = Signal(str)                   # lang

    def __init__(self, lang: str, models_root: str, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.models_root = models_root
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        lang = self.lang
        try:
            path = download_package(
                lang, self.models_root,
                progress=lambda done, total: self.progress.emit(lang, done, total),
                cancel=self.cancel_event.is_set)
            self.installed.emit(lang, path)
        except DownloadCancelled:
            self.cancelled.emit(lang)
        except Exception as exc:  # noqa — در پنجره نمایش داده می‌شود
            self.failed.emit(lang, str(exc))


class ModelManagerDialog(QDialog):
    """فهرست زبان‌های ML Kit با وضعیت، حجم DL_SZ، دانلود/لغو و حذف."""

    def __init__(self, settings, models_root: str, parent=None, on_models_changed=None):
        super().__init__(parent)
        self.setWindowTitle('مدل‌های ترجمهٔ آفلاین (ML Kit)')
        self.resize(820, 600)
        self.settings = settings
        self.models_root = models_root
        self.on_models_changed = on_models_changed
        self._worker: DownloadWorker = None
        self._rows = {}                    # lang → dict(tree_item, stack, buttons, progress, status_item)
        self._prev_page = {}

        layout = QVBoxLayout(self)
        intro = QLabel(
            'زبان مقصد را از فهرست انتخاب کنید؛ مدل همان زبان از همان سرورهای خود ML Kit '
            '(همان مدل‌های آفلاین Google Translate) دانلود و با بررسی SHA-256 نصب می‌شود.\n'
            'هر بسته هر دو جهت (انگلیسی ⇄ زبان) را دارد. پس از نصب، ترجمه همیشه آفلاین از کش '
            'محلی انجام می‌شود و فقط دریافت اولیه اینترنت می‌خواهد.')
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.source_note = QLabel()
        self.source_note.setWordWrap(True)
        self.source_note.setStyleSheet('color: gray;')
        layout.addWidget(self.source_note)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(['زبان', 'وضعیت', 'حجم دانلود (DL_SZ)'])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree, 1)

        self.storage_note = QLabel('محل ذخیره (کش محلی): ' + models_root)
        self.storage_note.setWordWrap(True)
        layout.addWidget(self.storage_note)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self._button_box.rejected.connect(self.close)
        layout.addWidget(self._button_box)

        self._populate()
        self._refresh_status()

    # ------------------------------------------------------------ ساخت ردیف‌ها
    def _populate(self):
        sample_urls = model_urls(pair_for('fa'))
        self.source_note.setText('منبع دانلود (مثل ML Kit): ' + sample_urls[0])
        for lang in known_languages():
            item = QTreeWidgetItem()
            name = language_name(lang)
            item.setText(0, '%s (%s)' % (name, lang))
            item.setToolTip(0, language_native(lang))
            item.setTextAlignment(0, Qt.AlignRight | Qt.AlignVCenter)
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
            self.tree.addTopLevelItem(item)

            page_wrap = QWidget()
            row = QHBoxLayout(page_wrap)
            row.setContentsMargins(2, 0, 2, 0)
            stack = QStackedWidget(page_wrap)
            row.addWidget(stack)

            btn_download = QPushButton('دانلود')
            btn_download.setMinimumWidth(84)
            btn_download.clicked.connect(lambda _=False, l=lang: self._start_download(l))
            stack.addWidget(btn_download)

            progress_page = QWidget()
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setFormat('%p%')
            btn_cancel = QPushButton('لغو')
            btn_cancel.setFixedWidth(48)
            btn_cancel.clicked.connect(self._cancel_download)
            inner = QHBoxLayout(progress_page)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(pbar, 1)
            inner.addWidget(btn_cancel)
            stack.addWidget(progress_page)

            btn_delete = QPushButton('حذف')
            btn_delete.setMinimumWidth(84)
            btn_delete.clicked.connect(lambda _=False, l=lang: self._delete(l))
            stack.addWidget(btn_delete)

            self.tree.setItemWidget(item, 2, page_wrap)
            item.setSizeHint(2, QSize(190, 36))
            self._rows[lang] = {'item': item, 'stack': stack, 'download': btn_download,
                                'progress': pbar, 'delete': btn_delete}

    # ------------------------------------------------------------ وضعیت‌ها
    def _refresh_status(self):
        from .mlkit_models import language_status
        status = language_status(self.models_root)
        installed = 0
        for lang, row in self._rows.items():
            rec = status.get(lang, {})
            if rec.get('ready'):
                row['item'].setText(1, STATUS_READY)
                installed += 1
            elif rec.get('partial'):
                dirs = '، '.join(sorted(rec['directions']))
                row['item'].setText(1, '%s (%s)' % (STATUS_PARTIAL, dirs))
            else:
                row['item'].setText(1, STATUS_NONE)
            row['item'].setText(2, format_bytes(rec.get('DL_SZ', 0)))
            row['item'].setToolTip(
                2, 'حجم بازشده: %s  |  ریویژن: r%d  |  SHA-256: %s…'
                   % (format_bytes(rec.get('SZ', 0)), rec.get('RV', 0), rec.get('HASH', '')[:16]))
            if self._worker is None or self._worker.lang != lang:
                self._show_page(lang, PAGE_DELETE if rec.get('ready') or rec.get('partial') else PAGE_DOWNLOAD)
        self.setWindowTitle('مدل‌های ترجمهٔ آفلاین (ML Kit) — %d زبان آماده' % installed)
        self._update_close_button()

    def _show_page(self, lang: str, page: int):
        row = self._rows[lang]
        row['stack'].setCurrentIndex(page)

    def _update_close_button(self):
        busy = self._worker is not None
        self._button_box.button(QDialogButtonBox.Close).setEnabled(not busy)

    # ------------------------------------------------------------ دانلود
    def _start_download(self, lang: str):
        if self._worker is not None:
            return
        for l, row in self._rows.items():
            row['download'].setEnabled(False)
            row['delete'].setEnabled(False)
        bar = self._rows[lang]['progress']
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFormat('در حال دانلود…')
        self._rows[lang]['item'].setText(1, STATUS_DOWNLOADING)
        self._show_page(lang, PAGE_PROGRESS)

        self._worker = DownloadWorker(lang, self.models_root, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.installed.connect(self._on_installed)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        self._update_close_button()

    def _cancel_download(self):
        if self._worker is not None:
            self._worker.cancel()

    def _on_progress(self, lang: str, received: int, total: int):
        row = self._rows[lang]
        bar = row['progress']
        if total > 0:
            bar.setRange(0, 100)
            bar.setValue(min(100, int(received * 100 / total)))
            bar.setFormat('%p%  (%s / %s)' % (format_bytes(received), format_bytes(total)))
        else:
            bar.setRange(0, 0)
        row['item'].setText(1, STATUS_DOWNLOADING)

    def _on_installed(self, lang: str, path: str):
        self._refresh_status()
        if self.on_models_changed:
            self.on_models_changed()
        QMessageBox.information(
            self, 'مدل آماده شد',
            'مدل «%s» دانلود و نصب شد و برای ترجمهٔ آفلاین آماده است.\n%s' % (language_name(lang), path))

    def _on_failed(self, lang: str, error: str):
        self._refresh_status()
        QMessageBox.critical(self, 'دانلود مدل ناموفق بود',
                             'دریافت «%s» ناموفق بود:\n%s' % (language_name(lang), error))

    def _on_cancelled(self, lang: str):
        self._refresh_status()

    def _on_finished(self):
        worker, self._worker = self._worker, None
        if worker is not None:
            worker.deleteLater()
        for row in self._rows.values():
            row['download'].setEnabled(True)
            row['delete'].setEnabled(True)
        self._refresh_status()

    # ------------------------------------------------------------ حذف
    def _delete(self, lang: str):
        if self._worker is not None:
            return
        name = language_name(lang)
        if QMessageBox.question(
                self, 'حذف مدل',
                'مدل «%s» از کش محلی حذف شود؟ (برای استفادهٔ دوباره باید دوباره دانلود شود.)' % name,
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            remove_language(lang, self.models_root)
        except ModelDownloadError as exc:
            QMessageBox.critical(self, 'حذف مدل ناموفق بود', str(exc))
            return
        self._refresh_status()
        if self.on_models_changed:
            self.on_models_changed()

    def closeEvent(self, event):
        if self._worker is not None:
            event.ignore()
            QMessageBox.information(self, 'دانلود در حال انجام است',
                                    'برای بستن، اول دانلود را «لغو» کنید.')
            return
        super().closeEvent(event)
