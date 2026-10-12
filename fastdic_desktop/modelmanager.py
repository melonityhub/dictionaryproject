# -*- coding: utf-8 -*-
"""In-app model download and installation dialog."""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QProgressBar,
                               QPushButton, QVBoxLayout)

from .model_download import DIRECTIONS, install_model_from_url
from .translator import discover_packages


class ModelDownloadWorker(QThread):
    progress = Signal(int, int)
    installed = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str, direction: str, models_root: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.direction = direction
        self.models_root = models_root

    def run(self):
        try:
            path = install_model_from_url(self.url, self.direction, self.models_root,
                                          progress=self.progress.emit)
            self.installed.emit(path)
        except Exception as exc:  # surfaced in the dialog
            self.failed.emit(str(exc))


class ModelManagerDialog(QDialog):
    """Collect a compatible ZIP source and install either translation direction."""

    def __init__(self, settings, models_root: str, parent=None, on_models_changed=None):
        super().__init__(parent)
        self.setWindowTitle('دانلود مدل‌های ترجمه')
        self.resize(760, 500)
        self.settings = settings
        self.models_root = models_root
        self.on_models_changed = on_models_changed
        self._workers = {}
        self._fields = {}
        self._statuses = {}
        self._progress = {}
        self._buttons = {}

        layout = QVBoxLayout(self)
        intro = QLabel(
            'برای هر جهت، نشانی مستقیم HTTPS فایل ZIP سازگار را وارد کنید. '
            'بسته باید translation_model.pb، فایل‌های BIPE و واژگان مدل را داشته باشد. '
            'پس از نصب، ترجمه بدون اینترنت انجام می‌شود؛ فقط دریافت مدل به اینترنت نیاز دارد.'
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        for direction in ('fa>en', 'en>fa'):
            info = DIRECTIONS[direction]
            group = QGroupBox(info['label'])
            group_layout = QVBoxLayout(group)
            status = QLabel()
            status.setWordWrap(True)
            group_layout.addWidget(status)

            source = QLineEdit(str(settings.get(info['setting'], '') or ''))
            source.setPlaceholderText('https://…/translation-model.zip')
            source.setClearButtonEnabled(True)
            group_layout.addWidget(source)

            controls = QHBoxLayout()
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            progress.setFormat('%p%')
            button = QPushButton('دانلود و نصب')
            controls.addWidget(progress, 1)
            controls.addWidget(button)
            group_layout.addLayout(controls)
            layout.addWidget(group)

            self._fields[direction] = source
            self._statuses[direction] = status
            self._progress[direction] = progress
            self._buttons[direction] = button
            button.clicked.connect(lambda _=False, selected=direction: self._start_download(selected))

        self.model_note = QLabel('محل ذخیره: ' + models_root)
        self.model_note.setWordWrap(True)
        layout.addWidget(self.model_note)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self._button_box.rejected.connect(self.close)
        layout.addWidget(self._button_box)
        self._refresh_status()

    def _refresh_status(self):
        installed = discover_packages(self.models_root)
        for direction in ('fa>en', 'en>fa'):
            if direction in installed:
                self._statuses[direction].setText('وضعیت: نصب شده و قابل‌شناسایی')
            else:
                self._statuses[direction].setText('وضعیت: هنوز نصب نشده')

    def _start_download(self, direction: str):
        if direction in self._workers:
            return
        url = self._fields[direction].text().strip()
        if not url:
            QMessageBox.warning(self, 'نشانی مدل وارد نشده',
                                'برای %s، نشانی مستقیم HTTPS فایل ZIP را وارد کنید.' % DIRECTIONS[direction]['label'])
            self._fields[direction].setFocus()
            return

        self.settings.set(DIRECTIONS[direction]['setting'], url)
        self._buttons[direction].setEnabled(False)
        self._progress[direction].setRange(0, 0)
        self._progress[direction].setFormat('در حال دانلود…')
        self._statuses[direction].setText('در حال دریافت و بررسی بسته…')
        self._button_box.button(QDialogButtonBox.Close).setEnabled(False)

        worker = ModelDownloadWorker(url, direction, self.models_root, self)
        self._workers[direction] = worker
        worker.progress.connect(lambda current, total, d=direction: self._update_progress(d, current, total))
        worker.installed.connect(lambda path, d=direction: self._download_succeeded(d, path))
        worker.failed.connect(lambda error, d=direction: self._download_failed(d, error))
        worker.finished.connect(lambda d=direction: self._worker_finished(d))
        worker.start()

    def _update_progress(self, direction: str, current: int, total: int):
        bar = self._progress[direction]
        if total <= 0:
            bar.setRange(0, 0)
            return
        bar.setRange(0, 100)
        bar.setValue(min(100, int(current * 100 / total)))
        bar.setFormat(f'%p%  ({self._format_bytes(current)} / {self._format_bytes(total)})')

    @staticmethod
    def _format_bytes(size: int) -> str:
        value = float(size)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if value < 1024 or unit == 'GB':
                return '%.1f %s' % (value, unit)
            value /= 1024
        return '%.1f GB' % value

    def _download_succeeded(self, direction: str, path: str):
        self._progress[direction].setRange(0, 100)
        self._progress[direction].setValue(100)
        self._progress[direction].setFormat('نصب شد')
        self._statuses[direction].setText('آماده: ' + path)
        self._refresh_status()
        if self.on_models_changed:
            self.on_models_changed()
        QMessageBox.information(self, 'مدل نصب شد',
                                'مدل %s نصب شد و برای ترجمه‌ی آفلاین آماده است.' % DIRECTIONS[direction]['label'])

    def _download_failed(self, direction: str, error: str):
        self._progress[direction].setRange(0, 100)
        self._progress[direction].setValue(0)
        self._progress[direction].setFormat('ناموفق')
        self._statuses[direction].setText('دانلود یا بررسی مدل ناموفق بود.')
        QMessageBox.critical(self, 'نصب مدل ناموفق بود', error)

    def _worker_finished(self, direction: str):
        worker = self._workers.pop(direction, None)
        if worker is not None:
            worker.deleteLater()
        self._buttons[direction].setEnabled(True)
        self._button_box.button(QDialogButtonBox.Close).setEnabled(not self._workers)

    def closeEvent(self, event):
        if self._workers:
            event.ignore()
            QMessageBox.information(self, 'دانلود در حال انجام است',
                                    'برای جلوگیری از ناقص‌شدن مدل، تا پایان دانلود صبر کنید.')
            return
        super().closeEvent(event)
