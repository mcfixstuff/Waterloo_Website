from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from admin_panel.models import User
import msal
import requests
from .forms import UserSignatureForm,FERPAForm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


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
    """Render the Applications page with signature form and FERPA forms."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    signature_form = UserSignatureForm(instance=user)
    
    # Fetch FERPA forms for this user
    ferpa_forms = FERPAForm.objects.filter(user=user).order_by('-updated_at')
    
    context = {
        'active_page': 'Applications',
        'user': user,
        'signature_form': signature_form,
        'ferpa_forms': ferpa_forms  # Add this line to pass FERPA forms to the template
    }
    return render(request, "admin_panel/Applications.html", context)


def ApplicationApprovals(request):
    """Render the ApplicationApprovals view with permission check."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    # Get the current user
    current_user = User.objects.filter(email=email).first()
    
    # Check if the user is a superuser or manager
    if not current_user or (current_user.role != "superuser" and current_user.role != "manager"):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    context = {
        'active_page': 'ApplicationApprovals',
        'user': current_user
        # other context data
    }
    return render(request, "admin_panel/ApplicationApprovalsDashboard.html", context)





def select_form_type(request):
    """Handle form type selection from the modal."""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Redirect based on the form type selection
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
            return HttpResponse('leave_absence_form')
        elif form_type == 'leave_absence':
            return HttpResponse('leave_absence_form')
        else:
            messages.error(request, "Invalid form type selected")
    
    return redirect('Applications')
    
    
    


def save_ferpa_form(request):
    """Simple view to save FERPA form data to database"""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        # Create a new form instance
        ferpa_form = FERPAForm(
            user=user,
            student_name=request.POST.get('student_name', ''),
            university_division=request.POST.get('university_division', ''),
            peoplesoft_id=request.POST.get('peoplesoft_id', ''),
            offices=request.POST.getlist('offices[]', []),
            info_categories=request.POST.getlist('info_categories[]', []),
            release_to=request.POST.get('release_to', ''),
            additional_individuals=request.POST.get('additional_individuals', ''),
            purposes=request.POST.getlist('purposes[]', []),
            password=request.POST.get('password', ''),
            form_date=request.POST.get('form_date', timezone.now().date()),
            other_office_text=request.POST.get('other_office_text', ''),
            other_info_text=request.POST.get('other_info_text', ''),
            other_purpose_text=request.POST.get('other_purpose_text', ''),
            status='pending',  # Set as pending by default
            submitted_at=timezone.now()
        )
        ferpa_form.save()
        
        # Return a success response
        return redirect('Applications')
    
    # If not POST, redirect to home
    return redirect('Applications')

def preview_application(request, form_id):
    """View function to display a read-only preview of a FERPA form."""
    ferpa_form = get_object_or_404(FERPAForm, id=form_id)
    
    # Check if the user is authorized to view the form
    current_user = User.objects.filter(email=request.session.get("user_email")).first()
    if not current_user or (current_user != ferpa_form.user and current_user.role not in ["superuser", "manager"]):
        return HttpResponseForbidden("You do not have permission to view this application.")

    context = {
        "ferpa_form": ferpa_form,
        # If user has a signature, pass its URL to the template
        "user_signature": ferpa_form.user.signature_image.url if ferpa_form.user.signature_image else None,
    }
    return render(request, "preview_application.html", context)


def generate_pdf(request, form_id):
    """Generate and return a simple PDF using ReportLab with signature image."""
    
    # Get FERPA form data
    ferpa_form = get_object_or_404(FERPAForm, id=form_id)
    
    # Create a response with PDF content type
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ferpa_form_{form_id}.pdf"'

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
    p.drawString(100, height - 100, f"Student Name: {ferpa_form.student_name}")
    p.drawString(100, height - 120, f"University Division: {ferpa_form.university_division}")
    p.drawString(100, height - 140, f"PeopleSoft ID: {ferpa_form.peoplesoft_id}")

    p.drawString(100, height - 160, f"Selected Offices: {', '.join(ferpa_form.offices)}")
    p.drawString(100, height - 180, f"Information Categories: {', '.join(ferpa_form.info_categories)}")

    p.drawString(100, height - 200, f"Released To: {ferpa_form.release_to}")
    p.drawString(100, height - 220, f"Additional Individuals: {ferpa_form.additional_individuals or 'None'}")

    p.drawString(100, height - 240, f"Purpose: {', '.join(ferpa_form.purposes)}")
    p.drawString(100, height - 260, f"Password for Phone Verification: {ferpa_form.password}")

    # Date
    p.drawString(100, height - 280, f"Date: {ferpa_form.form_date}")

    # Signature Section
    p.drawString(100, height - 320, "Student Signature:")

    # Check if the user has a signature image
    if ferpa_form.user.signature_image:
        signature_path = ferpa_form.user.signature_image.path
        if os.path.exists(signature_path):
            p.drawImage(signature_path, 100, height - 380, width=150, height=50)
        else:
            p.drawString(100, height - 360, "Signature not found.")
    else:
        p.drawString(100, height - 360, "No signature on file.")

    # Footer
    p.drawString(100, height - 400, "This is a digital document generated from the FERPA system.")

    # Save PDF
    p.showPage()
    p.save()

    return response