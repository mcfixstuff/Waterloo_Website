# myapp/forms.py
from django import forms
from django.utils import timezone
from .models import User, FERPAForm

class UserSignatureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['signature_image']
        widgets = {
            'signature_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

class FERPAFormForm(forms.ModelForm):
    """Form for handling FERPA Authorization submissions"""
    
    student_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control d-inline-block w-50'})
    )
    
    university_division = forms.ChoiceField(
        choices=[
            ('', 'Click Here to Select One'),
            ('Main Campus', 'Main Campus'),
            ('Downtown', 'Downtown'),
            ('Clear Lake', 'Clear Lake'),
            ('Victoria', 'Victoria'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select d-inline-block w-50'})
    )
    
    peoplesoft_id = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    release_to = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    additional_individuals = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    password = forms.CharField(
        required=True,
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    form_date = forms.DateField(
        required=True,
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    other_office_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mt-1', 'id': 'other_office_text', 'style': 'display: none;'})
    )
    
    other_info_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mt-1', 'id': 'other_info_text', 'style': 'display: none;'})
    )
    
    other_purpose_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mt-1', 'id': 'other_purpose_text', 'style': 'display: none;'})
    )
    
    class Meta:
        model = FERPAForm
        fields = [
            'student_name', 'university_division', 'peoplesoft_id',
            'release_to', 'additional_individuals', 'password', 'form_date',
            'other_office_text', 'other_info_text', 'other_purpose_text'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if at least one office is selected
        offices = self.data.getlist('offices[]', [])
        if not offices:
            self.add_error(None, "Please select at least one office.")
        
        # Check if at least one info category is selected
        info_categories = self.data.getlist('info_categories[]', [])
        if not info_categories:
            self.add_error(None, "Please select at least one information category.")
        
        # Check if at least one purpose is selected
        purposes = self.data.getlist('purposes[]', [])
        if not purposes:
            self.add_error(None, "Please select at least one purpose.")
        
        # Check if "Other" office is selected but no text is provided
        if 'Other' in offices and not cleaned_data.get('other_office_text'):
            self.add_error('other_office_text', "Please specify the other office.")
        
        # Check if "Other" info category is selected but no text is provided
        if 'Other' in info_categories and not cleaned_data.get('other_info_text'):
            self.add_error('other_info_text', "Please specify the other information category.")
        
        # Check if "Other" purpose is selected but no text is provided
        if 'Other' in purposes and not cleaned_data.get('other_purpose_text'):
            self.add_error('other_purpose_text', "Please specify the other purpose.")
        
        return cleaned_data