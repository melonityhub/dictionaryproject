# -*- coding: utf-8 -*-
"""رابط گرافیکی (PySide6) — جریان کار مطابق اپ اندروید:
  جستجو (SearchFragment) → فهرست پیشنهاد [ردیف مترجم + تاریخچه(۲) + نتایج دیتابیس(≤۵۰) / Levenshtein]
  → انتخاب مورد (WordResultFragment) → HTML نتیجه (FDHtml) → ذخیره در تاریخچه (deleteAndInsert).
"""
import os
import sys
import traceback
import urllib.parse

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, QObject
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit,
                               QPushButton, QSpinBox, QSplitter, QTabBar, QTextBrowser, QVBoxLayout, QWidget)

from . import htmlgen
from .db import FDDatabase, category_of, lang_of, trim_lower, is_english, CAT_ENGLISH, CAT_PERSIAN
from .numwords import en_words, fa_words, is_integer_text, to_int
from .translator import OfflineTranslatorService, MAX_TRANSLATOR_WORDS
from .userdata import Settings, UserData

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
except Exception:           # noqa
    QMediaPlayer = None


class TranslateWorker(QThread):
    done = Signal(object, object, str, str)       # result, error, direction, source

    def __init__(self, svc, text):
        super().__init__()
        self.svc, self.text = svc, text

    def run(self):
        try:
            r, err, d = self.svc.translate(self.text)
            self.done.emit(r, err, d, self.text)
        except Exception as ex:   # noqa
            traceback.print_exc()
            self.done.emit(None, 'خطا در ترجمه: %s' % ex, '', self.text)


class SettingsDialog(QDialog):
    def __init__(self, st: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('تنظیمات')
        self.st = st
        f = QFormLayout(self)
        self.db = QLineEdit(st.get('db_path', ''))
        self.models = QLineEdit(st.get('models_dir', ''))
        for edit, is_dir in ((self.db, False), (self.models, True)):
            b = QPushButton('انتخاب…')
            b.clicked.connect(lambda _=False, e=edit, d=is_dir: self._pick(e, d))
            row = QHBoxLayout(); row.addWidget(edit); row.addWidget(b)
            f.addRow('پوشه‌ی بسته‌های ترجمه (شامل translate_faen / translate_enfa):' if is_dir
                     else 'فایل دیتابیس (fastdic_plain.sqlite):', row)
        self.beam = QSpinBox(); self.beam.setRange(1, 8); self.beam.setValue(int(st.get('beam', 4)))
        f.addRow('اندازه‌ی beam search (۱ تا ۸):', self.beam)
        self.dark = QCheckBox('حالت تیره'); self.dark.setChecked(bool(st.get('dark', False)))
        f.addRow(self.dark)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        f.addRow(bb)
        self.resize(640, 220)

    def _pick(self, edit, is_dir):
        p = (QFileDialog.getExistingDirectory(self, 'انتخاب پوشه') if is_dir
             else QFileDialog.getOpenFileName(self, 'انتخاب دیتابیس', '', 'SQLite (*.sqlite *.db);;All (*)')[0])
        if p:
            edit.setText(p)

    def apply(self):
        self.st.set('db_path', self.db.text().strip()); self.st.set('models_dir', self.models.text().strip())
        self.st.set('beam', self.beam.value()); self.st.set('dark', self.dark.isChecked())


class MainWindow(QMainWindow):
    LIMIT = 50                  # ConfigConstKt.LIMIT
    HISTORY_LIMIT = 2           # SearchFragment: history.search(word, 2)

    def __init__(self, settings: Settings = None, userdata: UserData = None):
        super().__init__()
        self.setWindowTitle('FastDic Desktop — دیکشنری و مترجم آفلاین')
        self.resize(1180, 760)
        self.st = settings or Settings()
        self.ud = userdata or UserData()
        self.db = None
        self.svc = None
        self.mode = 'search'
        self.current = None                       # {word, category, meaning, word_id}
        self._worker = None
        self._player = None

        # ----- چیدمان -----
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        top = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText('یک لغت یا عبارت را تایپ کنید… (فارسی یا انگلیسی)')
        self.search.setClearButtonEnabled(True)
        self.btn_fav = QPushButton('☆'); self.btn_fav.setToolTip('افزودن/حذف از علاقه‌مندی‌ها'); self.btn_fav.setFixedWidth(40)
        self.btn_settings = QPushButton('⚙ تنظیمات')
        top.addWidget(self.search, 1); top.addWidget(self.btn_fav); top.addWidget(self.btn_settings)
        root.addLayout(top)

        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1)
        left = QWidget(); lv = QVBoxLayout(left); lv.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabBar(); [self.tabs.addTab(t) for t in ('جستجو', 'تاریخچه', 'علاقه‌مندی‌ها', 'مترجم متن')]
        lv.addWidget(self.tabs)
        self.list = QListWidget(); lv.addWidget(self.list, 1)
        # صفحه‌ی «مترجم متن»
        self.tr_box = QWidget(); tv = QVBoxLayout(self.tr_box); tv.setContentsMargins(0, 0, 0, 0)
        self.tr_in = QPlainTextEdit(); self.tr_in.setPlaceholderText('متن را این‌جا بنویسید (حداکثر %d واژه)…' % MAX_TRANSLATOR_WORDS)
        self.tr_btn = QPushButton('ترجمه (Ctrl+Enter)')
        tv.addWidget(self.tr_in, 1); tv.addWidget(self.tr_btn); lv.addWidget(self.tr_box, 1); self.tr_box.hide()
        split.addWidget(left)
        self.view = QTextBrowser(); self.view.setOpenLinks(False); self.view.setOpenExternalLinks(False)
        split.addWidget(self.view)
        split.setStretchFactor(0, 2); split.setStretchFactor(1, 5)
        self.status = QLabel(''); self.statusBar().addWidget(self.status, 1)

        # ----- سیگنال‌ها -----
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(120)
        self.timer.timeout.connect(self.refresh_list)
        self.search.textChanged.connect(lambda _t: self.timer.start())
        self.search.returnPressed.connect(self.on_enter)
        self.list.itemActivated.connect(self.on_item)
        self.list.itemClicked.connect(self.on_item)
        self.tabs.currentChanged.connect(self.on_tab)
        self.view.anchorClicked.connect(self.on_anchor)
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_fav.clicked.connect(self.toggle_fav)
        self.tr_btn.clicked.connect(self.translate_box)
        QShortcut(QKeySequence('Ctrl+Return'), self, activated=self.translate_box)
        QShortcut(QKeySequence('Ctrl+L'), self, activated=lambda: (self.search.setFocus(), self.search.selectAll()))

        self.load_resources()
        self.refresh_list()
        self.show_welcome()

    # ----------------------------------------------------------------- منابع
    @property
    def dark(self) -> bool:
        return bool(self.st.get('dark', False))

    def load_resources(self):
        p = self.st.get('db_path', '')
        self.db = None
        if p and os.path.isfile(p):
            try:
                d = FDDatabase(p)
                self.db = d if d.check() else None
            except Exception:
                self.db = None
        mroot = self.st.get('models_dir', '')
        self.svc = OfflineTranslatorService(mroot, beam=int(self.st.get('beam', 4))) if mroot and os.path.isdir(mroot) else None
        msg = []
        msg.append('دیتابیس: ' + ('آماده' if self.db else 'انتخاب نشده'))
        msg.append('مترجم: ' + (', '.join(x.replace('>', '→') for x in self.svc.available()) if self.svc and self.svc.available() else 'بسته‌ای پیدا نشد'))
        self.status.setText('   |   '.join(msg))

    def open_settings(self):
        dlg = SettingsDialog(self.st, self)
        if dlg.exec():
            dlg.apply(); self.load_resources(); self.refresh_list()

    def show_welcome(self):
        if not self.db or not self.svc:
            body = htmlgen.not_found('از «⚙ تنظیمات» فایل دیتابیس و پوشه‌ی بسته‌های ترجمه را انتخاب کنید.', 'خوش آمدید')
        else:
            body = htmlgen.not_found('یک لغت را جستجو کنید، یا روی ردیف «ترجمه» بزنید تا متن با مدل آفلاین ترجمه شود.', 'آماده است')
        self.view.setHtml(htmlgen.wrap(body, self.dark))

    # ----------------------------------------------------------------- فهرست پیشنهادها
    def on_tab(self, i):
        self.mode = ('search', 'history', 'favourites', 'translator')[i]
        self.tr_box.setVisible(self.mode == 'translator'); self.list.setVisible(self.mode != 'translator')
        self.refresh_list()

    def _add_item(self, m: dict):
        word, meaning = m.get('word') or '', m.get('meaning') or ''
        if m.get('is_placeholder'):
            text = '🌐  ترجمه‌ی «%s» با مترجم آفلاین' % word
        elif m.get('is_translator'):
            text = ('🕘 ' if m.get('is_history') else '') + '🌐 ' + word[:80] + (('\n' + meaning[:140]) if meaning else '')
        else:
            text = ('🕘 ' if m.get('is_history') else '') + word + (('\n' + meaning[:140]) if meaning else '')
        it = QListWidgetItem(text)
        it.setData(Qt.UserRole, m)
        self.list.addItem(it)

    def refresh_list(self):
        if self.mode == 'translator':
            return
        self.list.clear()
        q = self.search.text()
        if self.mode == 'history':
            for m in self.ud.history_latest(100): self._add_item(m)
            return
        if self.mode == 'favourites':
            for m in self.ud.fav_list(): self._add_item(m)
            return
        t = trim_lower(q) or ''
        if not t:                                               # جستجوی خالی ⇒ ۵۰ مورد آخرِ تاریخچه
            for m in self.ud.history_latest(50): self._add_item(m)
            return
        if len(t) >= 100:
            self._add_item({'word': q.strip()[:60] + '…', 'is_placeholder': True, 'is_translator': True, 'text': q}); return
        # SearchFragment.getSuggestedWords: عدد ⇒ تبدیل به حروف
        if is_integer_text(q):
            n = to_int(q)
            self._add_item({'word': en_words(n), 'meaning': fa_words(n), 'is_number': True})
        hist = self.ud.history_search(q, category_of(t), self.HISTORY_LIMIT)
        for h in hist: h['is_translator'] = False
        found = self.db.search(q, self.LIMIT) if self.db else []
        self._add_item({'word': q.strip(), 'is_placeholder': True, 'is_translator': True, 'text': q})        # ردیف مترجم (getTranslatePlaceHolder)
        if found:
            for m in hist + found: self._add_item(m)
        else:
            if len(t) < 10: [self._add_item(h) for h in hist]
            if self.db:
                for m in self.db.levenshtein_suggestions(t): self._add_item(m)

    def on_enter(self):
        if self.list.count():
            first_real = next((i for i in range(self.list.count()) if not self.list.item(i).data(Qt.UserRole).get('is_placeholder')), 0)
            self.on_item(self.list.item(first_real))

    # ----------------------------------------------------------------- نمایش نتیجه
    def on_item(self, item: QListWidgetItem):
        m = item.data(Qt.UserRole)
        if not m:
            return
        if m.get('is_placeholder'):
            self.translate_text(m.get('text') or m.get('word'))
        elif m.get('is_translator'):                      # ردیف تاریخچه/علاقه‌مندیِ یک ترجمه: همان نتیجه‌ی ذخیره‌شده
            self.view.setHtml(htmlgen.wrap(htmlgen.translator_block(m['word'], m.get('meaning'), None, ''), self.dark))
            self.current = {'word': m['word'], 'category': m['category'], 'meaning': m.get('meaning'), 'word_id': None}
            self._update_fav_button()
        elif m.get('is_number'):
            return
        else:
            self.show_word(m)

    def show_word(self, m: dict, record=True):
        if not self.db:
            self.view.setHtml(htmlgen.wrap(htmlgen.not_found('ابتدا فایل دیتابیس را از تنظیمات انتخاب کنید.'), self.dark)); return
        word = m.get('word') or ''
        lang = lang_of(word)
        res = self.db.detail_by_word_id(lang, m['word_id']) if m.get('word_id') is not None else self.db.word_exists(lang, word)
        if res is None:
            res = self.db.word_exists(lang, word)
        if res is None:
            self.view.setHtml(htmlgen.wrap(htmlgen.not_found('برای «%s» نتیجه‌ای در دیتابیس نبود.' % word), self.dark)); return
        body = htmlgen.english_block(res) if res['lang'] == 'English' else htmlgen.persian_block(res)
        self.view.setHtml(htmlgen.wrap(body, self.dark))
        cat = CAT_ENGLISH if res['lang'] == 'English' else CAT_PERSIAN
        meaning = ('، ' if cat == CAT_ENGLISH else ', ').join(self.db.get_word_meanings(res['lang'], res['word_id']))
        self.current = {'word': res['word'], 'category': cat, 'meaning': meaning, 'word_id': res['word_id']}
        if record:
            self.ud.history_delete_and_insert(res['word'], cat, meaning, res['word_id'], False)
        self._update_fav_button()

    # ----------------------------------------------------------------- ترجمه
    def translate_box(self):
        if self.mode != 'translator':
            self.tabs.setCurrentIndex(3)
        self.translate_text(self.tr_in.toPlainText())

    def translate_text(self, text: str):
        text = (text or '').strip()
        if not text:
            return
        if not self.svc or not self.svc.available():
            self.view.setHtml(htmlgen.wrap(htmlgen.translator_block(text, None, 'پوشه‌ی بسته‌های ترجمه از تنظیمات انتخاب نشده یا بسته‌ای در آن نیست.', ''), self.dark)); return
        if len(text.split()) > MAX_TRANSLATOR_WORDS:                      # ConfigConstKt.MAX_TRANSLATOR_WORDS
            QMessageBox.warning(self, 'متن طولانی است', 'حداکثر %d واژه مجاز است.' % MAX_TRANSLATOR_WORDS); return
        self.status.setText('در حال ترجمه…')
        self.view.setHtml(htmlgen.wrap('<p class="rtl">⏳ در حال ترجمه…</p>', self.dark))
        self._worker = TranslateWorker(self.svc, text)
        self._worker.done.connect(self.on_translated)
        self._worker.start()

    def on_translated(self, result, error, direction, source):
        self.load_resources_status_only()
        body = htmlgen.translator_block(source, result, error, direction)
        if result and self.db:                                              # handleOfflineTranslator: بررسی لغت‌بودن متن
            lang = lang_of(source)
            res = self.db.word_exists(lang, source) if len(source) < 100 else None
            if res:
                body += '<hr>' + (htmlgen.english_block(res) if res['lang'] == 'English' else htmlgen.persian_block(res))
        self.view.setHtml(htmlgen.wrap(body, self.dark))
        if result:
            self.ud.history_delete_and_insert(source, category_of(source), result, None, True)
            self.current = {'word': source, 'category': category_of(source), 'meaning': result, 'word_id': None}
            self._update_fav_button()

    def load_resources_status_only(self):
        self.status.setText('   |   '.join(['دیتابیس: ' + ('آماده' if self.db else 'انتخاب نشده'),
                                            'مترجم: ' + (', '.join(x.replace('>', '→') for x in self.svc.available()) if self.svc and self.svc.available() else 'بسته‌ای پیدا نشد')]))

    # ----------------------------------------------------------------- لینک‌ها، صوت، علاقه‌مندی
    def on_anchor(self, url: QUrl):
        s = url.toString()
        if s.startswith('fdword://'):
            w = urllib.parse.unquote(s[len('fdword://'):])
            self.search.blockSignals(True); self.search.setText(w); self.search.blockSignals(False)
            self.tabs.setCurrentIndex(0)
            self.refresh_list()
            lang = lang_of(w)
            if self.db:
                res = self.db.word_exists(lang, trim_lower(w) or w)
                if res: self.show_word({'word': res['word'], 'word_id': res['word_id']})
                else: self.view.setHtml(htmlgen.wrap(htmlgen.not_found('«%s» در دیتابیس نیست.' % w), self.dark))
        elif s.startswith('sound://'):
            folder, _, fn = s[len('sound://'):].partition('/')
            self.play(htmlgen.AUDIO_BASE + '%s/mp3/%s.mp3' % (folder, fn))
        elif s.startswith('#'):
            self.view.scrollToAnchor(s[1:])

    def play(self, url: str):
        if QMediaPlayer is None:
            import webbrowser; webbrowser.open(url); return
        if self._player is None:
            self._player = QMediaPlayer(self); self._out = QAudioOutput(self); self._player.setAudioOutput(self._out)
        self._player.setSource(QUrl(url)); self._player.play()
        self.statusBar().showMessage('پخش از اینترنت: ' + url, 4000)

    def _update_fav_button(self):
        c = self.current
        self.btn_fav.setText('★' if c and self.ud.fav_is(c['word'], c['category']) else '☆')

    def toggle_fav(self):
        c = self.current
        if not c:
            return
        if self.ud.fav_is(c['word'], c['category']):
            self.ud.fav_remove(c['word'], c['category'])
        else:
            self.ud.fav_add(c['word'], c['category'], c['meaning'], c['word_id'], is_translator=c['word_id'] is None)
        self._update_fav_button()
        if self.mode == 'favourites':
            self.refresh_list()


def main(argv=None):
    app = QApplication(argv or sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    f = QFont(); f.setFamilies(['Vazirmatn', 'Tahoma', 'Segoe UI', 'Noto Sans Arabic', 'DejaVu Sans']); f.setPointSize(10)
    app.setFont(f)
    w = MainWindow()
    w.show()
    return app.exec()
