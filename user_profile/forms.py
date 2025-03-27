from django import forms
from authentication.models import UserProfile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
                'placeholder': 'Write your thoughts here...',
                'rows': 4,
            }),
        }
        