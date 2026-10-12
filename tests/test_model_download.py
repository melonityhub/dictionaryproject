import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastdic_desktop.model_download import ModelDownloadError, install_model_from_url
from fastdic_desktop.model_spec import ModelSpec


BIPE_NAMES = (
    'encoder_embed_ids_0',
    'encoder_swizzled_birnn_0',
    'encoder_swizzled_birnn_1',
    'encoder_swizzled_birnn_2',
    'decoder_init_0',
    'decoder_step_embed_ids_0',
    'decoder_step_0',
)


def _varint(value):
    out = bytearray()
    while value > 0x7f:
        out.append((value & 0x7f) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def _bytes_field(number, value):
    return _varint((number << 3) | 2) + _varint(len(value)) + value


def _model_archive(source='fa', target='en', include_models=True, traversal=False):
    files = {}
    for name in BIPE_NAMES:
        files[name] = 'resources/%s.bipe' % name
    source_model, source_vocab = 'resources/source.model', 'resources/source.vocab'
    target_model, target_vocab = 'resources/target.model', 'resources/target.vocab'

    source_config = _bytes_field(1, source_model.encode()) + _bytes_field(2, source_vocab.encode())
    target_config = _bytes_field(1, target_model.encode()) + _bytes_field(2, target_vocab.encode())
    config = _bytes_field(1, source_config) + _bytes_field(6, target_config)
    manifest = _bytes_field(1, source.encode()) + _bytes_field(2, target.encode()) + _bytes_field(4, config)
    for name, path in files.items():
        mapping = _bytes_field(1, name.encode()) + _bytes_field(2, path.encode())
        manifest += _bytes_field(5, mapping)

    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        prefix = 'wrapped/translate_%s%s/' % (source, target)
        archive.writestr(prefix + 'translation_model.pb', manifest)
        for path in (source_model, source_vocab, target_model, target_vocab):
            archive.writestr(prefix + path, b'model-resource')
        if include_models:
            for path in files.values():
                archive.writestr(prefix + path, b'\x00\x00\x00\x00BIPE' + b'fake-model-data')
        if traversal:
            archive.writestr('../outside.txt', b'not allowed')
    return output.getvalue()


class FakeResponse(io.BytesIO):
    def __init__(self, payload, url):
        super().__init__(payload)
        self.headers = {'Content-Length': str(len(payload))}
        self._url = url

    def geturl(self):
        return self._url


class ModelDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.models_root = Path(self.temp.name) / 'models'
        self.url = 'https://models.example.test/fa-en.zip'

    def tearDown(self):
        self.temp.cleanup()

    def _install(self, payload, direction='fa>en', url=None, progress=None):
        response = FakeResponse(payload, url or self.url)
        with patch('fastdic_desktop.model_download.urllib.request.urlopen', return_value=response):
            return install_model_from_url(url or self.url, direction, str(self.models_root), progress)

    def test_downloads_valid_bundle_and_reports_progress(self):
        payload = _model_archive()
        updates = []
        installed = Path(self._install(payload, progress=lambda current, total: updates.append((current, total))))
        self.assertEqual(installed.name, 'translate_faen')
        self.assertTrue((installed / 'translation_model.pb').is_file())
        self.assertEqual((installed / 'resources' / 'encoder_embed_ids_0.bipe').read_bytes()[4:8], b'BIPE')
        spec = ModelSpec(str(installed))
        self.assertEqual((spec.src_lang, spec.tgt_lang), ('fa', 'en'))
        self.assertTrue(updates)
        self.assertEqual(updates[-1], (len(payload), len(payload)))

    def test_downloads_both_required_language_directions(self):
        fa_en = Path(self._install(_model_archive('fa', 'en'), direction='fa>en'))
        en_fa = Path(self._install(_model_archive('en', 'fa'), direction='en>fa',
                                   url='https://models.example.test/en-fa.zip'))
        self.assertEqual(fa_en.name, 'translate_faen')
        self.assertEqual(en_fa.name, 'translate_enfa')
        self.assertEqual((ModelSpec(str(fa_en)).src_lang, ModelSpec(str(fa_en)).tgt_lang), ('fa', 'en'))
        self.assertEqual((ModelSpec(str(en_fa)).src_lang, ModelSpec(str(en_fa)).tgt_lang), ('en', 'fa'))

    def test_rejects_wrong_direction_without_replacing_installed_model(self):
        target = self.models_root / 'translate_faen'
        target.mkdir(parents=True)
        sentinel = target / 'keep.txt'
        sentinel.write_text('existing model remains intact', encoding='utf-8')
        with self.assertRaises(ModelDownloadError):
            self._install(_model_archive('en', 'fa'), direction='fa>en')
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'existing model remains intact')

    def test_rejects_zip_slip_paths(self):
        with self.assertRaisesRegex(ModelDownloadError, 'مسیر'):
            self._install(_model_archive(traversal=True))
        self.assertFalse((Path(self.temp.name) / 'outside.txt').exists())

    def test_rejects_incomplete_model_package(self):
        with self.assertRaises(ModelDownloadError):
            self._install(_model_archive(include_models=False))
        self.assertFalse((self.models_root / 'translate_faen').exists())

    def test_requires_https_before_network_request(self):
        with patch('fastdic_desktop.model_download.urllib.request.urlopen') as open_url:
            with self.assertRaises(ModelDownloadError):
                install_model_from_url('http://models.example.test/model.zip', 'fa>en', str(self.models_root))
            open_url.assert_not_called()

    def test_rejects_invalid_direction(self):
        with self.assertRaises(ModelDownloadError):
            install_model_from_url(self.url, 'fa>de', str(self.models_root))


if __name__ == '__main__':
    unittest.main()
