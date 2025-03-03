from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from admin_panel.models import User
import msal
from django.db.models import Q
import requests
from .forms import UserSignatureForm,FERPAForm,TexasResidencyAffidavit,Application
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from django.contrib import messages



# Authentication Views
def show_login_page(request):
    """Render the login page."""
    return render(request, "admin_panel/login.html")
        


@csrf_exempt
def trigger_microsoft_login(request):
    """Initiate Microsoft OAuth login flow."""
    auth_url = (
        f"{settings.MICROSOFT_AUTH['AUTHORITY']}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_AUTH['CLIENT_ID']}"
        f"&response_type=code"
        f"&redirect_uri={settings.MICROSOFT_AUTH['REDIRECT_URI']}"
        f"&response_mode=query"
        f"&scope=User.Read"
        f"&prompt=select_account"
    )
    return redirect(auth_url)

def login_view(request):
    """Handle Microsoft OAuth callback and user authentication."""
    if "code" in request.GET:
        auth_code = request.GET["code"]

        msal_app = msal.ConfidentialClientApplication(
            settings.MICROSOFT_AUTH["CLIENT_ID"],
            client_credential=settings.MICROSOFT_AUTH["CLIENT_SECRET"],
            authority=settings.MICROSOFT_AUTH["AUTHORITY"],
        )

        token_response = msal_app.acquire_token_by_authorization_code(
            auth_code,
            scopes=["User.Read"],
            redirect_uri=settings.MICROSOFT_AUTH["REDIRECT_URI"],
        )

        if "access_token" in token_response:
            access_token = token_response["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()

            user, created = User.objects.get_or_create(
                microsoft_id=user_info["id"],
                defaults={
                    "username": user_info.get("displayName", "Unknown"),
                    "email": user_info.get("mail", ""),
                    "role": "basicuser" if User.objects.exists() else "superuser",
                }
            )

            if not user.status:
                return HttpResponse("Your account has been disabled. Please contact the administrator.", status=403)

            request.session["access_token"] = access_token
            request.session["user_email"] = user_info.get("mail")

            return redirect("admin_dashboard")

    return redirect("login")

def logout_view(request):
    """Handle user logout and session cleanup."""
    request.session.flush()
    logout_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={settings.MICROSOFT_AUTH['REDIRECT_URI']}"
    )
    return redirect('login')

# Dashboard Views
def admin_dashboard(request):
    """Render the admin dashboard with user management interface."""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")

    headers = {"Authorization": f"Bearer {access_token}"}
    user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()
    current_user = User.objects.filter(email=user_info.get("mail")).first()
    
    if current_user and not current_user.status:
        return HttpResponse("Your account has been disabled. Please contact the administrator.", status=403)
    
    # Role priority for sorting
    role_priority = {"superuser": 1, "manager": 2, "basicuser": 3}

    # Get and sort users by status and role
    enabled_users = User.objects.filter(status=True)
    enabled_users = sorted(enabled_users, key=lambda u: role_priority.get(u.role, 99))
    disabled_users = User.objects.filter(status=False).order_by("id")

    return render(request, "admin_panel/dashboard.html", {
        "user_name": user_info.get("displayName", "User"),
        "user_role": current_user.role if current_user else "basicuser",
        "enabled_users": enabled_users,
        "disabled_users": disabled_users,
        "active_page": "dashboard"
    })

# User Management Views
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status (superuser only)."""
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    current_user = User.objects.filter(email=email).first()
    if not current_user or current_user.role != "superuser":
        return HttpResponseForbidden("You do not have permission to perform this action.")

    user = get_object_or_404(User, id=user_id)
    user.status = not user.status
    user.save()

    return redirect("admin_dashboard")

def change_user_role(request, user_id):
    """Change user role (superuser only)."""
    if "access_token" not in request.session:
        return redirect("login")

    current_user = User.objects.filter(email=request.session.get("user_email")).first()
    if not current_user or current_user.role != "superuser":
        return HttpResponseForbidden("You do not have permission to perform this action.")

    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get("new_role")

    if user.role == "superuser" and new_role != "superuser":
        return HttpResponseForbidden("You cannot demote a superuser.")

    if new_role in ["superuser", "manager", "basicuser"]:
        user.role = new_role
        user.save()

    return redirect("admin_dashboard")

#PROJECT 0.2



# Update your existing upload_signature view or add it if it doesn't exist
def upload_signature(request):
    """Handle user signature upload."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        form = UserSignatureForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('Applications')  # Redirect to applications page after success
    else:
        form = UserSignatureForm(instance=user)
    
    # You don't need a separate template as you're using a modal in your existing template
    # Pass the form to the applications template
    context = {
        'active_page': 'Applications',
        'user': user,
        'signature_form': form
    }
    return render(request, "admin_panel/Applications.html", context)


# 3. Update the Applications view to include the signature form
def Applications(request):
    """Render the Applications page with signature form and applications."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    signature_form = UserSignatureForm(instance=user)
    
    # Fetch all applications for this user
    applications = Application.objects.filter(user=user).order_by('-updated_at')
    
    context = {
        'active_page': 'Applications',
        'user': user,
        'signature_form': signature_form,
        'applications': applications
    }
    return render(request, "admin_panel/Applications.html", context)

def ApplicationApprovals(request):
    """Render the ApplicationApprovals view with permission check."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    current_user = User.objects.filter(email=email).first()
    if not current_user or (current_user.role not in ["superuser", "manager"]):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # 1) Stats - now using Application model instead of FERPAForm
    pending_count = Application.objects.filter(status='pending').count()
    approved_count = Application.objects.filter(status='approved').count()
    returned_count = Application.objects.filter(status='returned').count()

    # For "Today", let's get applications submitted today
    today = timezone.now().date()
    today_count = Application.objects.filter(
        submitted_at__date=today
    ).count()

    # 2) Pending applications for the table
    pending_forms = Application.objects.filter(status='pending').order_by('-created_at')

    # 3) Recent applications for the "Recent Activity"
    recent_forms = Application.objects.filter(
        status__in=["approved", "returned"]
    ).order_by('-reviewed_at', '-updated_at')[:5]

    context = {
        'active_page': 'ApplicationApprovals',
        'user': current_user,
        'pending_forms': pending_forms,
        'recent_forms': recent_forms,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'returned_count': returned_count,
        'today_count': today_count,
    }
    return render(request, "admin_panel/ApplicationApprovalsDashboard.html", context)





def select_form_type(request):
    """Handle form type selection from the modal without creating a draft record immediately."""
    if "access_token" not in request.session:
        return redirect("login")
        
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
        
    user = get_object_or_404(User, email=email)
        
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Store the form type selection in session instead of creating an application
        if form_type in ['ferpa_authorization', 'texas_affidavit']:
            # Map the form type to application_type
            application_type = {
                'ferpa_authorization': 'ferpa',
                'texas_affidavit': 'texas_residency'
            }.get(form_type)
            
            # Store the selected type in session for later use when form is actually saved
            request.session['selected_form_type'] = application_type
                
            # Render the appropriate form template without creating an application yet
            if form_type == 'ferpa_authorization':
                context = {
                    'user': user,
                    'active_page': 'Applications'
                }
                return render(request, 'FERPA_Authorization_form.html', context)
            elif form_type == 'texas_affidavit':
                context = {
                    'user': user,
                    'active_page': 'Applications'
                }
                return render(request, 'Texas_Residency_Affidavit_Form.html', context)
            elif form_type == 'leave_absence':
                return HttpResponse('leave_absence_form')
        else:
            messages.error(request, "Invalid form type selected")
        
    return redirect('Applications')
    
    
    


def save_ferpa_form(request):
    """Save FERPA form data, creating an Application only when explicitly saved."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        # Check if we're saving a draft or submitting
        is_draft = "save_as_draft" in request.POST
        is_submit = "submit_form" in request.POST
        
        # Only proceed with saving if explicitly requested
        if is_draft or is_submit:
            # Get application ID if we already have one
            application_id = request.session.get('current_application_id')
            
            # If no existing application but we're saving or submitting
            if not application_id:
                # Create a new application
                application_type = request.session.get('selected_form_type')
                if not application_type:
                    messages.error(request, "Form type not found. Please try again.")
                    return redirect('Applications')
                
                # Create the application record
                application = Application.objects.create(
                    user=user,
                    type=application_type,
                    application_name=f"New {application_type.replace('_', ' ').title()} Application",
                    status='draft' if is_draft else 'pending',
                    submitted_at=None if is_draft else timezone.now()
                )
            else:
                # Get existing application if we have an ID
                try:
                    application = Application.objects.get(id=application_id, user=user)
                    
                    # Update status based on button clicked
                    if is_draft:
                        application.status = "draft"
                        application.submitted_at = None
                    elif is_submit:
                        application.status = "pending"
                        application.submitted_at = timezone.now()
                    
                    application.save()
                except Application.DoesNotExist:
                    messages.error(request, "Application not found.")
                    return redirect('Applications')
            
            # Create or update the FERPA form
            ferpa_form, created = FERPAForm.objects.get_or_create(
                application=application,
                defaults={
                    'student_name': request.POST.get('student_name', ''),
                    'university_division': request.POST.get('university_division', ''),
                    'peoplesoft_id': request.POST.get('peoplesoft_id', ''),
                    'offices': request.POST.getlist('offices[]', []),
                    'info_categories': request.POST.getlist('info_categories[]', []),
                    'release_to': request.POST.get('release_to', ''),
                    'additional_individuals': request.POST.get('additional_individuals', ''),
                    'purposes': request.POST.getlist('purposes[]', []),
                    'password': request.POST.get('password', ''),
                    'form_date': request.POST.get('form_date', timezone.now().date()),
                    'other_office_text': request.POST.get('other_office_text', ''),
                    'other_info_text': request.POST.get('other_info_text', ''),
                    'other_purpose_text': request.POST.get('other_purpose_text', ''),
                }
            )
            
            # If form already existed, update its fields
            if not created:
                ferpa_form.student_name = request.POST.get('student_name', '')
                ferpa_form.university_division = request.POST.get('university_division', '')
                ferpa_form.peoplesoft_id = request.POST.get('peoplesoft_id', '')
                ferpa_form.offices = request.POST.getlist('offices[]', [])
                ferpa_form.info_categories = request.POST.getlist('info_categories[]', [])
                ferpa_form.release_to = request.POST.get('release_to', '')
                ferpa_form.additional_individuals = request.POST.get('additional_individuals', '')
                ferpa_form.purposes = request.POST.getlist('purposes[]', [])
                ferpa_form.password = request.POST.get('password', '')
                ferpa_form.form_date = request.POST.get('form_date', timezone.now().date())
                ferpa_form.other_office_text = request.POST.get('other_office_text', '')
                ferpa_form.other_info_text = request.POST.get('other_info_text', '')
                ferpa_form.other_purpose_text = request.POST.get('other_purpose_text', '')
                ferpa_form.save()
            
            # Update application name based on student name
            application.application_name = f"FERPA Authorization - {ferpa_form.student_name}"
            application.save()
            
            # If submitting, use the submit method to set timestamps properly
            if is_submit:
                application.submit()

            # Clean up session
            if 'current_application_id' in request.session:
                del request.session['current_application_id']
            if 'selected_form_type' in request.session:
                del request.session['selected_form_type']
            
            messages.success(request, "FERPA Authorization form saved successfully.")
        else:
            # User is canceling - just redirect back without saving
            if 'selected_form_type' in request.session:
                del request.session['selected_form_type']
        
        # Redirect to Applications after saving or submitting
        return redirect('Applications')
    
    # If not POST, just redirect to Applications
    return redirect('Applications')
    """Save FERPA form data, creating an Application only when explicitly saved."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        # Check if we're saving a draft or submitting
        is_draft = "save_as_draft" in request.POST
        
        # Get application ID if we already have one, otherwise use None
        application_id = request.session.get('current_application_id')
        application = None
        
        # If no existing application but we're saving (not just previewing)
        if not application_id and (is_draft or "submit_form" in request.POST):
            # Create a new application only if explicitly saving
            application_type = request.session.get('selected_form_type')
            if not application_type:
                messages.error(request, "Form type not found. Please try again.")
                return redirect('Applications')
            
            # Now create the application record since user has chosen to save
            application = Application.objects.create(
                user=user,
                type=application_type,
                application_name=f"New {application_type.replace('_', ' ').title()} Application",
                status='draft' if is_draft else 'pending',
                submitted_at=None if is_draft else timezone.now()
            )
            request.session['current_application_id'] = application.id
        elif application_id:
            # Get existing application if we have an ID
            try:
                application = Application.objects.get(id=application_id, user=user)
                
                # Update status based on button clicked
                if is_draft:
                    application.status = "draft"
                    application.submitted_at = None
                elif "submit_form" in request.POST:
                    application.status = "pending"
                    application.submitted_at = timezone.now()
                
                # Save the application if we're explicitly saving
                if is_draft or "submit_form" in request.POST:
                    application.save()
            except Application.DoesNotExist:
                messages.error(request, "Application not found.")
                return redirect('Applications')
        
        # Only save the FERPA form data if we're explicitly saving
        if application and (is_draft or "submit_form" in request.POST):
            ferpa_form, created = FERPAForm.objects.get_or_create(
                application=application,
                defaults={
                    'student_name': request.POST.get('student_name', ''),
                    'university_division': request.POST.get('university_division', ''),
                    'peoplesoft_id': request.POST.get('peoplesoft_id', ''),
                    'offices': request.POST.getlist('offices[]', []),
                    'info_categories': request.POST.getlist('info_categories[]', []),
                    'release_to': request.POST.get('release_to', ''),
                    'additional_individuals': request.POST.get('additional_individuals', ''),
                    'purposes': request.POST.getlist('purposes[]', []),
                    'password': request.POST.get('password', ''),
                    'form_date': request.POST.get('form_date', timezone.now().date()),
                    'other_office_text': request.POST.get('other_office_text', ''),
                    'other_info_text': request.POST.get('other_info_text', ''),
                    'other_purpose_text': request.POST.get('other_purpose_text', ''),
                }
            )
            
            # If form already existed, update its fields
            if not created:
                ferpa_form.student_name = request.POST.get('student_name', '')
                ferpa_form.university_division = request.POST.get('university_division', '')
                ferpa_form.peoplesoft_id = request.POST.get('peoplesoft_id', '')
                ferpa_form.offices = request.POST.getlist('offices[]', [])
                ferpa_form.info_categories = request.POST.getlist('info_categories[]', [])
                ferpa_form.release_to = request.POST.get('release_to', '')
                ferpa_form.additional_individuals = request.POST.get('additional_individuals', '')
                ferpa_form.purposes = request.POST.getlist('purposes[]', [])
                ferpa_form.password = request.POST.get('password', '')
                ferpa_form.form_date = request.POST.get('form_date', timezone.now().date())
                ferpa_form.other_office_text = request.POST.get('other_office_text', '')
                ferpa_form.other_info_text = request.POST.get('other_info_text', '')
                ferpa_form.other_purpose_text = request.POST.get('other_purpose_text', '')
                ferpa_form.save()
            
            # Update application name based on student name
            if application:
                application.application_name = f"FERPA Authorization - {ferpa_form.student_name}"
                application.save()
                
                # If submitting, use the submit method to set timestamps properly
                if not is_draft and "submit_form" in request.POST:
                    application.submit()

            # Clean up session if we've saved
            if 'current_application_id' in request.session:
                del request.session['current_application_id']
            if 'selected_form_type' in request.session:
                del request.session['selected_form_type']
        
        # Redirect based on what button was clicked
        if "preview" in request.POST and application:
            # Just show preview without saving anything to the database
            return redirect('preview_temp_application')  # You'll need to create this view
        else:
            # Redirect to Applications after saving or submitting
            return redirect('Applications')
    
    # If not POST, just redirect to Applications
    return redirect('Applications')



def save_texas_affidavit_form(request):
    """Save Texas Residency Affidavit form data, creating an Application only when explicitly saved."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        # Check if we're saving a draft or submitting
        is_draft = "save_as_draft" in request.POST
        is_submit = "submit_form" in request.POST
        
        # Only proceed with saving if explicitly requested
        if is_draft or is_submit:
            # Get application ID if we already have one
            application_id = request.session.get('current_application_id')
            
            # If no existing application but we're saving or submitting
            if not application_id:
                # Create a new application
                application_type = request.session.get('selected_form_type')
                if not application_type:
                    messages.error(request, "Form type not found. Please try again.")
                    return redirect('Applications')
                
                # Create the application record
                application = Application.objects.create(
                    user=user,
                    type=application_type,
                    application_name=f"New {application_type.replace('_', ' ').title()} Application",
                    status='draft' if is_draft else 'pending',
                    submitted_at=None if is_draft else timezone.now()
                )
            else:
                # Get existing application if we have an ID
                try:
                    application = Application.objects.get(id=application_id, user=user)
                    
                    # Update status based on button clicked
                    if is_draft:
                        application.status = "draft"
                        application.submitted_at = None
                    elif is_submit:
                        application.status = "pending"
                        application.submitted_at = timezone.now()
                    
                    application.save()
                except Application.DoesNotExist:
                    messages.error(request, "Application not found.")
                    return redirect('Applications')
            
            # Process form data
            try:
                student_dob = timezone.datetime.strptime(request.POST.get('student_dob', ''), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                student_dob = timezone.now().date()
            
            # Create or update the Texas Residency Affidavit
            texas_affidavit, created = TexasResidencyAffidavit.objects.get_or_create(
                application=application,
                defaults={
                    'county_name': request.POST.get('county_name', ''),
                    'appeared_name': request.POST.get('appeared_name', ''),
                    'full_name': request.POST.get('full_name', ''),
                    'age': int(request.POST.get('age', 0)),
                    'graduated_check': 'graduated_check' in request.POST,
                    'resided_check': 'resided_check' in request.POST,
                    'permanent_resident_check': 'permanent_resident_check' in request.POST,
                    'college_name': request.POST.get('college_name', ''),
                    'day_of_month': int(request.POST.get('day_of_month', 1)),
                    'month': request.POST.get('month', ''),
                    'year': int(request.POST.get('year', 2025)),
                    'student_id': request.POST.get('student_id', ''),
                    'student_dob': student_dob,
                    'notary_day': request.POST.get('notary_day') or None,
                    'notary_month': request.POST.get('notary_month', ''),
                    'notary_year': request.POST.get('notary_year') or None,
                    'notary_name': request.POST.get('notary_name', ''),
                }
            )
            
            # If form already existed, update its fields
            if not created:
                texas_affidavit.county_name = request.POST.get('county_name', '')
                texas_affidavit.appeared_name = request.POST.get('appeared_name', '')
                texas_affidavit.full_name = request.POST.get('full_name', '')
                texas_affidavit.age = int(request.POST.get('age', 0))
                texas_affidavit.graduated_check = 'graduated_check' in request.POST
                texas_affidavit.resided_check = 'resided_check' in request.POST
                texas_affidavit.permanent_resident_check = 'permanent_resident_check' in request.POST
                texas_affidavit.college_name = request.POST.get('college_name', '')
                texas_affidavit.day_of_month = int(request.POST.get('day_of_month', 1))
                texas_affidavit.month = request.POST.get('month', '')
                texas_affidavit.year = int(request.POST.get('year', 2025))
                texas_affidavit.student_id = request.POST.get('student_id', '')
                texas_affidavit.student_dob = student_dob
                texas_affidavit.notary_day = request.POST.get('notary_day') or None
                texas_affidavit.notary_month = request.POST.get('notary_month', '')
                texas_affidavit.notary_year = request.POST.get('notary_year') or None
                texas_affidavit.notary_name = request.POST.get('notary_name', '')
                texas_affidavit.save()
            
            # Update application name based on full name
            application.application_name = f"Texas Residency Affidavit - {texas_affidavit.full_name}"
            application.save()
            
            # If submitting, use the submit method to set timestamps properly
            if is_submit:
                application.submit()

            # Clean up session
            if 'current_application_id' in request.session:
                del request.session['current_application_id']
            if 'selected_form_type' in request.session:
                del request.session['selected_form_type']
            
            messages.success(request, "Texas Residency Affidavit saved successfully.")
        else:
            # User is canceling - just redirect back without saving
            if 'selected_form_type' in request.session:
                del request.session['selected_form_type']
        
        # Redirect to Applications after saving or submitting
        return redirect('Applications')
    
    # If not POST, just redirect to Applications
    return redirect('Applications')
def preview_application(request, app_id):
    """View function to display a read-only preview of an application form."""
    # Get the application
    application = get_object_or_404(Application, id=app_id)
    
    # Check if the user is authorized to view the application
    current_user = User.objects.filter(email=request.session.get("user_email")).first()
    if not current_user or (current_user != application.user and current_user.role not in ["superuser", "manager"]):
        return HttpResponseForbidden("You do not have permission to view this application.")
    
    # Get the form based on application type
    ferpa_form = None
    texas_affidavit = None
    
    if application.type == 'ferpa':
        ferpa_form = getattr(application, 'ferpa_form', None)
        if not ferpa_form:
            return HttpResponse("FERPA form data not found for this application.", status=404)
        template_name = "preview_application.html"
    elif application.type == 'texas_residency':
        texas_affidavit = getattr(application, 'texas_residency_affidavit', None)
        if not texas_affidavit:
            return HttpResponse("Texas Residency Affidavit data not found for this application.", status=404)
        template_name = "Preview_Texas_Residency_Affidavit.html"
    else:
        return HttpResponse("Unknown application type.", status=400)
    
    # Prepare context
    context = {
        "application": application,
        "user_signature": application.user.signature_image.url if application.user.signature_image else None,
    }
    
    # Add form-specific data to context
    if ferpa_form:
        context["ferpa_form"] = ferpa_form
    elif texas_affidavit:
        context["texas_affidavit"] = texas_affidavit
    
    return render(request, template_name, context)


def generate_pdf(request, app_id):
    """Generate and return a PDF of an application form."""
    
    # Get the application
    application = get_object_or_404(Application, id=app_id)
    
    # Determine which form to use based on application type
    if application.type == 'ferpa':
        try:
            form = application.ferpa_form
        except FERPAForm.DoesNotExist:
            return HttpResponse("FERPA form data not found for this application.", status=404)
        
        # Create a response with PDF content type
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="ferpa_authorization_{app_id}.pdf"'

        # Create PDF object
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        # Set font
        p.setFont("Helvetica", 12)

        # Title
        p.drawString(100, height - 50, "FERPA Authorization Form")
        p.drawString(100, height - 70, "Family Educational Rights and Privacy Act (FERPA)")
        p.line(100, height - 80, 500, height - 80)

        # Add content dynamically
        p.drawString(100, height - 100, f"Student Name: {form.student_name}")
        p.drawString(100, height - 120, f"University Division: {form.university_division}")
        p.drawString(100, height - 140, f"PeopleSoft ID: {form.peoplesoft_id}")

        p.drawString(100, height - 160, f"Selected Offices: {', '.join(form.offices)}")
        p.drawString(100, height - 180, f"Information Categories: {', '.join(form.info_categories)}")

        p.drawString(100, height - 200, f"Released To: {form.release_to}")
        p.drawString(100, height - 220, f"Additional Individuals: {form.additional_individuals or 'None'}")

        p.drawString(100, height - 240, f"Purpose: {', '.join(form.purposes)}")
        p.drawString(100, height - 260, f"Password for Phone Verification: {form.password}")

        # Date
        p.drawString(100, height - 280, f"Date: {form.form_date}")

        # Signature Section
        p.drawString(100, height - 320, "Student Signature:")

        # Check if the user has a signature image
        if application.user.signature_image:
            signature_path = application.user.signature_image.path
            if os.path.exists(signature_path):
                p.drawImage(signature_path, 100, height - 380, width=150, height=50)
            else:
                p.drawString(100, height - 360, "Signature not found.")
        else:
            p.drawString(100, height - 360, "No signature on file.")

    elif application.type == 'texas_residency':
        try:
            form = application.texas_residency_affidavit
        except TexasResidencyAffidavit.DoesNotExist:
            return HttpResponse("Texas Residency Affidavit data not found for this application.", status=404)
        
        # Create a response with PDF content type
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="texas_residency_{app_id}.pdf"'

        # Create PDF object
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        # Set font
        p.setFont("Helvetica", 12)

        # Title
        p.drawString(100, height - 50, "AFFIDAVIT")
        p.drawString(100, height - 70, "STATE OF TEXAS")
        p.drawString(100, height - 90, "Texas Residency Verification")
        p.line(100, height - 100, 500, height - 100)

        # County and Appearance
        p.drawString(100, height - 120, f"COUNTY OF: {form.county_name}")
        p.drawString(100, height - 140, "Before me, the undersigned Notary Public, on this day personally appeared")
        p.drawString(100, height - 160, f"{form.appeared_name}")
        p.drawString(100, height - 180, "known to me, who being by me duly sworn upon his/her oath, deposed and said:")

        # Personal information
        p.drawString(100, height - 200, f"1. My name is {form.full_name}")
        p.drawString(100, height - 220, f"   I am {form.age} years of age and have personal knowledge of the facts stated herein.")

        # Checkboxes
        p.drawString(100, height - 240, f"2. {'[X]' if form.graduated_check else '[ ]'} I graduated or will graduate from a Texas high school or received my GED in TX.")
        p.drawString(100, height - 260, f"3. {'[X]' if form.resided_check else '[ ]'} I resided in Texas for three years leading up to graduation/GED.")
        p.drawString(100, height - 280, f"4. I have resided or will have resided in Texas for 12 months prior to enrollment in {form.college_name}")
        p.drawString(100, height - 300, f"5. {'[X]' if form.permanent_resident_check else '[ ]'} I will file for permanent residency when eligible.")

        # Date
        p.drawString(100, height - 320, f"In witness whereof, this {form.day_of_month} day of {form.month}, {form.year}.")

        # Signature Section
        p.drawString(100, height - 350, "Signature:")

        # Check if the user has a signature image
        if application.user.signature_image:
            signature_path = application.user.signature_image.path
            if os.path.exists(signature_path):
                p.drawImage(signature_path, 100, height - 400, width=150, height=50)
            else:
                p.drawString(100, height - 370, "Signature not found.")
        else:
            p.drawString(100, height - 370, "No signature on file.")

        p.drawString(100, height - 430, f"Student ID: {form.student_id}")
        p.drawString(100, height - 450, f"Date of Birth: {form.student_dob.strftime('%m/%d/%Y')}")

        # Notary section
        if form.notary_day and form.notary_month and form.notary_year:
            p.drawString(100, height - 480, f"SWORN TO BEFORE ME on {form.notary_day} {form.notary_month}, {form.notary_year}")
            if form.notary_name:
                p.drawString(100, height - 500, f"Notary: {form.notary_name}")
    else:
        return HttpResponse("Unknown application type or not supported for PDF generation.", status=400)

    # Footer
    p.drawString(100, height - 520, "This is a digital document generated from the application system.")

    # Save PDF
    p.showPage()
    p.save()

    return response


def approve_form(request, app_id):
    """Approve an application if the user is manager or superuser."""
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    current_user = User.objects.filter(email=email).first()
    if not current_user or current_user.role not in ["superuser", "manager"]:
        return HttpResponseForbidden("You do not have permission to approve forms.")

    # Fetch the application that is pending
    application = get_object_or_404(Application, id=app_id, status="pending")

    # Approve the application using the built-in method
    application.approve(reviewer=current_user)

    # Redirect back to approvals page
    return redirect("ApplicationApprovals")



def return_form(request, app_id):
    """Return an application for revision if the user is manager or superuser."""
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    current_user = User.objects.filter(email=email).first()
    if not current_user or current_user.role not in ["superuser", "manager"]:
        return HttpResponseForbidden("You do not have permission to return forms.")

    # Get form review comments from POST request
    comments = request.POST.get("comments", "")
    
    # If there's no POST request, redirect to a form that collects comments
    if request.method != "POST":
        # Get the application
        application = get_object_or_404(Application, id=app_id, status="pending")
        context = {
            "application": application,
            "user": current_user
        }
        return render(request, "return_form.html", context)
    
    # Fetch the application that is pending
    application = get_object_or_404(Application, id=app_id, status="pending")

    # Return the application using the built-in method
    application.return_for_revision(reviewer=current_user, comments=comments)

    # Redirect back to approvals page
    return redirect("ApplicationApprovals")


def edit_ferpa_form(request, app_id):
    """Allow a user to edit their draft or returned FERPA form."""
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    current_user = User.objects.filter(email=email).first()
    if not current_user:
        return redirect("login")

    # 1) Fetch the application, ensuring user is the owner and it's in draft or returned
    application = get_object_or_404(
        Application,
        id=app_id,
        user=current_user,
        status__in=["draft", "returned"],
        type="ferpa"
    )

    # Get the associated FERPA form
    try:
        ferpa_form = application.ferpa_form
    except FERPAForm.DoesNotExist:
        return HttpResponse("FERPA form data not found for this application.", status=404)

    if request.method == "POST":
        # 2) Decide if user wants to "Save as Draft" or "Submit Form"
        if "save_as_draft" in request.POST:
            form_status = "draft"
            submitted_time = None
        else:
            form_status = "pending"
            submitted_time = timezone.now()

        # 3) Update existing ferpa_form record with new data
        ferpa_form.student_name = request.POST.get("student_name", "")
        ferpa_form.university_division = request.POST.get("university_division", "")
        ferpa_form.peoplesoft_id = request.POST.get("peoplesoft_id", "")
        ferpa_form.offices = request.POST.getlist("offices[]", [])
        ferpa_form.info_categories = request.POST.getlist("info_categories[]", [])
        ferpa_form.release_to = request.POST.get("release_to", "")
        ferpa_form.additional_individuals = request.POST.get("additional_individuals", "")
        ferpa_form.purposes = request.POST.getlist("purposes[]", [])
        ferpa_form.password = request.POST.get("password", "")
        ferpa_form.form_date = request.POST.get("form_date", timezone.now().date())
        ferpa_form.other_office_text = request.POST.get("other_office_text", "")
        ferpa_form.other_info_text = request.POST.get("other_info_text", "")
        ferpa_form.other_purpose_text = request.POST.get("other_purpose_text", "")
        ferpa_form.save()

        # Update the application status
        application.status = form_status
        application.submitted_at = submitted_time
        application.save()

        # If submitting (not draft), use the submit method to set timestamps properly
        if form_status == "pending":
            application.submit()

        return redirect("Applications")

    # If GET, pre-fill the same HTML template with ferpa_form data
    context = {
        "ferpa_form": ferpa_form,
        "application": application,
        "user": current_user
    }
    return render(request, "FERPA_Authorization_form.html", context)

def edit_texas_residency(request, app_id):
    """Allow a user to edit their draft or returned Texas Residency Affidavit."""
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    current_user = User.objects.filter(email=email).first()
    if not current_user:
        return redirect("login")

    # 1) Fetch the application
    application = get_object_or_404(
        Application,
        id=app_id,
        user=current_user,
        status__in=["draft", "returned"],
        type="texas_residency"
    )

    # Get or create the associated Texas Residency form
    try:
        texas_affidavit = application.texas_residency_affidavit
    except TexasResidencyAffidavit.DoesNotExist:
        # Create a new Texas Residency Affidavit if it doesn't exist
        texas_affidavit = TexasResidencyAffidavit(
            application=application,
            full_name=current_user.username,  # Default to user's name
            age=18,  # Default age - IMPORTANT: Set a default non-null value
            day_of_month=timezone.now().day,
            month=timezone.now().strftime('%B'),  # Month name
            year=timezone.now().year,
            county_name="",  # Empty string is valid for text fields
            appeared_name="",
            college_name="",
            student_id="",
            student_dob=timezone.now().date()  # Default date, user will update
        )
        texas_affidavit.save()
        
        # Update application name
        application.application_name = f"Texas Residency Affidavit - {texas_affidavit.full_name}"
        application.save()

    if request.method == "POST":
        # Handle form submission
        
        # Decide form status based on which button was clicked
        if "save_as_draft" in request.POST:
            form_status = "draft"
            submitted_time = None
        else:
            form_status = "pending"
            submitted_time = timezone.now()
            
        # Process student DOB
        try:
            student_dob = timezone.datetime.strptime(request.POST.get('student_dob', ''), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            student_dob = timezone.now().date()
            
        # Get age with a valid default value if missing or invalid
        try:
            age = int(request.POST.get('age', 18))
            if age < 1:  # Make sure age is positive
                age = 18
        except (ValueError, TypeError):
            age = 18  # Default age if value is invalid
            
        # Update the Texas Residency Affidavit
        texas_affidavit.county_name = request.POST.get('county_name', '')
        texas_affidavit.appeared_name = request.POST.get('appeared_name', '')
        texas_affidavit.full_name = request.POST.get('full_name', '')
        texas_affidavit.age = age  # Use validated age value
        texas_affidavit.graduated_check = 'graduated_check' in request.POST
        texas_affidavit.resided_check = 'resided_check' in request.POST
        texas_affidavit.permanent_resident_check = 'permanent_resident_check' in request.POST
        texas_affidavit.college_name = request.POST.get('college_name', '')
        
        # Get day_of_month with a valid default value
        try:
            day_of_month = int(request.POST.get('day_of_month', 1))
            if day_of_month < 1 or day_of_month > 31:
                day_of_month = 1
        except (ValueError, TypeError):
            day_of_month = 1
            
        texas_affidavit.day_of_month = day_of_month
        texas_affidavit.month = request.POST.get('month', '')
        
        # Get year with a valid default value
        try:
            year = int(request.POST.get('year', 2025))
            if year < 2000 or year > 2050:
                year = 2025
        except (ValueError, TypeError):
            year = 2025
            
        texas_affidavit.year = year
        texas_affidavit.student_id = request.POST.get('student_id', '')
        texas_affidavit.student_dob = student_dob
        
        # Only update notary fields if they are provided
        notary_day = request.POST.get('notary_day')
        if notary_day and notary_day.strip():
            try:
                texas_affidavit.notary_day = int(notary_day)
            except ValueError:
                pass
            
        texas_affidavit.notary_month = request.POST.get('notary_month', '')
        
        notary_year = request.POST.get('notary_year')
        if notary_year and notary_year.strip():
            try:
                texas_affidavit.notary_year = int(notary_year)
            except ValueError:
                pass
            
        texas_affidavit.notary_name = request.POST.get('notary_name', '')
        
        # Save the Texas Residency Affidavit
        texas_affidavit.save()
        
        # Update application name and status
        application.application_name = f"Texas Residency Affidavit - {texas_affidavit.full_name}"
        application.status = form_status
        application.submitted_at = submitted_time
        application.save()
        
        # If submitting, use the submit method to set timestamps properly
        if form_status == "pending":
            application.submit()

        # Redirect to dashboard
        return redirect("Applications")

    # If GET, pre-fill the form with texas_affidavit data
    context = {
        "texas_affidavit": texas_affidavit,
        "application": application,
        "user": current_user,
        "active_page": "Applications"
    }
    
    # Fix: Use the correct template path (update this to match your actual template location)
    return render(request, "Texas_Residency_Affidavit_Form.html", context)