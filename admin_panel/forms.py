# myapp/forms.py
from django import forms
from django.utils import timezone
from .models import User, Application, FERPAForm, TexasResidencyAffidavit

class UserSignatureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['signature_image']
        widgets = {
            'signature_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

class ApplicationForm(forms.ModelForm):
    """Base form for creating an application"""
    
    class Meta:
        model = Application
        fields = ['type']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        
        # Generate a default application name based on type
        app_type = instance.get_type_display()
        instance.application_name = f"{app_type} - {timezone.now().strftime('%Y-%m-%d')}"
        
        if commit:
            instance.save()
        return instance


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
    
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.application:
            instance.application = self.application
            # Update application name with student name
            self.application.application_name = f"FERPA Authorization - {instance.student_name}"
            self.application.save()
        
        if commit:
            instance.save()
        return instance
    
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


class TexasResidencyAffidavitForm(forms.ModelForm):
    """Form for handling Texas Residency Affidavit submissions"""
    
    MONTH_CHOICES = [
        ('', 'Select Month'),
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]
    
    # Basic form fields
    county_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    appeared_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    full_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    age = forms.IntegerField(
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Checkbox attestations
    graduated_check = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    resided_check = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    permanent_resident_check = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # College information
    college_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(name of college)'})
    )
    
    # Date information
    day_of_month = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Day'})
    )
    
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    year = forms.IntegerField(
        required=True,
        min_value=2000,
        max_value=2100,
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'})
    )
    
    # Student information
    student_id = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Student ID number'})
    )
    
    student_dob = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Notary section - optional in the form since it will be completed by notary
    notary_day = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Day'})
    )
    
    notary_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notary_year = forms.IntegerField(
        required=False,
        min_value=2000,
        max_value=2100,
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'})
    )
    
    notary_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notary Name'})
    )
    
    class Meta:
        model = TexasResidencyAffidavit
        fields = [
            'county_name', 'appeared_name', 'full_name', 'age',
            'graduated_check', 'resided_check', 'permanent_resident_check',
            'college_name', 'day_of_month', 'month', 'year',
            'student_id', 'student_dob',
            'notary_day', 'notary_month', 'notary_year', 'notary_name',
        ]
        
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.application:
            instance.application = self.application
            # Update application name with student name
            self.application.application_name = f"Texas Residency Affidavit - {instance.full_name}"
            self.application.save()
        
        if commit:
            instance.save()
        return instance
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate day of month is appropriate for the selected month
        month = cleaned_data.get('month')
        day = cleaned_data.get('day_of_month')
        
        if month and day:
            days_31 = ['January', 'March', 'May', 'July', 'August', 'October', 'December']
            days_30 = ['April', 'June', 'September', 'November']
            
            if month == 'February' and day > 29:
                self.add_error('day_of_month', "February cannot have more than 29 days.")
            elif month in days_30 and day > 30:
                self.add_error('day_of_month', f"{month} cannot have more than 30 days.")
        
        # Make sure student is at least 16 years old
        dob = cleaned_data.get('student_dob')
        if dob:
            today = timezone.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                self.add_error('student_dob', "Student must be at least 16 years old.")
        
        return cleaned_data


class TexasResidencyForm(forms.Form):
    """Form for Texas Residency Questionnaire"""

    # Part A: Student Basic Information
    name = forms.CharField(
        label="Name",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        label="Date of Birth",
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    age = forms.IntegerField(
        label="Age",
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    term = forms.CharField(
        label="Term",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    student_id_number = forms.CharField(
        label="Student ID Number",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Part B: Previous Enrollment
    attended_texas_public_college = forms.ChoiceField(
        label="1. During the 12 months prior to the term for which you are applying, did you attend a public college or university in Texas in a fall or spring term?",
        choices=[('yes', 'Yes'), ('no', 'No')],
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    texas_public_institution = forms.CharField(
        label="2. If yes, what Texas public institution did you last attend? (Give full name, not just initials)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_enrolled_fall_year = forms.IntegerField(
        label="Fall, Year",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    last_enrolled_spring_year = forms.IntegerField(
        label="Spring, Year",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    tuition_status = forms.ChoiceField(
        label="4. During your last semester at a Texas public institution, did you pay resident (in-state) or nonresident (out-of-state) tuition?",
        choices=[
            ('resident', 'Resident (in-state)'),
            ('nonresident', 'Nonresident (out-of-state)'),
            ('unknown', 'Unknown')
        ],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    in_state_reason = forms.CharField(
        label="5. If you paid in-state tuition at your last institution, was it because you were a Texas resident or because you were a nonresident who received a...",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Part C: Intent to Establish Domicile (Example - only a few fields)
    purpose_for_being_in_texas = forms.ChoiceField(
        label="1. What is your purpose for being in Texas?",
        choices=[
            ('college', 'Go to College'),
            ('home', 'Establish/Maintain a Home'),
            ('work', 'Work Assignment'),
            ('other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # ... (Add all other fields from the questionnaire)

    # Part H: General Comments
    general_comments = forms.CharField(
        label="Is there any additional information that you believe your college should know in evaluating your eligibility to be classified as a resident? If so, please provide it below:",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    # File Attachments (This is a basic example - adjust as needed)
    # supporting_documents = forms.FileField(
    #     label="Upload Supporting Documents (Minimum 2):",
    #     required=False,
    #     widget=forms.FileInput(attrs={'multiple': True})
    # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can add logic here to conditionally show/hide fields
        # based on other field values if needed.

    def clean(self):
        cleaned_data = super().clean()
        # Add any form-level validation here (e.g., cross-field validation)
        return cleaned_data


class ApplicationReviewForm(forms.ModelForm):
    """Form for reviewing applications"""
    
    status = forms.ChoiceField(
        choices=Application.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    review_comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    class Meta:
        model = Application
        fields = ['status', 'review_comments']
    
    def __init__(self, *args, **kwargs):
        self.reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.reviewer:
            instance.reviewer = self.reviewer
            instance.reviewed_at = timezone.now()
        
        if commit:
            instance.save()
        
        return instance