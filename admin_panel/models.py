from django.db import models
from django.utils import timezone
import os

class User(models.Model):
    microsoft_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, default="basicuser")
    status = models.BooleanField(default=True)
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Check if this is an existing instance and if signature_image has changed
        if self.pk:
            try:
                old_instance = User.objects.get(pk=self.pk)
                if old_instance.signature_image and self.signature_image != old_instance.signature_image:
                    # Delete the old image file from filesystem
                    if os.path.isfile(old_instance.signature_image.path):
                        os.remove(old_instance.signature_image.path)
            except User.DoesNotExist:
                pass  # This is a new instance
        
        # Save the new instance
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} ({self.role}) - {'Active' if self.status else 'Disabled'}"


class Application(models.Model):
    # Link to User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    
    # Application type
    TYPE_CHOICES = [
        ('ferpa', 'FERPA Authorization'),
        ('texas_residency', 'Texas Residency Affidavit'),
        ('other', 'Other Application Type')
    ]
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    
    # Application name (can be generated based on type and date)
    application_name = models.CharField(max_length=255)
    
    # Status tracking
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('returned', 'Returned for Revision'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Reviewer details
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_applications'
    )
    review_comments = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)  # When submitted for review
    reviewed_at = models.DateTimeField(null=True, blank=True)  # When reviewed
    
    def __str__(self):
        return f"{self.application_name} - {self.get_status_display()}"
    
    def submit(self):
        """Mark application as submitted for approval"""
        self.status = 'pending'
        self.submitted_at = timezone.now()
        self.save()
    
    def approve(self, reviewer):
        """Mark application as approved"""
        self.status = 'approved'
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def return_for_revision(self, reviewer, comments):
        """Return application for revision with comments"""
        self.status = 'returned'
        self.reviewer = reviewer
        self.review_comments = comments
        self.reviewed_at = timezone.now()
        self.save()


class FERPAForm(models.Model):
    # Link to Application model instead of User
    application = models.OneToOneField(
        Application, 
        on_delete=models.CASCADE, 
        related_name='ferpa_form',
        null=True,  # Add this temporarily 
        blank=True  # Also add this
    )
    
    # Basic form data
    student_name = models.CharField(max_length=255)
    university_division = models.CharField(max_length=50)
    peoplesoft_id = models.CharField(max_length=20)
    offices = models.JSONField(default=list)  # Store selected offices as a list
    info_categories = models.JSONField(default=list)  # Store selected info categories
    release_to = models.CharField(max_length=255)
    additional_individuals = models.CharField(max_length=255, blank=True, null=True)
    purposes = models.JSONField(default=list)  # Store selected purposes
    password = models.CharField(max_length=10)  # Phone verification password
    form_date = models.DateField()
    
    # Additional fields for "Other" text inputs
    other_office_text = models.CharField(max_length=255, blank=True, null=True)
    other_info_text = models.CharField(max_length=255, blank=True, null=True)
    other_purpose_text = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"FERPA Form - {self.student_name}"
    
    def save(self, *args, **kwargs):
        # If this is a new instance, set the application name
        if not self.pk and hasattr(self, 'application'):
            if not self.application.application_name:
                self.application.application_name = f"FERPA Authorization - {self.student_name}"
                self.application.save()
        super().save(*args, **kwargs)


class TexasResidencyAffidavit(models.Model):
    # Link to Application model instead of User
    application = models.OneToOneField(
        Application, 
        on_delete=models.CASCADE, 
        related_name='texas_residency_affidavit',
        null=True,  # Add this temporarily
        blank=True  # Also add this 
    )
    
    # Basic form data
    county_name = models.CharField(max_length=100)
    appeared_name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    
    # Checkbox attestations
    graduated_check = models.BooleanField(default=False)
    resided_check = models.BooleanField(default=False)
    permanent_resident_check = models.BooleanField(default=False)
    
    # College information
    college_name = models.CharField(max_length=255)
    
    # Date information
    day_of_month = models.PositiveIntegerField()
    month = models.CharField(max_length=20)
    year = models.PositiveIntegerField()
    
    # Student information
    student_id = models.CharField(max_length=50)
    student_dob = models.DateField()
    
    # Notary section
    notary_day = models.PositiveIntegerField(null=True, blank=True)
    notary_month = models.CharField(max_length=20, null=True, blank=True)
    notary_year = models.PositiveIntegerField(null=True, blank=True)
    notary_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Texas Residency Affidavit - {self.full_name}"
    
    def save(self, *args, **kwargs):
        # If this is a new instance, set the application name
        if not self.pk and hasattr(self, 'application'):
            if not self.application.application_name:
                self.application.application_name = f"Texas Residency Affidavit - {self.full_name}"
                self.application.save()
        super().save(*args, **kwargs)


class ResidencyReclassification(models.Model):
    application = models.OneToOneField(
        Application, 
        on_delete=models.CASCADE, 
        related_name='residency_reclassification',
        null=True,
        blank=True
    )
    # Part A: Student Basic Information
    student_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField()  # Age
    term = models.CharField(max_length=50) # Academic term
    student_id_number = models.CharField(max_length=20)  # Student ID Number
    
    # Part B: Previous Enrollment
    attended_texas_public_college = models.BooleanField() # 1. Have you attended a Texas public college?
    texas_public_institution = models.CharField(max_length=255, blank=True, null=True)  # 2. If yes, institution
    # 3. If yes, dates of attendance
    last_enrolled_fall_year = models.CharField(max_length=20, blank=True, null=True)  # Fall, Year
    last_enrolled_spring_year = models.CharField(max_length=20, blank=True, null=True)  # Spring, Year

    last_tuition_status = models.CharField(
        max_length=50,
        choices=[
            ('resident', 'Resident (in-state)'),
            ('nonresident', 'Nonresident (out-of-state)'),
            ('unknown', 'Unknown')
        ],
        blank=True,
        null=True
    )  # 4. Tuition status

    in_state_tuition_basis = models.CharField(max_length=50, choices=[
        ('resident', 'Resident'),
        ('nonresident_waiver', 'Nonresident with a waiver'),
        ('unknown', 'Unknown')
    ], blank=True, null=True)  # 5. In-state tuition basis

    # Part C: Questions if you answered ”No” to Question 1 of Part B
    country_of_residence = models.CharField(max_length=100, blank=True, null=True)  # Of which country...
    texas_resident = models.CharField(max_length=20, choices=[
        ('yes', 'Yes'),
        ('no', 'No'),
        ('unknown', "I don't know")
    ], blank=True, null=True)  # Are you a resident of Texas?

    # Part D. Questions continuing from Part C. Acquisition of High School Diploma or GED
    graduated_texas_high_school = models.BooleanField()  # 1a. Did you graduate...
    high_school_name = models.CharField(max_length=255, blank=True, null=True)  # 1b. High school name
    high_school_city = models.CharField(max_length=255, blank=True, null=True)  # 1b. High school city
    lived_in_texas_36_months = models.BooleanField()  # 2. Lived in Texas 36 months leading up to high school graduation
    lived_in_texas_12_months = models.BooleanField()  # 3. Lived in Texas 12 months for applying semester
    us_citizen_or_permanent_resident = models.CharField(max_length=20, choices=[
        ('neither', 'Neither'),
        ('permanent_resident', 'Permanent Resident'),
        ('us_citizen', 'US Citizen')
    ])  # 4. US Citizen or Permanent Resident
    holds_visa = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 5. Do you hold a visa?
    visa_type = models.CharField(max_length=50, blank=True, null=True)  # Visa Type (if applicable)


    # Part E: Basis of Claim to Residency
    files_own_income_tax = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')])  # 1. File own income tax
    claimed_as_dependent = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')])  # 2. Claimed as dependent
    support_provider = models.CharField(max_length=50, choices=[
        ('self', 'Self'),
        ('parent_or_guardian', 'Parent or guardian'),
        ('other', 'Other')
    ], blank=True, null=True) # 3. Support provider

    # Part F: Questions for students who answered ”Yes” to Question 1 or ”Self” to Question 3 of Part E
    us_citizen = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 1. Are you a U.S. Citizen?
    currently_live_in_texas = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 5. Live in Texas?
    years_living_in_texas = models.PositiveIntegerField(blank=True, null=True)  # 6a. Years living in Texas
    months_living_in_texas = models.PositiveIntegerField(blank=True, null=True)  # 6a. Months living in Texas
    main_purpose_for_texas = models.CharField(max_length=50, choices=[
        ('college', 'Go to College'),
        ('home', 'Establish/Maintain a Home'),
        ('work', 'Work Assignment'),
        ('other', 'Other')
    ], blank=True, null=True)  # 6b. Purpose for being in Texas
    military_home_of_record = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No'), ('na', 'N/A')], blank=True, null=True)  # 7a. Military Home of Record
    military_legal_residence = models.CharField(max_length=100, blank=True, null=True)  # 7b. Military legal residence
    holds_title_to_property = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 8a. Holds title to property
    date_title_acquired = models.DateField(blank=True, null=True)  # 8a. Date title acquired
    owns_business_in_texas = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 8b. Owns business in Texas
    date_business_acquired = models.DateField(blank=True, null=True)  # 8b. Date business acquired
    gainfully_employed_in_texas = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 9a. Gainfully employed
    received_social_services = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 9b. Received social services
    married_to_texas_resident = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)  # 10a. Married to Texas resident
    spouse_basis_for_residency = models.CharField(max_length=50, choices=[
        ('8a', '8a. Hold Title'),
        ('8b', '8b. Ownership Interest'),
        ('9a', '9a. Gainful Employment'),
        ('9b', '9b. Social Services Support'),
        ('10a', '10a. Texas Resident'),
    ], blank=True, null=True)  # 10b. Spouse's basis for residency
    years_married_to_resident = models.PositiveIntegerField(blank=True, null=True)  # 10c. Years married
    months_married_to_resident = models.PositiveIntegerField(blank=True, null=True)  # 10c. Months married

    # PART G.  Questions for students who answered “Parent” or “Legal Guardian” to Question 3 of PART E. 
    parent_guardian_us_citizen = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 1. Parent/Guardian US Citizen?
    parent_guardian_permanent_resident = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 2. Parent/Guardian Permanent Resident?
    parent_guardian_pending_residency = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 3. Parent/Guardian Pending Residency?
    parent_guardian_visa_status = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 4. Parent/Guardian Visa Status?
    parent_guardian_visa_type = models.CharField(max_length=50, blank=True, null=True)  # 4. If yes, Visa type
    parent_guardian_lives_in_texas = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 5. Parent/Guardian lives in Texas?
    parent_guardian_years_in_texas = models.PositiveIntegerField(blank=True, null=True)  # 6a. Years in Texas
    parent_guardian_months_in_texas = models.PositiveIntegerField(blank=True, null=True)  # 6a. Months in Texas
    parent_guardian_purpose_for_texas = models.CharField(
        max_length=50,
        choices=[
            ('college', 'Go to College'),
            ('home', 'Establish/Maintain a Home'),
            ('work', 'Work Assignment'),
            ('other', 'Other')
        ],
        blank=True,
        null=True
    )  # 6b. Purpose for being in Texas
    parent_guardian_military_home_of_record = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No'), ('na', 'N/A')],
        blank=True,
        null=True
    )  # 7a. Military Home of Record
    parent_guardian_military_legal_residence = models.CharField(max_length=100, blank=True, null=True)  # 7b. Military Legal Residence
    parent_guardian_holds_title_to_property = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 8a. Holds title to property
    parent_guardian_date_title_acquired = models.DateField(blank=True, null=True)  # 8a. Date title acquired
    parent_guardian_owns_business = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 8b. Owns business
    parent_guardian_date_business_acquired = models.DateField(blank=True, null=True)  # 8b. Date business acquired
    parent_guardian_gainfully_employed = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 9a. Gainfully employed
    parent_guardian_received_social_services = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 9b. Received social services
    parent_guardian_married_to_resident = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True,
        null=True
    )  # 10a. Married to resident
    parent_guardian_spouse_basis_residency = models.CharField(
        max_length=50,
        choices=[
            ('8a', '8a. Hold Title'),
            ('8b', '8b. Ownership Interest'),
            ('9a', '9a. Gainful Employment'),
            ('9b', '9b. Social Services Support'),
            ('10a', '10a. Texas Resident'),
        ],
        blank=True,
        null=True
    )  # 10b. Spouse basis residency
    parent_guardian_years_married = models.PositiveIntegerField(blank=True, null=True)  # 10c. Years married
    parent_guardian_months_married = models.PositiveIntegerField(blank=True, null=True)  # 10c. Months married

    # Part H. General Comments
    general_comments = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Residency Reclassification - {self.student_name}"
    
    def save(self, *args, **kwargs):
        # If this is a new instance, set the application name
        if not self.pk and hasattr(self, 'application'):
            if not self.application.application_name:
                self.application.application_name = f"Residency Reclassification - {self.student_name}"
                self.application.save()
        super().save(*args, **kwargs)