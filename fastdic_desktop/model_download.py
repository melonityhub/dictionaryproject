# -*- coding: utf-8 -*-
"""Download and safely install compatible offline translation-model ZIP bundles.

The application intentionally accepts a user-supplied HTTPS ZIP URL: ML Kit's
Android model manager is not exposed as a static desktop download endpoint.
"""
import os
import shutil
import stat
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable, Optional, Tuple
from urllib.parse import urlsplit

from .model_spec import ModelSpec

DIRECTIONS = {
    'fa>en': {
        'source': 'fa',
        'target': 'en',
        'folder': 'translate_faen',
        'setting': 'model_url_fa_en',
        'label': 'فارسی → انگلیسی',
    },
    'en>fa': {
        'source': 'en',
        'target': 'fa',
        'folder': 'translate_enfa',
        'setting': 'model_url_en_fa',
        'label': 'انگلیسی → فارسی',
    },
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
    """A source or archive could not be safely installed as a model package."""


def _validate_https_url(url: str) -> str:
    url = (url or '').strip()
    parsed = urlsplit(url)
    if parsed.scheme.lower() != 'https' or not parsed.hostname:
        raise ModelDownloadError('برای دانلود مدل، نشانی مستقیم HTTPS وارد کنید.')
    if parsed.username or parsed.password:
        raise ModelDownloadError('نشانی‌های HTTPS دارای نام کاربری/گذرواژه پشتیبانی نمی‌شوند.')
    return url


def _download_archive(url: str, destination: Path,
                      progress: Optional[Callable[[int, int], None]] = None) -> None:
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'FastDic-Desktop/1.0 model downloader',
                 'Accept': 'application/zip, application/octet-stream;q=0.9, */*;q=0.1'},
    )
    try:
        response = urllib.request.urlopen(request, timeout=45)
    except urllib.error.HTTPError as exc:
        raise ModelDownloadError('منبع مدل پاسخ HTTP %d داد.' % exc.code) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ModelDownloadError('دریافت مدل از منبع ناموفق بود: %s' % exc) from exc

    with response:
        final_url = urlsplit(response.geturl())
        if final_url.scheme.lower() != 'https':
            raise ModelDownloadError('منبع دانلود پس از تغییرمسیر از HTTPS خارج شد.')
        raw_length = response.headers.get('Content-Length')
        try:
            total = int(raw_length) if raw_length else 0
        except (TypeError, ValueError):
            total = 0
        if total < 0 or total > _MAX_DOWNLOAD_BYTES:
            raise ModelDownloadError('حجم فایل فشرده از حد مجاز (۵۱۲ مگابایت) بیشتر است.')

        received = 0
        with open(destination, 'wb') as output:
            while True:
                chunk = response.read(_BLOCK_SIZE)
                if not chunk:
                    break
                received += len(chunk)
                if received > _MAX_DOWNLOAD_BYTES:
                    raise ModelDownloadError('حجم دانلود از حد مجاز (۵۱۲ مگابایت) بیشتر شد.')
                output.write(chunk)
                if progress:
                    progress(received, total)
        if total and received != total:
            raise ModelDownloadError('دانلود ناقص بود؛ اندازه‌ی دریافتی با اندازه‌ی اعلام‌شده برابر نیست.')
        if received == 0:
            raise ModelDownloadError('منبع، فایل خالی فرستاد.')
        if progress:
            progress(received, total or received)


def _safe_member_parts(name: str) -> Tuple[str, ...]:
    # Treat both slash styles as separators so archives remain safe on Windows too.
    normalized = name.replace('\\', '/')
    if '\x00' in normalized:
        raise ModelDownloadError('ZIP شامل نام فایل نامعتبر است.')
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith('/'):
        raise ModelDownloadError('ZIP شامل مسیر مطلق نامعتبر است.')
    parts = tuple(part for part in path.parts if part not in ('', '.'))
    if (not parts or any(part == '..' or part.rstrip(' .') in ('', '.', '..') for part in parts)
            or any(':' in part for part in parts)):
        raise ModelDownloadError('ZIP شامل مسیر خروج از پوشه‌ی مدل است.')
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
                raise ModelDownloadError('اندازه‌ی یک فایل در ZIP نامعتبر است.')
            total_size += info.file_size
            if total_size > _MAX_EXTRACTED_BYTES:
                raise ModelDownloadError('حجم بازشده‌ی مدل از حد مجاز (۱ گیگابایت) بیشتر است.')
            parsed_entries.append((info, parts))

        extract_root.mkdir(parents=True, exist_ok=True)
        root = extract_root.resolve()
        extracted_bytes = 0
        for info, parts in parsed_entries:
            target = extract_root.joinpath(*parts)
            resolved = target.resolve()
            if os.path.commonpath((str(root), str(resolved))) != str(root):
                raise ModelDownloadError('مسیر یکی از فایل‌های ZIP خارج از پوشه‌ی مدل است.')
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
                    raise ModelDownloadError('اندازه‌ی واقعی فایل با اندازه‌ی اعلام‌شده در ZIP برابر نیست.')
            except ModelDownloadError:
                raise
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                raise ModelDownloadError('بازکردن فایل‌های مدل از ZIP ناموفق بود.') from exc


def _validated_package(extract_root: Path, expected_direction: str) -> Path:
    candidates = list(extract_root.rglob('translation_model.pb'))
    if len(candidates) != 1:
        raise ModelDownloadError('ZIP باید دقیقاً یک translation_model.pb داشته باشد.')
    package_root = candidates[0].parent
    try:
        spec = ModelSpec(str(package_root))
    except Exception as exc:
        raise ModelDownloadError('فایل translation_model.pb قابل‌خواندن نیست.') from exc

    expected = DIRECTIONS[expected_direction]
    actual = (spec.src_lang.lower(), spec.tgt_lang.lower())
    wanted = (expected['source'], expected['target'])
    if actual != wanted:
        raise ModelDownloadError(
            'جهت مدل اشتباه است؛ این بسته %s→%s است، اما %s انتخاب شده.'
            % (actual[0], actual[1], expected['label'])
        )

    for name in _REQUIRED_BIPE_MODELS:
        if name not in spec.files:
            raise ModelDownloadError('مدل ناقص است؛ فایل %s در بسته معرفی نشده.' % name)

    referenced = set(spec.files.values())
    referenced.update((spec.src_model, spec.src_vocab, spec.tgt_model, spec.tgt_vocab))
    resolved_root = package_root.resolve()
    resolved_files = {}
    for relative_name in referenced:
        try:
            parts = _safe_member_parts(relative_name)
            asset = package_root.joinpath(*parts)
            resolved = asset.resolve(strict=True)
        except (OSError, RuntimeError, ModelDownloadError) as exc:
            raise ModelDownloadError('مسیر یکی از فایل‌های مدل نامعتبر یا مفقود است.') from exc
        if os.path.commonpath((str(resolved_root), str(resolved))) != str(resolved_root) or not resolved.is_file():
            raise ModelDownloadError('یکی از فایل‌های مدل خارج از بسته است یا فایل معمولی نیست.')
        resolved_files[relative_name] = resolved

    for name in _REQUIRED_BIPE_MODELS:
        asset = resolved_files[spec.files[name]]
        try:
            with open(asset, 'rb') as model_file:
                header = model_file.read(8)
        except OSError as exc:
            raise ModelDownloadError('خواندن فایل مدل %s ممکن نیست.' % name) from exc
        if len(header) < 8 or header[4:8] != b'BIPE':
            raise ModelDownloadError('فایل %s فرمت BIPE معتبر ندارد.' % name)

    return package_root


def install_model_from_url(url: str, direction: str, models_root: str,
                           progress: Optional[Callable[[int, int], None]] = None) -> str:
    """Download a compatible ZIP over HTTPS and atomically install one language pair.

    The ZIP may have a single top-level wrapper folder. It must contain one
    ``translation_model.pb``, the seven BIPE files referenced by that manifest,
    and its source/target model and vocabulary resources. Returns the installed
    package directory.
    """
    if direction not in DIRECTIONS:
        raise ModelDownloadError('جهت ترجمه‌ی انتخاب‌شده پشتیبانی نمی‌شود.')
    url = _validate_https_url(url)
    root = Path(models_root).expanduser().absolute()
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not root.is_dir():
            raise OSError('not a directory')
    except OSError as exc:
        raise ModelDownloadError('پوشه‌ی ذخیره‌ی مدل قابل‌استفاده نیست: %s' % exc) from exc

    work = Path(tempfile.mkdtemp(prefix='.model-download-', dir=str(root)))
    target = root / DIRECTIONS[direction]['folder']
    staged = root / ('.%s-install-%s' % (target.name, uuid.uuid4().hex))
    backup = root / ('.%s-backup-%s' % (target.name, uuid.uuid4().hex))
    try:
        archive_path = work / 'model.zip'
        extract_root = work / 'contents'
        _download_archive(url, archive_path, progress)
        _extract_safely(archive_path, extract_root)
        package_root = _validated_package(extract_root, direction)
        shutil.copytree(package_root, staged)

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
    except ModelDownloadError:
        raise
    except (OSError, shutil.Error, ValueError, zipfile.BadZipFile) as exc:
        raise ModelDownloadError('نصب بسته‌ی مدل ناموفق بود: %s' % exc) from exc
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if staged.exists() or staged.is_symlink():
            if staged.is_dir() and not staged.is_symlink():
                shutil.rmtree(staged, ignore_errors=True)
            else:
                staged.unlink(missing_ok=True)
