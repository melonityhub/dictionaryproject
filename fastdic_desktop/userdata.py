# -*- coding: utf-8 -*-
"""تاریخچه و علاقه‌مندی‌ها — معادل FDHistory / FDFavourite / FDFavouriteFolder (Couchbase Lite در اندروید)
که این‌جا با یک SQLite محلی جایگزین شده است (همگام‌سازی ابری Parse/Couchbase پیاده نشده)."""
import json
import os
import sqlite3
import time
from typing import List, Optional

HISTORY_MAX = 100          # FDHistory.deleteOldHistory: بیش از ۱۰۰ سند ⇒ قدیمی‌ها حذف می‌شوند


def app_dir() -> str:
    d = os.path.join(os.path.expanduser('~'), '.fastdic_desktop')
    os.makedirs(d, exist_ok=True)
    return d


def default_models_dir() -> str:
    """Writable default location for model bundles downloaded by the app."""
    return os.path.join(app_dir(), 'models')


class Settings:
    def __init__(self, path=None):
        self.path = path or os.path.join(app_dir(), 'settings.json')
        try:
            self.data = json.load(open(self.path, encoding='utf8'))
        except Exception:
            self.data = {}

    def get(self, k, default=None):
        return self.data.get(k, default)

    def set(self, k, v):
        self.data[k] = v
        json.dump(self.data, open(self.path, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


class UserData:
    def __init__(self, path=None):
        self.con = sqlite3.connect(path or os.path.join(app_dir(), 'user.sqlite'), check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.executescript("""
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL, category INTEGER NOT NULL,
            meaning TEXT, word_id INTEGER, is_translator INTEGER DEFAULT 0, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS folders(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS favourites(id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL, category INTEGER NOT NULL,
            meaning TEXT, word_id INTEGER, folder_id INTEGER, created_at REAL NOT NULL, is_translator INTEGER DEFAULT 0, UNIQUE(word, category, folder_id));
        """)
        self.con.commit()

    # ---- تاریخچه ----
    def history_delete_and_insert(self, word, category, meaning, word_id=None, is_translator=False):
        if not word:
            return
        self.con.execute("DELETE FROM history WHERE word=? AND category=?", (word, category))
        self.con.execute("INSERT INTO history(word,category,meaning,word_id,is_translator,created_at) VALUES(?,?,?,?,?,?)",
                         (word, category, meaning, word_id, int(is_translator), time.time()))
        n = self.con.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        if n >= HISTORY_MAX:
            self.con.execute("DELETE FROM history WHERE id IN (SELECT id FROM history ORDER BY created_at ASC LIMIT ?)", (n - HISTORY_MAX,))
        self.con.commit()

    def history_search(self, prefix: str, category: int, limit: int = 2) -> List[dict]:
        """FDHistory.search: category برابر، word LIKE 'prefix%'، جدیدترین‌ها اول، سقف limit."""
        rows = self.con.execute("SELECT * FROM history WHERE category=? AND word LIKE ? ORDER BY created_at DESC LIMIT ?",
                                (category, prefix.strip() + '%', limit)).fetchall()
        return [self._h(r) for r in rows]

    def history_latest(self, limit=50) -> List[dict]:
        return [self._h(r) for r in self.con.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))]

    def history_clear(self):
        self.con.execute("DELETE FROM history"); self.con.commit()

    @staticmethod
    def _h(r):
        return {'word': r['word'], 'category': r['category'], 'meaning': r['meaning'], 'word_id': r['word_id'],
                'is_history': True, 'is_translator': bool(r['is_translator'])}

    # ---- علاقه‌مندی‌ها ----
    def folders(self) -> List[dict]:
        return [dict(r) for r in self.con.execute("SELECT * FROM folders ORDER BY name")]

    def add_folder(self, name: str) -> int:
        self.con.execute("INSERT OR IGNORE INTO folders(name) VALUES(?)", (name,)); self.con.commit()
        return self.con.execute("SELECT id FROM folders WHERE name=?", (name,)).fetchone()[0]

    def fav_add(self, word, category, meaning, word_id=None, folder_id: Optional[int] = None, is_translator=False):
        self.con.execute("INSERT OR REPLACE INTO favourites(word,category,meaning,word_id,folder_id,created_at,is_translator) VALUES(?,?,?,?,?,?,?)",
                         (word, category, meaning, word_id, folder_id, time.time(), int(is_translator))); self.con.commit()

    def fav_remove(self, word, category):
        self.con.execute("DELETE FROM favourites WHERE word=? AND category=?", (word, category)); self.con.commit()

    def fav_is(self, word, category) -> bool:
        return self.con.execute("SELECT 1 FROM favourites WHERE word=? AND category=?", (word, category)).fetchone() is not None

    def fav_list(self, folder_id: Optional[int] = None) -> List[dict]:
        if folder_id is None:
            rows = self.con.execute("SELECT * FROM favourites ORDER BY created_at DESC")
        else:
            rows = self.con.execute("SELECT * FROM favourites WHERE folder_id=? ORDER BY created_at DESC", (folder_id,))
        return [{'word': r['word'], 'category': r['category'], 'meaning': r['meaning'], 'word_id': r['word_id'],
                 'is_history': False, 'is_translator': bool(r['is_translator'])} for r in rows]
