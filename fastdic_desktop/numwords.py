# -*- coding: utf-8 -*-
"""تبدیل عدد به حروف (انگلیسی/فارسی). در اپ اندروید این کار را ماژول بیرونی com.fastdic...fdnumberstowords می‌کند
که داخل آرشیو نبود؛ این‌جا نسخه‌ی ساده‌ی خودم است (فقط عدد صحیح)."""
_ONES = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
         'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
_SCALE = ['', 'thousand', 'million', 'billion', 'trillion']


def _en_below_1000(n):
    out = []
    if n >= 100:
        out.append(_ONES[n // 100] + ' hundred'); n %= 100
    if n >= 20:
        out.append(_TENS[n // 10] + ('-' + _ONES[n % 10] if n % 10 else ''))
    elif n > 0 or not out:
        out.append(_ONES[n])
    return ' '.join(out)


def en_words(n: int) -> str:
    if n < 0:
        return 'minus ' + en_words(-n)
    if n == 0:
        return 'zero'
    parts, i = [], 0
    while n:
        n, r = divmod(n, 1000)
        if r:
            parts.append(_en_below_1000(r) + (' ' + _SCALE[i] if _SCALE[i] else ''))
        i += 1
    return ' '.join(reversed(parts))


_FA1 = ['صفر', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه', 'ده', 'یازده', 'دوازده', 'سیزده', 'چهارده',
        'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده']
_FA10 = ['', '', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
_FA100 = ['', 'صد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
_FAS = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون']


def _fa_below_1000(n):
    parts = []
    if n >= 100:
        parts.append(_FA100[n // 100]); n %= 100
    if n >= 20:
        parts.append(_FA10[n // 10]); n %= 10
        if n:
            parts.append(_FA1[n])
    elif n > 0:
        parts.append(_FA1[n])
    return ' و '.join(parts)


def fa_words(n: int) -> str:
    if n < 0:
        return 'منفی ' + fa_words(-n)
    if n == 0:
        return 'صفر'
    parts, i = [], 0
    while n:
        n, r = divmod(n, 1000)
        if r:
            parts.append(_fa_below_1000(r) + (' ' + _FAS[i] if _FAS[i] else ''))
        i += 1
    return ' و '.join(reversed(parts))


def is_integer_text(s: str) -> bool:
    t = s.strip().translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))
    return t.lstrip('-').isdigit() and 0 < len(t) <= 15


def to_int(s: str) -> int:
    return int(s.strip().translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')))
