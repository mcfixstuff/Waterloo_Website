from django import forms

class ReleaseForm(forms.Form):
    student_name = forms.CharField(label="Student Name", max_length=100, widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    student_email = forms.EmailField(label="Student Email", widget=forms.EmailInput(attrs={'readonly': 'readonly'}))
    student_id = forms.CharField(label="PeopleSoft I.D. Number", max_length=20, required=False)
    
    office_choices = [
        ('registrar', "Office of the University Registrar"),
        ('financial_aid', "Scholarships and Financial Aid"),
        ('student_finance', "Student Financial Services"),
        ('undergrad_scholars', "Undergraduate Scholars @ UH"),
        ('advancement', "University Advancement"),
        ('dean', "Dean of Students Office"),
        ('other', "Other"),
    ]
    offices = forms.MultipleChoiceField(label="Select Offices", choices=office_choices, widget=forms.CheckboxSelectMultiple)

    info_choices = [
        ('advising', "Academic Advising Profile/Information"),
        ('academic_records', "Academic Records"),
        ('all_records', "All University Records"),
        ('billing', "Billing/Financial Aid"),
        ('disciplinary', "Disciplinary"),
        ('grades', "Grades/Transcripts"),
        ('housing', "Housing"),
        ('photos', "Photos"),
        ('scholarships', "Scholarship and/or Honors"),
        ('other', "Other"),
    ]
    information = forms.MultipleChoiceField(label="Information to Disclose", choices=info_choices, widget=forms.CheckboxSelectMultiple)

    recipient = forms.CharField(label="Recipient Name(s)", max_length=255, required=True)
    
    purpose_choices = [
        ('family', "Family"),
        ('institution', "Educational Institution"),
        ('honor', "Honor or Award"),
        ('employer', "Employer/Prospective Employer"),
        ('media', "Public or Media of Scholarship"),
        ('other', "Other"),
    ]
    purpose = forms.MultipleChoiceField(label="Purpose of Release", choices=purpose_choices, widget=forms.CheckboxSelectMultiple)

    password = forms.CharField(label="Phone Access Password", max_length=10, required=True)

    student_signature = forms.CharField(label="Student Signature", max_length=100, required=True)

    date = forms.DateField(label="Date", widget=forms.DateInput(attrs={'type': 'date'}))

