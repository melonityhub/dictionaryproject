# -*- coding: utf-8 -*-
"""ساخت HTML نتیجه — هم‌ساختار با utils/FDHtml.java (ترتیب بخش‌ها: معنی+جمله‌ها، هم‌معنی/متضاد،
فعل‌های عبارتی، هم‌نشینی‌ها، اصطلاح‌ها، خانواده‌ی واژه). CSS اصلی (assets/css/style-results.css) داخل
آرشیو نبود؛ استایل زیر ساده‌شده است و با QTextBrowser سازگار است."""
import html
import urllib.parse
from typing import Optional

from . import fd_data as D

e = html.escape
AUDIO_BASE = 'http://cdn.fastdic.com/c-en-audios/'        # ConfigConstKt.AUDIO_HELP_FILE_BASE_URL


def _css(dark: bool) -> str:
    bg, fg, mut, card, acc = (('#1e1f22', '#e6e6e6', '#9aa0a6', '#2a2c30', '#6ea8fe') if dark
                              else ('#ffffff', '#202124', '#5f6368', '#f4f6f8', '#1a73e8'))
    return f"""
    body {{ background:{bg}; color:{fg}; font-family:'Vazirmatn','Tahoma','Segoe UI',sans-serif; font-size:14px; }}
    h1 {{ font-size:22px; margin:6px 0; }} h2 {{ font-size:16px; color:{acc}; margin:14px 0 6px 0; }}
    a {{ color:{acc}; text-decoration:none; }}
    .menu a {{ margin:0 6px; }} .pos {{ color:{mut}; font-size:12px; }}
    .p {{ background:{card}; padding:1px 6px; }} .cefr {{ background:{acc}; color:#fff; padding:1px 6px; }}
    .tag {{ color:{mut}; font-size:12px; }} .meaning {{ margin:8px 0; }}
    .sent-en {{ color:{fg}; }} .sent-fa {{ color:{mut}; }}
    .box {{ background:{card}; padding:8px; margin:6px 0; }}
    .ltr {{ direction:ltr; text-align:left; }} .rtl {{ direction:rtl; text-align:right; }}
    .err {{ color:#d93025; }}
    """


def _wl(word: str) -> str:
    """لینک لغت (fdword://) — کلیک روی آن همان لغت را باز می‌کند."""
    return '<a href="fdword://%s">%s</a>' % (urllib.parse.quote(word, safe=''), e(word))


def _pos_html(pos_list) -> str:                         # generateEnglishPos (حداکثر ۶ مورد، به‌ترتیب معکوس)
    if not pos_list or len(pos_list) > 6:
        return ''
    return ' '.join('<span class="p" title="%s">%s</span>' % (e(p['equiv'] or ''), e(p['pos'] or '')) for p in reversed(pos_list))


def _cefr(c) -> str:
    return ' <span class="cefr" title="A1 مبتدی · A2 ابتدایی · B1 متوسط · B2 بالاتر از متوسط · C1 پیشرفته · C2 مسلط">%s</span>' % e(c) if c else ''


def _countable(v) -> str:
    return {0: 'uncountable', 1: 'countable', 2: 'countable uncountable'}.get(v, '') if v is not None else ''


def _formal(v) -> str:
    return {0: 'informal', 1: 'formal'}.get(v, '') if v is not None else ''


def _british(v) -> str:
    return {0: 'انگلیسی بریتانیایی', 1: 'انگلیسی آمریکایی'}.get(v, '') if v is not None else ''


def _sentences(sents, en_first=True) -> str:
    if not sents:
        return ''
    out = ['<div>']
    for s in sents[:3] if False else sents:
        en, fa = s.get('english') or '', s.get('persian') or ''
        out.append('<p class="ltr sent-en">• %s</p>' % e(en) if en else '')
        out.append('<p class="rtl sent-fa">%s</p>' % e(fa) if fa else '')
    out.append('</div>')
    return ''.join(out)


def _audio_links(res) -> str:                           # generateEnglishAudios
    out = []
    for label, key, folder in (('American', 'american', 'us'), ('British', 'british', 'uk')):
        for a in res['audios'][key]:
            ph = a.get('phonetic') or ''
            fn = a.get('filename')
            if fn:
                out.append('<span class="ltr">%s /%s/ <a href="sound://%s/%s">🔊</a></span>' %
                           (label, e(ph), folder, urllib.parse.quote(fn, safe='')))
            elif ph:
                out.append('<span class="ltr tag">%s: %s</span>' % (label, e(ph)))
    return ' &nbsp; '.join(out)


def english_block(res: dict) -> str:
    """بدنه‌ی نتیجه‌ی انگلیسی (generateEnglishBlock) + منو."""
    parts = []
    menu = []
    # --- معنی‌ها و جمله‌ها
    menu.append('<a href="#meanings-sentences">%s</a>' % 'معنی و جمله‌ها')
    parts.append('<a name="meanings-sentences"></a><h2>معنی «%s»</h2>' % e(res['word']))
    forms = [('گذشته‌ی ساده (simple past)', res['simple_past']), ('اسم مفعول (past participle)', res['past_participle']),
             ('مصدر (infinitive)', res['infinitive']), ('سوم شخص مفرد', res['third_person_singular']),
             ('وجه وصفی حال (-ing)', res['present_participle']), ('جمع (plural)', res['plural']),
             ('برتر (comparative)', res['comparative']), ('برترین (superlative)', res['superlative'])]
    shown = [(l, w) for l, w in forms if w]
    if shown:
        parts.append('<div class="box rtl">' + ' · '.join('%s: %s' % (l, _wl(w)) for l, w in shown) + '</div>')
    if res.get('description_html'):
        parts.append('<div class="box rtl"><b>توضیح</b>%s</div>' % res['description_html'])
    au = _audio_links(res)
    if au:
        parts.append('<p>%s</p>' % au)
    for m in res['meanings']:
        tags = ' '.join(x for x in (_formal(m['formal']), _countable(m['countable'])) if x)
        parts.append('<div class="meaning rtl"><div class="pos ltr">%s %s %s</div><p>%s %s %s</p>%s%s</div>' % (
            e(tags), _pos_html(m['pos']), _cefr(m['cefr']),
            '<span class="tag">%s</span>' % e(_british(m['british'])) if _british(m['british']) else '',
            ' '.join('<span class="tag">[%s]</span>' % e(c) for c in m['categories'] if c),
            e(m['meaning'] or ''),
            '<div class="box">%s</div>' % m['description_html'] if m.get('description_html') else '',
            _sentences(m['sentences'])))
    # --- هم‌معنی/متضاد
    if res['syn_ant']:
        menu.append('<a href="#synonyms-antonyms">هم‌معنی و متضاد</a>')
        parts.append('<a name="synonyms-antonyms"></a><h2>هم‌معنی‌ها و متضادها</h2>')
        for s in res['syn_ant']:
            parts.append('<div class="box ltr"><span class="p">%s</span> %s' % (e(s.get('pos') or ''), e(s.get('definitions') or '')))
            if s.get('synonyms'):
                parts.append('<br><b>Synonyms:</b> ' + ', '.join(_wl(w.strip()) for w in s['synonyms'].split(',') if w.strip()))
            if s.get('antonyms'):
                parts.append('<br><b>Antonyms:</b> ' + ', '.join(_wl(w.strip()) for w in s['antonyms'].split(',') if w.strip()))
            parts.append('</div>')
    for key, title, anchor in (('phrasal_verbs', 'Phrasal verbs', 'phrasal-verbs'), ('collocations', 'Collocations', 'collocations'),
                               ('idioms', 'Idioms', 'idioms')):
        items = res['idioms'][key]
        if items:
            menu.append('<a href="#%s">%s</a>' % (anchor, title))
            parts.append('<a name="%s"></a><h2 class="ltr">%s</h2>' % (anchor, title))
            for it in items:
                parts.append('<div class="box"><p class="ltr">%s</p>%s</div>' % (
                    _wl(it['word']), ''.join('<p class="rtl sent-fa">%s</p>' % e(m or '') for m in it['meanings'])))
    fam = res['family']
    if fam:
        menu.append('<a href="#word-family">خانواده‌ی واژه</a>')
        parts.append('<a name="word-family"></a><h2>خانواده‌ی واژه</h2><div class="box ltr">')
        for k, posid in (('noun', 1), ('adjective', 7), ('verb_transitive', 5), ('verb_intransitive', 6), ('adverb', 8)):
            if fam.get(k):
                parts.append('<p><span class="p">%s</span> %s</p>' % (e(D.POS_EN[posid]), ', '.join(_wl(w) for w in fam[k])))
        parts.append('</div>')
    return '<div class="menu rtl">%s</div>' % ' | '.join(menu) + ''.join(parts)


def persian_block(res: dict) -> str:
    """generatePersianBlock: معنی‌ها (+ تلفظ لاتین)، جمله‌ها، هم‌معنی/متضاد."""
    parts = ['<div class="menu rtl"><a href="#meanings-sentences">معنی و جمله‌ها</a>%s</div>' %
             (' | <a href="#synonyms-antonyms">هم‌معنی و متضاد</a>' if res['syn_ant'] else '')]
    parts.append('<a name="meanings-sentences"></a><h2 class="rtl">معنی «%s»</h2>' % e(res['word']))
    if res.get('description_html'):
        parts.append('<div class="box rtl">%s</div>' % res['description_html'])
    for d in res['details']:
        ph = '<span class="tag ltr">تلفظ /%s/</span>' % e(d['phonetics']) if d['phonetics'] else ''
        cats = ' '.join('<span class="tag">[%s]</span>' % e(c) for c in d['categories'] if c)
        parts.append('<div class="meaning"><div class="pos rtl">%s %s</div><p class="ltr">%s</p>%s%s</div>' % (
            _pos_html(d['pos']), ph + ' ' + cats, e(d['meaning'] or ''),
            '<div class="rtl box">%s</div>' % e(d['persian_meaning']) if d['persian_meaning'] else '',
            _sentences(d['sentences'])))
    if res['syn_ant']:
        parts.append('<a name="synonyms-antonyms"></a><h2 class="rtl">هم‌معنی‌ها و متضادها</h2>')
        for s in res['syn_ant']:
            parts.append('<div class="box rtl">%s</div>' % e(s['text'] or ''))
    return ''.join(parts)


def wrap(body: str, dark=False) -> str:
    return '<html><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>' % (_css(dark), body)


def translator_block(source: str, result: Optional[str], error: Optional[str], direction: str) -> str:
    direction = direction or ''
    """بخش «ترجمه در مترجم» (generateEnglishMeaningForOrder با translateModel)."""
    if error:
        return '<h2 class="rtl">ترجمه</h2><p class="rtl err">%s</p>' % e(error)
    try:
        src, tgt = direction.split('>')
        from .mlkit_models import language_name
        label = '%s → %s' % (language_name(src), language_name(tgt))
    except Exception:
        label = direction.replace('>', ' → ') or 'ذخیره‌شده'
    dst_rtl = direction.split('>')[-1] in ('fa', 'ar', 'ur', 'iw')      # زبان‌های راست‌به‌چپ
    return ('<a name="translate"></a><h2 class="rtl">ترجمه در مترجم <span class="tag">(آفلاین، %s)</span></h2>'
            '<div class="box %s">%s</div>' % (label, 'rtl' if dst_rtl else 'ltr',
                                               e(result or '').replace('\n', '<br>')))


def not_found(message: str, title='موردی پیدا نشد') -> str:   # generateErrorMessage
    return '<h2 class="rtl">%s</h2><p class="rtl">%s</p>' % (e(title), e(message))
