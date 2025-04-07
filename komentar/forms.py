from django import forms
from .models import Komentar

class KomentarForm(forms.ModelForm):
    class Meta:
        model = Komentar
        fields = ['isi_komentar']
        widgets = {
            'isi': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comments...'})
        }