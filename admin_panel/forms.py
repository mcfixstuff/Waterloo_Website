# myapp/forms.py
from django import forms
from .models import User

class UserSignatureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['signature_image']
        widgets = {
            'signature_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }