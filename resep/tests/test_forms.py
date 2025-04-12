import pytest
from django.core.exceptions import ValidationError
from resep.forms import ResepForm
from resep.models import Kategori, CookingMethod, Bahan

@pytest.fixture
def kategori():
    return Kategori.objects.create(nama='Healthy Food')

@pytest.fixture
def metode_masak():
    return CookingMethod.objects.create(nama='Baked')

@pytest.fixture
def bahan_utama():
    return Bahan.objects.create(nama='Roti')

@pytest.fixture
def valid_form_data(kategori, metode_masak, bahan_utama):
    return {
        'judul': 'Bebek Kaleyo',
        'deskripsi': 'This is a delicious recipe for Bebek Kaleyo. This description is long enough to pass validation.',
        'alat': 'Bowl\nSpoon\nMixer',
        'bahan': 'Flour - 100g\nSugar - 50g\nEggs - 2',
        'langkah': '1. Mix the ingredients\n2. Bake in the oven for 30 minutes\n3. Serve hot',
        'kategori': kategori.id,
        'metode_masak': metode_masak.id,
        'bahan_utama': bahan_utama.id,
        'url_foto': 'https://example.com/recipe.jpg',
        'durasi': 45,
        'porsi': 4
    }

@pytest.mark.django_db
class TestResepForm:
    def test_valid_form(self, valid_form_data):
        form = ResepForm(data=valid_form_data)
        assert form.is_valid()

    def test_invalid_empty_form(self):
        form = ResepForm(data={})
        assert not form.is_valid()

        assert 'judul' in form.errors
        assert 'deskripsi' in form.errors
        assert 'alat' in form.errors
        assert 'bahan' in form.errors
        assert 'langkah' in form.errors
        assert 'kategori' in form.errors
        assert 'metode_masak' in form.errors
        assert 'bahan_utama' in form.errors
        assert 'url_foto' in form.errors
        assert 'durasi' in form.errors
        assert 'porsi' in form.errors

    def test_judul_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['judul'] = 'Test'
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'judul' in form.errors

        data['judul'] = 'A' * 101
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'judul' in form.errors

    def test_deskripsi_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['deskripsi'] = 'Too short'
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'deskripsi' in form.errors

    def test_bahan_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['bahan'] = 'Just one ingredient'
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'bahan' in form.errors

    def test_langkah_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['langkah'] = 'Mix and bake'
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'langkah' in form.errors

    def test_durasi_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['durasi'] = 0
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'durasi' in form.errors

        data['durasi'] = 1500
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'durasi' in form.errors

    def test_porsi_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['porsi'] = 0
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'porsi' in form.errors

        data['porsi'] = 101
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'porsi' in form.errors

    def test_url_foto_validation(self, valid_form_data):
        data = valid_form_data.copy()
        data['url_foto'] = 'not-a-valid-url'
        form = ResepForm(data=data)
        assert not form.is_valid()
        assert 'url_foto' in form.errors

    def test_sanitize_text(self, valid_form_data):
        data = valid_form_data.copy()
        data['judul'] = '<script>alert("XSS")</script>Safe Title'
        form = ResepForm(data=data)

        assert form.is_valid()

        assert '<script>' not in form.cleaned_data['judul']
        assert 'Safe Title' in form.cleaned_data['judul']

        data['deskripsi'] = '<p>This is <strong>formatted</strong> text</p>'
        form = ResepForm(data=data)

        assert form.is_valid()

        assert '<p>' in form.cleaned_data['deskripsi']
        assert '<strong>' in form.cleaned_data['deskripsi']