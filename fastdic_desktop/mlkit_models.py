# -*- coding: utf-8 -*-
"""دانلود و مدیریت مدل‌های ترجمهٔ آفلاین ML Kit (همان مدل‌های Google Translate آفلاین).

منبع دانلود دقیقاً همان سرورهای خود ML Kit است. در کلاس داخلی
``com.google.mlkit.nl.translate.internal.zzu`` (نسخهٔ translate@17.0.1) دو قالب
نشانی وجود دارد:

    https://dl.google.com/translate/offline/%s/high/%s/%s.zip
    https://redirector.gvt1.com/edgedl/translate/offline/%s/high/%s/%s.zip

که با ``("v<V>", "r<RV>", "<pair>")`` پر می‌شوند؛ مثال برای فارسی:

    https://dl.google.com/translate/offline/v5/high/r29/en_fa.zip

متادیتا (``translate_models_metadata.json`` نسخهٔ V=5) عین فایل ``res/raw`` خود
SDK است و برای هر زوج زبان این فیلدها را دارد: ``DL_SZ`` (حجم فایل ZIP دانلودی)،
``SZ`` (حجم باز‌شده)، ``RV`` (ریویژن)، ``HASH`` (SHA-256 بستهٔ دانلودی) و ``CAPS``.
مثل خود ML Kit، هش بستهٔ دانلودشده با HASH بررسی می‌شود و بستهٔ خراب نصب
نمی‌شود (معادل خطای ۱۰۲ یعنی «Hash does not match with expected» در SDK).

چیدمان نصب هم مثل اندروید است:
    <models_root>/<pair>/translate_<src><tgt>/translation_model.pb + *.bipe + resources/
هر بسته هر دو جهت را با هم دارد (مثلاً en_fa شامل translate_enfa و translate_faen
است)، پس انتخاب یک زبان مقصد یعنی فقط یک دانلود برای هر دو جهت.

پس از نصب، ترجمه فقط از کش محلی خوانده می‌شود و اینترنت لازم نیست؛ فقط دریافت
اولیهٔ مدل به اینترنت نیاز دارد.
"""
import hashlib
import json
import os
import shutil
import stat
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, List, Optional, Tuple

from .model_spec import ModelSpec

_HERE = os.path.dirname(os.path.abspath(__file__))
_METADATA_PATH = os.path.join(_HERE, 'data', 'translate_models_metadata.json')

# دو قالب نشانی، عین کلاس zzu در خود ML Kit
_URL_TEMPLATES = (
    'https://dl.google.com/translate/offline/%s/high/%s/%s.zip',
    'https://redirector.gvt1.com/edgedl/translate/offline/%s/high/%s/%s.zip',
)

# زبان‌هایی که در فهرست «زبان مقصد» بالای بقیه می‌آیند (فارسی + پرکاربردها)
PRIORITY_LANGS = ('fa', 'ar', 'de', 'es', 'fr', 'ru', 'zh', 'ja', 'tr', 'hi')

# نام فارسی و بومی هر زبان (کلیدها = کد زبان در متادیتای ML Kit)
LANGUAGE_NAMES: Dict[str, Tuple[str, str]] = {
    'en': ('انگلیسی', 'English'),
    'fa': ('فارسی', 'فارسی'),
    'ar': ('عربی', 'العربية'),
    'de': ('آلمانی', 'Deutsch'),
    'es': ('اسپانیایی', 'Español'),
    'fr': ('فرانسوی', 'Français'),
    'ru': ('روسی', 'Русский'),
    'zh': ('چینی', '中文'),
    'ja': ('ژاپنی', '日本語'),
    'tr': ('ترکی', 'Türkçe'),
    'hi': ('هندی', 'हिन्दी'),
    'af': ('آفریکانس', 'Afrikaans'),
    'be': ('بلاروسی', 'Беларуская'),
    'bg': ('بلغاری', 'Български'),
    'bn': ('بنگالی', 'বাংলা'),
    'ca': ('کاتالان', 'Català'),
    'cs': ('چکی', 'Čeština'),
    'cy': ('ولزی', 'Cymraeg'),
    'da': ('دانمارکی', 'Dansk'),
    'el': ('یونانی', 'Ελληνικά'),
    'eo': ('اسپرانتو', 'Esperanto'),
    'et': ('استونیایی', 'Eesti'),
    'fi': ('فنلاندی', 'Suomi'),
    'ga': ('ایرلندی', 'Gaeilge'),
    'gl': ('گالیسی', 'Galego'),
    'gu': ('گجراتی', 'ગુજરાતી'),
    'ha': ('هائوسی', 'Hausa'),
    'hr': ('کرواتی', 'Hrvatski'),
    'ht': ('کریول هائیتی', 'Kreyòl Ayisyen'),
    'hu': ('مجاری', 'Magyar'),
    'id': ('اندونزیایی', 'Indonesia'),
    'is': ('ایسلندی', 'Íslenska'),
    'it': ('ایتالیایی', 'Italiano'),
    'iw': ('عبری', 'עברית'),
    'ka': ('گرجی', 'ქართული'),
    'kn': ('کنادا', 'ಕನ್ನಡ'),
    'ko': ('کره‌ای', '한국어'),
    'lt': ('لیتوانیایی', 'Lietuvių'),
    'lv': ('لتونیایی', 'Latviešu'),
    'mk': ('مقدونی', 'Македонски'),
    'mr': ('مراتی', 'मराठी'),
    'ms': ('مالایی', 'Melayu'),
    'mt': ('مالتی', 'Malti'),
    'nl': ('هلندی', 'Nederlands'),
    'no': ('نروژی', 'Norsk'),
    'pl': ('لهستانی', 'Polski'),
    'pt': ('پرتغالی', 'Português'),
    'ro': ('رومانیایی', 'Română'),
    'sk': ('اسلواکی', 'Slovenčina'),
    'sl': ('اسلوونیایی', 'Slovenščina'),
    'sq': ('آلبانیایی', 'Shqip'),
    'sv': ('سوئدی', 'Svenska'),
    'sw': ('سواحلی', 'Kiswahili'),
    'ta': ('تامیلی', 'தமிழ்'),
    'te': ('تلوگویی', 'తెలుగు'),
    'th': ('تایلندی', 'ไทย'),
    'tl': ('تاگالوگ', 'Tagalog'),
    'uk': ('اوکراینی', 'Українська'),
    'ur': ('اردو', 'اردو'),
    'vi': ('ویتنامی', 'Tiếng Việt'),
}

_REQUIRED_BIPE_MODELS = (
    'encoder_embed_ids_0',
    'encoder_swizzled_birnn_0',
    'encoder_swizzled_birnn_1',
    'encoder_swizzled_birnn_2',
    'decoder_init_0',
    'decoder_step_embed_ids_0',
    'decoder_step_0',
)

_BLOCK_SIZE = 1024 * 1024
_MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
_MAX_EXTRACTED_BYTES = 1024 * 1024 * 1024


class ModelDownloadError(ValueError):
    """دانلود یا نصب بستهٔ مدل ممکن نشد."""


class DownloadCancelled(Exception):
    """کاربر دانلود را لغو کرد."""


# ------------------------------------------------------------------- متادیتا
def load_metadata() -> dict:
    """فایل متادیتای خود SDK (translate_models_metadata.json نسخهٔ V=5)."""
    with open(_METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def known_languages() -> Tuple[str, ...]:
    """همهٔ زبان‌های بستهٔ PK_HIGH؛ فارسی و پرکاربردها در ابتدای فهرست."""
    meta = load_metadata()
    langs = {lang_for_pair(p) for p in meta['PKG_HIGH']}
    ordered = [l for l in PRIORITY_LANGS if l in langs]
    ordered += sorted(langs - set(ordered))
    return tuple(ordered)


def language_name(lang: str) -> str:
    return LANGUAGE_NAMES.get(lang, (lang, lang))[0]


def language_native(lang: str) -> str:
    return LANGUAGE_NAMES.get(lang, (lang, lang))[1]


def pair_for(lang: str) -> str:
    """نام زوج زبان در متادیتا/URL: دو کد مرتب‌شدهٔ الفبایی با «_» (مثل en_fa، de_en)."""
    return '_'.join(sorted((lang, 'en')))


def lang_for_pair(pair: str) -> str:
    """زبانِ غیرانگلیسیِ زوج (en_fa ← fa)."""
    parts = pair.split('_')
    return parts[0] if parts[1] == 'en' else parts[1]


def package_info(lang: str = None, pair: str = None) -> dict:
    """فیلدهای DL_SZ / SZ / RV / HASH / CAPS برای یک زبان (کپی مستقل)."""
    meta = load_metadata()
    pair = pair or pair_for(lang or 'fa')
    entry = meta['PKG_HIGH'].get(pair)
    if entry is None:
        raise ModelDownloadError('زوج زبان «%s» در متادیتای ML Kit نیست.' % pair)
    info = dict(entry)
    info['pair'] = pair
    return info


def model_urls(pair: str) -> List[str]:
    """نشانی‌های دانلود، دقیقاً مثل zzu: ابتدا dl.google.com و سپس redirector.gvt1.com."""
    info = package_info(pair=pair)
    version, revision = 'v%d' % load_metadata()['V'], 'r%d' % info['RV']
    return [tpl % (version, revision, pair) for tpl in _URL_TEMPLATES]


def format_bytes(size: float) -> str:
    value = float(size)
    for unit in ('بایت', 'کیلوبایت', 'مگابایت', 'گیگابایت'):
        if value < 1024 or unit == 'گیگابایت':
            return ('%.0f %s' % (value, unit)) if unit == 'بایت' else ('%.1f %s' % (value, unit))
        value /= 1024
    return '%.1f گیگابایت' % value


# ------------------------------------------------------------- وضعیت نصب (کش)
def _candidate_dirs(root: str) -> List[str]:
    if not os.path.isdir(root):
        return []
    out = [root]
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p):
            out.append(p)
            for e in sorted(os.listdir(p)):
                p2 = os.path.join(p, e)
                if os.path.isdir(p2):
                    out.append(p2)
    return out


def _scan_pairs(models_root: str) -> Dict[str, dict]:
    """پوشه‌های نصب‌شده را بر اساس زوج زبان گروه می‌کند (عمق حداکثر ۲)."""
    groups: Dict[str, dict] = {}
    for cand in _candidate_dirs(models_root):
        if not os.path.isfile(os.path.join(cand, 'translation_model.pb')):
            continue
        try:
            spec = ModelSpec(cand)
        except Exception:
            continue
        src, tgt = spec.src_lang.lower(), spec.tgt_lang.lower()
        pair = '_'.join(sorted((src, tgt)))
        rec = groups.setdefault(pair, {'directions': {}, 'remove_dirs': set()})
        rec['directions']['%s>%s' % (src, tgt)] = cand
        # پوشه‌ای که با حذفش کل این زوج پاک می‌شود: نزدیک‌ترین پوشه به ریشه
        rel = os.path.relpath(cand, models_root)
        top = cand if rel == os.curdir else os.path.join(models_root, rel.split(os.sep)[0])
        rec['remove_dirs'].add(os.path.normpath(top))
    return groups


def language_status(models_root: str) -> Dict[str, dict]:
    """وضعیت هر زبان برای UI: نصب‌شده/آمادهٔ آفلاین، جهت‌ها، مسیرها و حجم DL_SZ."""
    groups = _scan_pairs(models_root)
    result = {}
    for lang in known_languages():
        pair = pair_for(lang)
        rec = groups.get(pair, {'directions': {}, 'remove_dirs': set()})
        fwd, rev = 'en>%s' % lang, '%s>en' % lang
        info = package_info(pair=pair)
        result[lang] = {
            'lang': lang,
            'pair': pair,
            'directions': dict(rec['directions']),
            'remove_dirs': set(rec['remove_dirs']),
            'ready': fwd in rec['directions'] and rev in rec['directions'],
            'partial': bool(rec['directions']) and not (fwd in rec['directions'] and rev in rec['directions']),
            'DL_SZ': info['DL_SZ'],
            'SZ': info['SZ'],
            'RV': info['RV'],
            'HASH': info['HASH'],
        }
    return result


def installed_languages(models_root: str) -> List[str]:
    """زبان‌هایی که هر دو جهت‌شان آمادهٔ آفلاین است (به‌ترتیب فهرست UI)."""
    status = language_status(models_root)
    return [l for l in known_languages() if status[l]['ready']]


def remove_language(lang: str, models_root: str) -> List[str]:
    """حذف کش محلی یک زبان (معادل «حذف مدل» در ML Kit). مسیرهای حذف‌شده برمی‌گردد."""
    status = language_status(models_root)
    rec = status.get(lang)
    if not rec or not rec['remove_dirs']:
        raise ModelDownloadError('مدلی برای «%s» نصب نشده است.' % language_name(lang))
    root = Path(models_root).expanduser().absolute().resolve()
    removed = []
    for d in sorted(rec['remove_dirs']):
        p = Path(d).absolute()
        # فقط پوشه‌های داخل ریشهٔ مدل‌ها مجاز به حذف‌اند
        if root != p and root not in p.resolve().parents:
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
            removed.append(str(p))
        elif p.exists() or p.is_symlink():
            p.unlink()
            removed.append(str(p))
    if not removed:
        raise ModelDownloadError('حذف مدل «%s» ممکن نشد.' % language_name(lang))
    return removed


# ------------------------------------------------------------------- دانلود
def _open_url(url: str, timeout: int = 45):
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'FastDic-Desktop/1.0 (ML Kit translation model downloader)',
                 'Accept': 'application/zip, application/octet-stream;q=0.9, */*;q=0.1'},
    )
    return urllib.request.urlopen(request, timeout=timeout)


def _download(url: str, destination: Path, expected_size: int,
              progress: Optional[Callable[[int, int], None]] = None,
              cancel: Optional[Callable[[], bool]] = None) -> None:
    if cancel is not None and cancel():
        raise DownloadCancelled()
    try:
        response = _open_url(url)
    except urllib.error.HTTPError as exc:
        raise ModelDownloadError('سرور مدل پاسخ HTTP %d داد.' % exc.code) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ModelDownloadError('اتصال به سرور مدل ناموفق بود: %s' % exc) from exc

    with response:
        final = urlsplit_safe(response.geturl())
        if final is None:
            raise ModelDownloadError('منبع دانلود پس از تغییرمسیر از HTTPS خارج شد.')
        raw_length = response.headers.get('Content-Length')
        try:
            total = int(raw_length) if raw_length else 0
        except (TypeError, ValueError):
            total = 0
        total = total or expected_size                # برای نمایش پیشرفت، به DL_SZ برمی‌گردیم
        if total > _MAX_DOWNLOAD_BYTES:
            raise ModelDownloadError('حجم فایل از حد مجاز (۵۱۲ مگابایت) بیشتر است.')

        received = 0
        with open(destination, 'wb') as output:
            while True:
                if cancel is not None and cancel():
                    raise DownloadCancelled()
                chunk = response.read(_BLOCK_SIZE)
                if not chunk:
                    break
                received += len(chunk)
                if received > _MAX_DOWNLOAD_BYTES:
                    raise ModelDownloadError('حجم دانلود از حد مجاز (۵۱۲ مگابایت) بیشتر شد.')
                output.write(chunk)
                if progress:
                    progress(received, total)
        if received == 0:
            raise ModelDownloadError('سرور، فایل خالی فرستاد.')
        if progress:
            progress(received, total or received)


def urlsplit_safe(url: str) -> Optional[str]:
    """بعد از تغییرمسیرها هم باید HTTPS بماند؛ در غیر این صورت None."""
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    if parts.scheme.lower() != 'https' or not parts.hostname:
        return None
    return url


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(_BLOCK_SIZE), b''):
            digest.update(block)
    return digest.hexdigest()


def _safe_member_parts(name: str) -> Tuple[str, ...]:
    # هر دو سبک اسلش جداکننده است تا آرشیو روی ویندوز هم امن بماند.
    normalized = name.replace('\\', '/')
    if '\x00' in normalized:
        raise ModelDownloadError('ZIP شامل نام فایل نامعتبر است.')
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith('/'):
        raise ModelDownloadError('ZIP شامل مسیر مطلق نامعتبر است.')
    parts = tuple(part for part in path.parts if part not in ('', '.'))
    if (not parts or any(part == '..' or part.rstrip(' .') in ('', '.', '..') for part in parts)
            or any(':' in part for part in parts)):
        raise ModelDownloadError('ZIP شامل مسیر خروج از پوشهٔ مدل است.')
    return parts


def _extract_safely(archive_path: Path, extract_root: Path) -> None:
    try:
        archive = zipfile.ZipFile(archive_path)
    except (zipfile.BadZipFile, OSError) as exc:
        raise ModelDownloadError('فایل دریافتی ZIP معتبر نیست.') from exc

    with archive:
        entries = archive.infolist()
        if not entries:
            raise ModelDownloadError('ZIP مدل خالی است.')
        total_size = 0
        seen = set()
        parsed_entries = []
        for info in entries:
            parts = _safe_member_parts(info.filename)
            normalized = '/'.join(parts)
            if normalized in seen and not info.is_dir():
                raise ModelDownloadError('ZIP شامل نام فایل تکراری است.')
            seen.add(normalized)
            mode = (info.external_attr >> 16) & 0xffff
            if stat.S_ISLNK(mode):
                raise ModelDownloadError('ZIP شامل پیوند نمادین نامعتبر است.')
            if info.file_size < 0:
                raise ModelDownloadError('اندازهٔ یک فایل در ZIP نامعتبر است.')
            total_size += info.file_size
            if total_size > _MAX_EXTRACTED_BYTES:
                raise ModelDownloadError('حجم بازشدهٔ مدل از حد مجاز (۱ گیگابایت) بیشتر است.')
            parsed_entries.append((info, parts))

        extract_root.mkdir(parents=True, exist_ok=True)
        root = extract_root.resolve()
        extracted_bytes = 0
        for info, parts in parsed_entries:
            target = extract_root.joinpath(*parts)
            resolved = target.resolve()
            if os.path.commonpath((str(root), str(resolved))) != str(root):
                raise ModelDownloadError('مسیر یکی از فایل‌های ZIP خارج از پوشهٔ مدل است.')
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                written = 0
                with archive.open(info, 'r') as source, open(target, 'xb') as output:
                    while True:
                        chunk = source.read(_BLOCK_SIZE)
                        if not chunk:
                            break
                        written += len(chunk)
                        extracted_bytes += len(chunk)
                        if written > info.file_size or extracted_bytes > _MAX_EXTRACTED_BYTES:
                            raise ModelDownloadError('حجم واقعی فایل‌های ZIP از حد مجاز بیشتر است.')
                        output.write(chunk)
                if written != info.file_size:
                    raise ModelDownloadError('اندازهٔ واقعی فایل با اندازهٔ اعلام‌شده در ZIP برابر نیست.')
            except ModelDownloadError:
                raise
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                raise ModelDownloadError('بازکردن فایل‌های مدل از ZIP ناموفق بود.') from exc


def _check_direction_folder(folder: Path) -> Tuple[str, str]:
    """اعتبارسنجی یک پوشهٔ جهت (translate_*) بر اساس translation_model.pb و BIPEها."""
    try:
        spec = ModelSpec(str(folder))
    except Exception as exc:
        raise ModelDownloadError('فایل translation_model.pb قابل‌خواندن نیست.') from exc

    for name in _REQUIRED_BIPE_MODELS:
        if name not in spec.files:
            raise ModelDownloadError('مدل ناقص است؛ فایل %s در بسته معرفی نشده.' % name)

    referenced = set(spec.files.values())
    referenced.update((spec.src_model, spec.src_vocab, spec.tgt_model, spec.tgt_vocab))
    resolved_root = folder.resolve()
    for relative_name in referenced:
        try:
            parts = _safe_member_parts(relative_name)
            asset = folder.joinpath(*parts)
            resolved = asset.resolve(strict=True)
        except (OSError, RuntimeError, ModelDownloadError) as exc:
            raise ModelDownloadError('مسیر یکی از فایل‌های مدل نامعتبر یا مفقود است.') from exc
        if os.path.commonpath((str(resolved_root), str(resolved))) != str(resolved_root) or not resolved.is_file():
            raise ModelDownloadError('یکی از فایل‌های مدل خارج از بسته است یا فایل معمولی نیست.')

    for name in _REQUIRED_BIPE_MODELS:
        asset = folder / spec.files[name]
        try:
            with open(asset, 'rb') as model_file:
                header = model_file.read(8)
        except OSError as exc:
            raise ModelDownloadError('خواندن فایل مدل %s ممکن نیست.' % name) from exc
        if len(header) < 8 or header[4:8] != b'BIPE':
            raise ModelDownloadError('فایل %s فرمت BIPE معتبر ندارد.' % name)
    return spec.src_lang.lower(), spec.tgt_lang.lower()


def _locate_package(extract_root: Path, expected_pair: str) -> Path:
    """ریشهٔ بسته را پیدا و اعتبارسنجی می‌کند؛ ZIP ممکن است یک پوشهٔ پوششی داشته باشد."""
    candidates = [p for p in extract_root.rglob('translation_model.pb') if p.is_file()]
    if not candidates:
        raise ModelDownloadError('در بستهٔ دریافتی هیچ translation_model.pb پیدا نشد.')
    package_root = os.path.commonpath([str(p.parent.resolve()) for p in candidates])

    seen_directions = set()
    for pb in candidates:
        folder = pb.parent
        src, tgt = _check_direction_folder(folder)
        pair = '_'.join(sorted((src, tgt)))
        if pair != expected_pair:
            raise ModelDownloadError('این بسته برای «%s» است، نه «%s».' % (pair, expected_pair))
        seen_directions.add('%s>%s' % (src, tgt))
    if not seen_directions:
        raise ModelDownloadError('بستهٔ دریافتی هیچ جهت ترجمه‌ای ندارد.')
    return Path(package_root)


def download_package(lang: str, models_root: str,
                     progress: Optional[Callable[[int, int], None]] = None,
                     cancel: Optional[Callable[[], bool]] = None,
                     expected_hash: Optional[str] = None) -> str:
    """دانلود بستهٔ زبان از سرورهای ML Kit، بررسی SHA-256 و نصب اتمی در کش محلی.

    هر بسته هر دو جهت (X→en و en→X) را دارد. خروجی: پوشهٔ نصب‌شده.
    """
    pair = pair_for(lang)
    info = package_info(pair=pair)
    root = Path(models_root).expanduser().absolute()
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not root.is_dir():
            raise OSError('not a directory')
    except OSError as exc:
        raise ModelDownloadError('پوشهٔ ذخیرهٔ مدل قابل‌استفاده نیست: %s' % exc) from exc

    work = Path(tempfile.mkdtemp(prefix='.mlkit-download-', dir=str(root)))
    target = root / pair
    staged = root / ('.%s-install-%s' % (pair, uuid.uuid4().hex))
    backup = root / ('.%s-backup-%s' % (pair, uuid.uuid4().hex))
    try:
        zip_path = work / (pair + '.zip')
        last_error: Optional[ModelDownloadError] = None
        for url in model_urls(pair):                     # اول dl.google.com، بعد redirector
            try:
                _download(url, zip_path, info['DL_SZ'], progress=progress, cancel=cancel)
                last_error = None
                break
            except DownloadCancelled:
                raise
            except ModelDownloadError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error

        # همان بررسی هش خود ML Kit (ModelUtils.zza → خطای ۱۰۲ در صورت مغایرت)
        digest = _sha256_file(zip_path)
        wanted = (expected_hash or info['HASH']).lower()
        if digest != wanted:
            raise ModelDownloadError(
                'هش بستهٔ دانلودشده با متادیتای ML Kit نمی‌خواند (SHA-256=%s…، انتظار %s…). '
                'دریافت دوباره را امتحان کنید.' % (digest[:12], wanted[:12]))

        extract_root = work / 'contents'
        _extract_safely(zip_path, extract_root)
        package_root = _locate_package(extract_root, pair)
        shutil.copytree(package_root, staged, symlinks=False)

        had_existing = target.exists() or target.is_symlink()
        if had_existing:
            os.replace(target, backup)
        try:
            os.replace(staged, target)
        except Exception:
            if had_existing and backup.exists() and not target.exists():
                os.replace(backup, target)
            raise
        if backup.exists() or backup.is_symlink():
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            else:
                backup.unlink()
        return str(target)
    except DownloadCancelled:
        raise
    except ModelDownloadError:
        raise
    except (OSError, shutil.Error, ValueError, zipfile.BadZipFile) as exc:
        raise ModelDownloadError('نصب بستهٔ مدل ناموفق بود: %s' % exc) from exc
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if staged.exists() or staged.is_symlink():
            if staged.is_dir() and not staged.is_symlink():
                shutil.rmtree(staged, ignore_errors=True)
            else:
                staged.unlink(missing_ok=True)
