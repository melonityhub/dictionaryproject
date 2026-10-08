# -*- coding: utf-8 -*-
"""
معادل پایتونی FDDatabaseManager / StringUtils / FDLanguageWord / FDSuggestions اپ اندروید.
کوئری‌ها کلمه‌به‌کلمه از سورس جاوا برداشته شده‌اند (نام فایل و خط در توضیح هر تابع).
"""
import re
import sqlite3
from typing import Dict, List, Optional

from . import fd_data as D

CAT_PERSIAN, CAT_ENGLISH = 1, 2          # utils/Category.java

# ---- p000const/ConstKt.java ----
_PERSIAN_LETTERS = set('آبپتثجچحخدذرزژسشصضطظعغفقکكگلمنواأهئيی؟')
_PERSIAN_DIGITS = set('۰۱۲۳۴۵۶۷۸۹')


def lang_of(text: Optional[str]) -> str:
    """FDLanguageWord.find: اگر شمار نویسه‌های فارسی (حرف/رقم) ≥ سایر نویسه‌ها ⇒ Persian."""
    if not text:
        return 'English'
    fa = sum(1 for c in text if c in _PERSIAN_LETTERS or c in _PERSIAN_DIGITS)
    other = len(text) - fa
    return 'Persian' if fa >= other else 'English'


def is_english(text) -> bool:
    return lang_of(text) == 'English'


def is_persian(text) -> bool:
    return lang_of(text) == 'Persian'


def category_of(text) -> int:                      # FDCategory.findLanguage
    return CAT_ENGLISH if is_english(text) else CAT_PERSIAN


_TO_FARSI = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
_TO_EN = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def replace_numbers_to_farsi(s: str) -> str:       # FDLanguageWord.replaceNumbersToFarsi
    return s.translate(_TO_FARSI) if s else ''


def to_english_number(s: str) -> str:
    return s.translate(_TO_EN) if s else ''


def remove_digits(s: Optional[str]) -> str:        # FDLanguageWord.replaceNumbers (ارقام لاتین را حذف می‌کند)
    return re.sub(r'[0-9]', '', s) if s else ''


def char_replacement(s: str) -> str:
    """StringUtils.charReplacement — جایگزینی ترتیبی (۱۲۸ ورودی) شکل‌های نمایشی عربی با حرف استاندارد."""
    out = []
    for ch in s:
        c = ord(ch)
        for i in range(128):
            if c == D.BROKEN_CHARS[i]:
                c = D.CORRECT_CHARS[i]
        out.append(chr(c))
    return ''.join(out)


def trim_lower(s: Optional[str]) -> Optional[str]:   # StringUtils.trimmingAndLowerCaseWords
    if s is None:
        return None
    t = s.strip(''.join(chr(i) for i in range(0, 33)))
    if len(t) > 100:
        return t
    return char_replacement(t).lower()


def pe_to_number(word: str) -> str:                 # StringUtils.peCharacterToNumber
    if not word:
        return ''
    for a, b in D.PE_TO_NUMBER:
        word = word.replace(a, b)
    return word


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


_SQL_EN_DETAIL = ("SELECT w.english_word as english_word, w.english_word_id as english_word_id, w.simple_past as simple_past, "
                  "w.past_participle as past_participle, w.infinitive as infinitive, w.`word_description_html` as word_description_html, "
                  "d.english_detail_id as english_detail_id, COALESCE(d.persian_meaning, '') as pe_meaning, "
                  "d.countable_uncountable as countable_uncountable, d.formal_informal as formal_informal, "
                  "d.british_american as british_american, d.cefr as cefr, w.third_person_singular as third_person_singular, "
                  "w.present_participle as present_participle, w.plural as plural, w.comparative as comparative, "
                  "w.superlative as superlative, d.has_image as has_image, d.description_html as description_html "
                  "FROM english_words w LEFT JOIN english_details d ON w.english_word_id = d.english_word_id "
                  "WHERE {where} ORDER BY d.position, d.english_detail_id")
_SQL_FA_DETAIL = ("SELECT w.persian_word as persian_word, w.persian_word_id as persian_word_id, "
                  "w.`word_description_html` as word_description_html, d.english_meaning as english_meaning, "
                  "COALESCE(d.persian_phonetic, '') as persian_phonetic, COALESCE(d.persian_meaning, '') as persian_meaning, "
                  "d.persian_detail_id as persian_detail_id, d.has_image as has_image "
                  "FROM persian_words w LEFT JOIN persian_details d ON w.persian_word_id = d.persian_word_id "
                  "WHERE {where} ORDER BY d.position, d.persian_detail_id")
_SQL_IDIOM = ("SELECT w.english_word as word, d.english_detail_id as english_detail_id, d.persian_meaning as persian_meaning, "
              "i.english_idiom_id as english_idiom_id, i.english_idiom_word_id as english_idiom_word_id, p.english_pos_id, p.pos "
              "FROM english_idioms i LEFT JOIN english_details d ON i.english_idiom_word_id = d.english_word_id "
              "LEFT JOIN english_words w ON i.english_idiom_word_id = w.english_word_id "
              "LEFT JOIN english_pos p ON p.english_detail_id = d.english_detail_id "
              "WHERE i.english_word_id = ? AND pos = ? "
              "GROUP BY p.pos, w.english_word, d.english_detail_id, d.persian_meaning, i.english_idiom_id, "
              "i.english_idiom_word_id, p.english_pos_id "
              "ORDER BY i.position, i.english_idiom_id, d.position, d.english_detail_id LIMIT 20")


class FDDatabase:
    def __init__(self, path: str):
        self.path = path
        self.con = sqlite3.connect('file:%s?mode=ro' % path.replace('\\', '/'), uri=True, check_same_thread=False)
        self.con.row_factory = sqlite3.Row

    def q(self, sql, args=()):
        try:
            return self.con.execute(sql, args).fetchall()
        except sqlite3.Error:
            return []

    def check(self) -> bool:                      # FDMainDatabaseHelper.checkDataBase
        return bool(self.q("SELECT 1 FROM english_words LIMIT 1"))

    # ------------------------------------------------------------ جستجو (FDDatabaseManager.search)
    def meanings_joined(self, lang: str, word_id: int, sep: str) -> str:
        return sep.join(self.get_meanings(lang, word_id))

    def get_meanings(self, lang: str, word_id: int) -> List[str]:   # getMeanings (خط 2061)
        if lang == 'English':
            rows = self.q("SELECT persian_meaning as meaning FROM english_details WHERE english_word_id = ?", (word_id,))
        else:
            rows = self.q("SELECT english_meaning as meaning FROM persian_details WHERE persian_word_id = ?", (word_id,))
        return [r['meaning'] for r in rows if r['meaning'] is not None]

    def search(self, text: str, limit: int = 50) -> List[dict]:
        """خروجی: فهرست ListModel (dict) — همان کوئری‌های GLOB اپ اندروید."""
        w = trim_lower(text)
        if not w:
            return []
        if len(w) >= 100:
            return []
        if is_english(w):
            rows = self.q("SELECT w.english_word AS word, w.english_word_id as word_id, english_word_id_parent as word_id_parent "
                          "FROM english_words w WHERE w.english_word GLOB ? ORDER BY w.english_word LIMIT ?",
                          (_glob_escape(w) + '*', limit))
        else:
            rows = self.q("SELECT w.persian_word AS word, w.persian_word_id as word_id, persian_word_id_parent as word_id_parent "
                          "FROM persian_words w WHERE w.word_in_number GLOB ? ORDER BY length(w.word_in_number) LIMIT ?",
                          (pe_to_number(w) + '*', limit))
        out = []
        for r in rows:
            parent = r['word_id_parent']
            m = {'word': r['word'], 'word_id': parent if parent is not None else r['word_id'],
                 'category': category_of(w), 'is_history': False, 'is_translator': False, 'is_parent_redirect': parent is not None}
            if parent is None:
                lang = lang_of(m['word'])
                m['meaning'] = self.meanings_joined(lang, m['word_id'], '، ' if is_english(w) else ', ')
            else:
                m['meaning'] = ('برای دیدن ترجمه روی متن کلیک کنید' if is_english(w)
                                else 'برای دیدن ترجمه روی متن کلیک کنید')   # R.string.fa_to_see_.. / en_to_see_..
            out.append(m)
        return out

    def levenshtein_suggestions(self, text: str) -> List[dict]:       # FDSuggestions.getLevenshtein
        t = text.strip()
        if not t or len(t) >= 100:
            return []
        n = len(t)
        pre = t[:2]
        suf = t[-2:]
        mid = t[:n // 2][-2:] if n % 2 == 0 else t[:(n + 1) // 2][-2:]
        if is_english(t):
            sql = ("SELECT english_word AS word, english_word_id AS id FROM english_words WHERE LENGTH(english_word) < ? "
                   "AND (english_word GLOB ? OR english_word GLOB ? OR english_word GLOB ?)")
        else:
            sql = ("SELECT persian_word AS word, persian_word_id AS id FROM persian_words WHERE LENGTH(persian_word) < ? "
                   "AND (persian_word GLOB ? OR persian_word GLOB ? OR persian_word GLOB ?)")
        rows = self.q(sql, (n * 2, _glob_escape(pre) + '*', '*' + _glob_escape(mid) + '*', '*' + _glob_escape(suf)))
        cands = []
        for r in rows:
            d = levenshtein(t, r['word'])
            if d <= 2:
                cands.append((d, r['word'], r['id']))
        cands.sort(key=lambda x: x[0])
        out = []
        for d, word, wid in cands:
            lang = lang_of(word)
            meaning = ('، ' if is_english(word) else ', ').join(self.get_word_meanings(lang, wid))
            if meaning != '':
                out.append({'word': word, 'word_id': wid, 'meaning': meaning, 'levenshtein': d, 'category': category_of(word),
                            'is_history': False, 'is_translator': False})
                if len(out) >= 50:
                    break
        return out

    def get_word_meanings(self, lang: str, word_id: int) -> List[str]:    # getWordMeanings (خط 1201)
        if lang == 'English':
            rows = self.q("SELECT persian_meaning as meaning FROM english_details WHERE english_word_id = ? ORDER BY position, english_detail_id", (word_id,))
        else:
            rows = self.q("SELECT english_meaning as meaning FROM persian_details WHERE persian_word_id = ?", (word_id,))
        return [r['meaning'] for r in rows if r['meaning'] is not None]

    # ------------------------------------------------------------ جزئیات
    def get_word_by_id(self, lang: str, wid) -> Optional[str]:           # getWordById (خط 1130)
        if wid is None:
            return None
        sql = ("SELECT english_word AS word FROM english_words WHERE english_word_id = ?" if lang == 'English'
               else "SELECT persian_word AS word FROM persian_words WHERE persian_word_id = ?")
        r = self.q(sql, (wid,))
        return r[0]['word'] if r else None

    def get_word_id_parent(self, lang: str, word: str) -> Optional[int]:  # getWordIdParent (خط 1989)
        if not word:
            return None
        if lang == 'English':
            r = self.q("SELECT english_word_id_parent FROM english_words WHERE english_word = ?", (word.strip().lower(),))
            return r[0]['english_word_id_parent'] if r else None
        r = self.q("SELECT persian_word_id_parent FROM persian_words WHERE persian_word = ?", (word.strip(),))
        return r[0]['persian_word_id_parent'] if r else None

    def get_pos(self, lang: str, detail_id: int) -> List[dict]:           # getPos (خط 1694)
        if lang == 'English':
            rows = self.q("SELECT pos FROM english_pos WHERE english_detail_id = ?", (detail_id,))
            return [{'pos': D.POS_EN.get(r['pos']), 'equiv': D.POS_EN_TO_FA.get(r['pos'])} for r in rows]
        rows = self.q("SELECT pos FROM persian_pos WHERE persian_detail_id = ?", (detail_id,))
        return [{'pos': D.POS_FA.get(r['pos']), 'equiv': D.POS_FA_TO_EN.get(r['pos'])} for r in rows]

    def get_sentences(self, lang: str, detail_id: int) -> List[dict]:      # getSentences (خط 1771)
        if lang == 'English':
            rows = self.q("SELECT english_sentence_id, english_sentence, persian_sentence FROM english_sentences "
                          "WHERE english_detail_id = ? ORDER BY position, english_sentence_id", (detail_id,))
        else:
            rows = self.q("SELECT persian_sentence_id, english_sentence, persian_sentence FROM persian_sentences "
                          "WHERE persian_detail_id = ? ORDER BY position, persian_sentence_id", (detail_id,))
        return [{'english': r['english_sentence'], 'persian': r['persian_sentence']} for r in rows]

    def get_categories(self, lang: str, detail_id: int) -> List[str]:      # getCategories (خط 1224)
        sql = ("SELECT category FROM english_categories WHERE english_detail_id = ?" if lang == 'English'
               else "SELECT category FROM persian_categories WHERE persian_detail_id = ?")
        return [D.CATEGORY_NAMES.get(r['category'], '') for r in self.q(sql, (detail_id,)) if r['category'] is not None]

    def get_audios(self, word_id: int) -> dict:                             # getAudios (خط 1562)
        def clean(fn):
            if fn is None:
                return None
            fn = ''.join(ch for ch in fn if ch.isprintable() or ch.isspace())
            return fn.strip()
        am = [{'filename': clean(r['filename']), 'phonetic': r['phonetic']} for r in
              self.q("SELECT filename, phonetic FROM english_american_audios WHERE english_word_id = ?", (word_id,))]
        br = [{'filename': clean(r['filename']), 'phonetic': r['phonetic']} for r in
              self.q("SELECT filename, phonetic FROM english_british_audios WHERE english_word_id = ?", (word_id,))]
        return {'american': am, 'british': br}

    def get_en_syn_ant(self, word_id: int) -> List[dict]:                   # getEnglishSynonymsAntonyms (خط 1724)
        rows = self.q("SELECT english_synonyms_antonyms_id, definitions, synonyms, antonyms, pos FROM english_synonyms_antonyms "
                      "WHERE english_word_id = ? ORDER BY position, english_synonyms_antonyms_id", (word_id,))
        return [{'pos': r['pos'], 'synonyms': r['synonyms'], 'antonyms': r['antonyms'], 'definitions': r['definitions']} for r in rows]

    def get_fa_syn_ant(self, word_id: int) -> List[dict]:                   # getSynonymsAntonyms (خط 1748)
        rows = self.q("SELECT persian_synonyms_antonyms_id, synonym_antonym FROM persian_synonyms_antonyms "
                      "WHERE persian_word_id = ? ORDER BY position, persian_synonyms_antonyms_id", (word_id,))
        return [{'text': r['synonym_antonym']} for r in rows]

    def _idioms(self, word_id: int, pos: int) -> List[dict]:
        rows = self.q(_SQL_IDIOM, (word_id, pos))
        groups: Dict[int, dict] = {}
        for r in rows:                                                  # groupIdiomMeanings (خط 1954)
            g = groups.setdefault(r['english_idiom_id'], {'word': r['word'], 'id': r['english_idiom_id'], 'meanings': []})
            g['meanings'].append(r['persian_meaning'])
        return list(groups.values())

    def get_idioms(self, word_id: int) -> dict:                             # getEnglishPOSs (خط 1818)
        return {'idioms': self._idioms(word_id, 18), 'collocations': self._idioms(word_id, 19),
                'phrasal_verbs': self._idioms(word_id, 20)}

    def get_word_family(self, word: str) -> dict:                           # getWordFamily (خط 1153)
        rows = self.q("SELECT `word`, `pos` FROM english_word_families_words WHERE english_word_family_id = "
                      "(SELECT english_word_family_id FROM english_word_families_words WHERE word = ? LIMIT 1)", (word,))
        names = {1: 'noun', 7: 'adjective', 5: 'verb_transitive', 6: 'verb_intransitive', 8: 'adverb'}
        fam: Dict[str, List[str]] = {}
        for r in rows:
            k = names.get(r['pos'])
            if k:
                fam.setdefault(k, []).append(r['word'])
        return fam

    # ------------------------------------------------------------ نتیجه‌ی کامل یک لغت
    def english_result(self, where: str, arg) -> Optional[dict]:
        rows = self.q(_SQL_EN_DETAIL.format(where=where), (arg,))
        if not rows:
            return None
        r0 = rows[0]
        res = {'lang': 'English', 'word': r0['english_word'], 'word_id': r0['english_word_id'],
               'past_participle': self.get_word_by_id('English', r0['past_participle']),
               'simple_past': self.get_word_by_id('English', r0['simple_past']),
               'infinitive': self.get_word_by_id('English', r0['infinitive']),
               'third_person_singular': self.get_word_by_id('English', r0['third_person_singular']),
               'present_participle': self.get_word_by_id('English', r0['present_participle']),
               'plural': self.get_word_by_id('English', r0['plural']),
               'comparative': self.get_word_by_id('English', r0['comparative']),
               'superlative': self.get_word_by_id('English', r0['superlative']),
               'description_html': r0['word_description_html'],
               'audios': self.get_audios(r0['english_word_id']),
               'syn_ant': self.get_en_syn_ant(r0['english_word_id']),
               'idioms': self.get_idioms(r0['english_word_id']),
               'family': self.get_word_family(r0['english_word']),
               'meanings': []}
        for r in rows:
            did = r['english_detail_id']
            if did is None:
                continue
            res['meanings'].append({
                'detail_id': did, 'meaning': r['pe_meaning'], 'countable': r['countable_uncountable'],
                'formal': r['formal_informal'], 'british': r['british_american'], 'cefr': r['cefr'],
                'has_image': r['has_image'] == 1, 'description_html': r['description_html'],
                'pos': self.get_pos('English', did), 'sentences': self.get_sentences('English', did),
                'categories': self.get_categories('English', did)})
        return res

    def persian_result(self, where: str, arg) -> Optional[dict]:
        rows = self.q(_SQL_FA_DETAIL.format(where=where), (arg,))
        if not rows:
            return None
        r0 = rows[0]
        res = {'lang': 'Persian', 'word': r0['persian_word'], 'word_id': r0['persian_word_id'],
               'description_html': r0['word_description_html'],
               'syn_ant': self.get_fa_syn_ant(r0['persian_word_id']), 'details': []}
        seen = []
        for r in rows:
            did = r['persian_detail_id']
            if did is None:
                continue
            ph = r['persian_phonetic']
            res['details'].append({
                'detail_id': did, 'meaning': r['english_meaning'], 'persian_meaning': r['persian_meaning'],
                'phonetics': remove_digits(ph), 'has_image': r['has_image'] == 1,
                'pos': self.get_pos('Persian', did), 'sentences': self.get_sentences('Persian', did),
                'categories': self.get_categories('Persian', did)})
        return res

    def detail_by_word_id(self, lang: str, word_id: int) -> Optional[dict]:   # getDetailByWordId (خط 619)
        if lang == 'English':
            return self.english_result("w.english_word_id = ?", word_id)
        return self.persian_result("w.persian_word_id = ?", word_id)

    def detail_by_word(self, lang: str, word: str) -> Optional[dict]:         # getDetailByWordGetOtherFormOfWord (خط 881)
        w = trim_lower(word) or ''
        if not w or len(w) >= 100:
            return None
        if lang == 'English':
            return self.english_result("w.english_word = ?", w.strip().lower())
        return self.persian_result("w.persian_word = ?", w.strip())

    def word_exists(self, lang: str, word: str):
        """برای ترجمه‌ی متن: اگر خود متن یک لغت دیکشنری است همان را نشان بده (getWordIdParent + جزئیات)."""
        parent = self.get_word_id_parent(lang, word)
        if parent is not None:
            return self.detail_by_word_id(lang, parent)
        return self.detail_by_word(lang, word)


def _glob_escape(s: str) -> str:
    """SQLite GLOB: در اپ اندروید escape نمی‌شود (ورودی خام)؛ فقط کاراکترهای ویژه‌ی GLOB را بی‌اثر می‌کنیم
    تا ورودی کاربر نتواند الگو بسازد و برنامه نشکند."""
    return re.sub(r'([*?\[])', r'[\1]', s)
