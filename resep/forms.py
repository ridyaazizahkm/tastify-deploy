from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.html import escape
import bleach
from .models import Resep, Kategori, Bahan, CookingMethod

ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'br', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {
    '*': ['style', 'class'],
    'a': ['href', 'title', 'target'],
}

class ResepForm(forms.ModelForm):
    class Meta:
        model = Resep
        fields = ['judul', 'deskripsi', 'alat', 'bahan', 'langkah', 'kategori', 'metode_masak', 'bahan_utama', 'url_foto', 'durasi', 'porsi']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter recipe title'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your recipe'}),
            'alat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List all equipment needed (one per line)'}),
            'bahan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List all ingredients (one per line)'}),
            'langkah': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write step-by-step instructions'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'metode_masak': forms.Select(attrs={'class': 'form-control'}),
            'bahan_utama': forms.Select(attrs={'class': 'form-control'}),
            'url_foto': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/your-image.jpg'}),
            'durasi': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Time in minutes'}),
            'porsi': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Number of servings'}),
        }
        labels = {
            'metode_masak': 'Metode Memasak',
            'bahan_utama': 'Bahan Utama',
            'durasi': 'Waktu Memasak (menit)',
            'porsi': 'Jumlah Porsi',
        }

    def __init__(self, *args, **kwargs):
        super(ResepForm, self).__init__(*args, **kwargs)

        if 'metode_masak' in self.fields:
            self.fields['metode_masak'].queryset = CookingMethod.objects.all()
            self.fields['metode_masak'].label_from_instance = lambda obj: obj.nama if hasattr(obj, 'nama') else str(obj)
            self.fields['metode_masak'].error_messages = {'required': 'Please select a cooking method'}

        if 'bahan_utama' in self.fields:
            self.fields['bahan_utama'].queryset = Bahan.objects.all()
            self.fields['bahan_utama'].label_from_instance = lambda obj: obj.nama if hasattr(obj, 'nama') else str(obj)
            self.fields['bahan_utama'].error_messages = {'required': 'Please select a main ingredient'}

        if 'kategori' in self.fields:
            self.fields['kategori'].queryset = Kategori.objects.all()
            self.fields['kategori'].label_from_instance = lambda obj: obj.nama if hasattr(obj, 'nama') else str(obj)
            self.fields['kategori'].error_messages = {'required': 'Please select a category'}

        self.fields['judul'].error_messages = {'required': 'Recipe title is required'}
        self.fields['deskripsi'].error_messages = {'required': 'Recipe description is required'}
        self.fields['alat'].error_messages = {'required': 'Tools/equipment information is required'}
        self.fields['bahan'].error_messages = {'required': 'Ingredients information is required'}
        self.fields['langkah'].error_messages = {'required': 'Cooking instructions are required'}
        self.fields['url_foto'].error_messages = {'required': 'Photo URL is required', 'invalid': 'Please enter a valid URL'}
        self.fields['durasi'].error_messages = {'required': 'Cooking time is required', 'invalid': 'Please enter a valid number'}
        self.fields['porsi'].error_messages = {'required': 'Number of servings is required', 'invalid': 'Please enter a valid number'}

    def sanitize_text(self, text):
        """Sanitize text input to prevent XSS attacks"""
        if text:
            cleaned_text = bleach.clean(
                text,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            return cleaned_text
        return text

    def clean_judul(self):
        judul = self.cleaned_data.get('judul')
        if judul:
            judul = self.sanitize_text(judul)
            if len(judul) < 5:
                raise ValidationError("Title must be at least 5 characters long")
            if len(judul) > 100:
                raise ValidationError("Title cannot exceed 100 characters")
        return judul

    def clean_deskripsi(self):
        deskripsi = self.cleaned_data.get('deskripsi')
        if deskripsi:
            deskripsi = self.sanitize_text(deskripsi)
            if len(deskripsi) < 20:
                raise ValidationError("Description must be at least 20 characters long")
        return deskripsi

    def clean_bahan(self):
        bahan = self.cleaned_data.get('bahan')
        if bahan:
            bahan = self.sanitize_text(bahan)
            lines = bahan.split('\n')
            if len(lines) < 2:
                raise ValidationError("Please list at least 2 ingredients")
        return bahan

    def clean_alat(self):
        alat = self.cleaned_data.get('alat')
        if alat:
            alat = self.sanitize_text(alat)
        return alat

    def clean_langkah(self):
        langkah = self.cleaned_data.get('langkah')
        if langkah:
            langkah = self.sanitize_text(langkah)
            if len(langkah) < 50:
                raise ValidationError("Instructions should be more detailed (at least 50 characters)")
        return langkah

    def clean_durasi(self):
        durasi = self.cleaned_data.get('durasi')
        if durasi is not None:
            if durasi < 1:
                raise ValidationError("Cooking time must be at least 1 minute")
            if durasi > 1440:
                raise ValidationError("Cooking time cannot exceed 24 hours (1440 minutes)")
        return durasi

    def clean_porsi(self):
        porsi = self.cleaned_data.get('porsi')
        if porsi is not None:
            if porsi < 1:
                raise ValidationError("Servings must be at least 1")
            if porsi > 100:
                raise ValidationError("Servings cannot exceed 100")
        return porsi

    def clean_url_foto(self):
        url = self.cleaned_data.get('url_foto')
        if url:
            url = self.sanitize_text(url)
            try:
                validator = URLValidator()
                validator(url)
            except ValidationError:
                raise ValidationError("Please enter a valid URL")
        return url
