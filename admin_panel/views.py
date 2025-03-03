from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
import os
from django.views.decorators.csrf import csrf_exempt
from admin_panel.models import User
from .forms import ReleaseForm
import msal
import requests

def check_session(request):
    """Helper function to check if a user is logged in"""
    if "access_token" not in request.session:
        return redirect("/admin/login/")  # Redirect to login if not authenticated
    return None

def rr_form(request):
    """Render the Residency Reclassification Form page, checking for login session."""
    session_redirect = check_session(request)
    if session_redirect:
        return session_redirect
    return render(request, "rr_form.html")

def release_form(request):
    """Render the Authorization to Release Educational Records form and handle file uploads"""
    
    # Ensure user is authenticated via session
    user_email = request.session.get("user_email")
    if not user_email:
        return redirect("login")

    # Fetch user details from the database
    current_user = User.objects.filter(email=user_email).first()
    
    if current_user:
        name_parts = current_user.username.split(", ")
        if len(name_parts) == 2:
            last_name, first_name = name_parts[0], name_parts[1].split()[0]
            full_name = f"{first_name} {last_name}"
        else:
            full_name = current_user.username
    else:
        full_name = "Unknown User"

    if request.method == "POST":
        form = ReleaseForm(request.POST, request.FILES)
        if form.is_valid():
            signature_file = request.FILES["student_signature"]
            file_extension = os.path.splitext(signature_file.name)[1].lower()

            # Ensure only PNG, JPG, and JPEG are accepted
            if file_extension not in [".png", ".jpg", ".jpeg"]:
                return render(request, "release_form.html", {"form": form, "error": "Invalid file format. Only PNG, JPG, and JPEG are allowed."})

            # Define the file save path
            signature_path = os.path.join(settings.MEDIA_ROOT, "signatures", signature_file.name)

            # Save the file to the media directory
            with open(signature_path, "wb+") as destination:
                for chunk in signature_file.chunks():
                    destination.write(chunk)

            return render(request, "release_form.html", {"form": form, "message": "File uploaded successfully!"})

    else:
        form = ReleaseForm(initial={'student_name': full_name, 'student_email': user_email})

    return render(request, "release_form.html", {"form": form})
    
def homepage(request):
    """Render the homepage."""
    return render(request, "homepage.html")

def forms_page(request):
    """Render the Forms page."""
    return render(request, "forms.html")
    


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
