# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, FileResponse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import date as date_filter
from django.contrib import messages
from django.db.models import Q

# App-specific imports
from admin_panel.models import User, Application, FERPAForm, TexasResidencyAffidavit,Department,ApprovalRule,DepartmentApproval
from .forms import UserSignatureForm

# Third-party imports
import requests
import tempfile
import subprocess
import os
import msal
from shutil import copyfile

# From academic_forms
from academic_forms import api_client

################ START OF show_login_page FUNCTION ####################
# This function renders the login page for the admin panel. It is the
# default view shown to users trying to access the login route.
########################################################################
def show_login_page(request):
    return render(request, "admin_panel/login.html")
############## END OF show_login_page FUNCTION #########################


################ START OF trigger_microsoft_login FUNCTION ####################
# This function initiates the Microsoft OAuth2 login by building the auth URL
# and redirecting the user to the Microsoft login page.
########################################################################
@csrf_exempt
def trigger_microsoft_login(request):
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
############## END OF trigger_microsoft_login FUNCTION #########################


################ START OF login_view FUNCTION ####################
# This function handles the redirect after Microsoft login. It retrieves the 
# access token using the authorization code and fetches user info from Graph API.
# It then either creates a new user or logs the existing one in.
########################################################################
def login_view(request):
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
############## END OF login_view FUNCTION #########################


################ START OF logout_view FUNCTION ####################
# Logs out the current user by clearing the session and redirecting them
# to the login page using Microsoft's logout endpoint.
########################################################################
def logout_view(request):
    request.session.flush()
    request.session.pop("cougar_verified", None)
    logout_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={settings.MICROSOFT_AUTH['REDIRECT_URI']}"
    )
    return redirect('login')
############## END OF logout_view FUNCTION #########################


################ START OF admin_dashboard FUNCTION ####################
# This function loads the admin dashboard view. It uses the current user's 
# session to retrieve their info and display user management tools and 
# approval rules. Only accessible by managers or superusers.
########################################################################
def admin_dashboard(request):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")

    headers = {"Authorization": f"Bearer {access_token}"}
    user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()
    current_user = User.objects.filter(email=user_info.get("mail")).first()

    if current_user and current_user.role == "basicuser":
        return redirect("Applications")

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
        "active_page": "dashboard",
        "approval_rules": ApprovalRule.objects.all(),
    })

############## END OF admin_dashboard FUNCTION #########################

################ START OF toggle_user_status FUNCTION ####################
# This function toggles whether a user's account is enabled or disabled.
# It can only be accessed by a logged-in user with the "superuser" role.
########################################################################
def toggle_user_status(request, user_id):
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
############## END OF toggle_user_status FUNCTION #########################


################ START OF change_user_role FUNCTION ####################
# This function allows a superuser to update another user's role. It also
# ensures that a superuser cannot be demoted by mistake or malicious intent.
########################################################################
def change_user_role(request, user_id):
    if "access_token" not in request.session:
        return redirect("login")

    current_user = User.objects.filter(email=request.session.get("user_email")).first()
    if not current_user or current_user.role != "superuser":
        return HttpResponseForbidden("You do not have permission to perform this action.")

    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get("new_role")

    if user.role == "superuser" and new_role != "superuser":
        return HttpResponseForbidden("You cannot demote a superuser.")

    if new_role in ["superuser", "manager", "basicuser", "approver"]:
        user.role = new_role
        user.save()

    return redirect("admin_dashboard")
############## END OF change_user_role FUNCTION #########################


################ START OF upload_signature FUNCTION ####################
# This function lets the logged-in user upload a signature image. It displays
# the form on GET and saves the image on POST. Only works if the user is logged in.
########################################################################
def upload_signature(request):
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

    context = {
        'active_page': 'Applications',
        'user': user,
        'signature_form': form
    }
    return render(request, "admin_panel/Applications.html", context)
############## END OF upload_signature FUNCTION #########################

################ START OF Applications FUNCTION ####################
# Renders the Applications page for a user. It includes their submitted
# applications, a signature upload form, and available forms fetched from
# the academic_forms API. It also tracks Cougar ID verification.
########################################################################
def Applications(request):
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    user = get_object_or_404(User, email=email)
    signature_form = UserSignatureForm(instance=user)
    applications = Application.objects.filter(user=user).order_by('-updated_at')

    api_forms = api_client.get_all_forms(email=email)
    for form in api_forms:
        print(f"Form ID: {form['id']}, Status: {form['status']}")

    context = {
        'active_page': 'Applications',
        'user': user,
        'signature_form': signature_form,
        'applications': applications,
        'api_forms': api_forms,
        'require_cougar_id': True,
        'cougar_verified': request.session.get("cougar_verified", False),
    }
    return render(request, "admin_panel/Applications.html", context)
############## END OF Applications FUNCTION #########################


################ START OF ApplicationApprovals FUNCTION ####################
# This view is for superusers, managers, and approvers to see pending forms
# requiring their department's approval. It also includes some dashboard stats
# and recent forms, and calculates which departments have yet to approve each form.
########################################################################
def ApplicationApprovals(request):
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    current_user = User.objects.filter(email=email).first()

    if not current_user or current_user.role not in ["superuser", "manager", "approver"]:
        return HttpResponseForbidden("You do not have permission to access this page.")

    if current_user.role == "superuser":
        pending_forms = Application.objects.filter(status="pending").order_by("-created_at")
    else:
        dept = current_user.department
        rules = ApprovalRule.objects.filter(departments_required=dept)
        form_types = [rule.form_type for rule in rules]
        approved_ids = DepartmentApproval.objects.filter(
            department=dept
        ).values_list("application_id", flat=True)

        pending_forms = Application.objects.filter(
            status="pending",
            type__in=form_types
        ).exclude(id__in=approved_ids).order_by("-created_at")

    approved_count = Application.objects.filter(status='approved').count()
    returned_count = Application.objects.filter(status='returned').count()
    today_count = Application.objects.filter(submitted_at__date=timezone.now().date()).count()

    recent_forms = Application.objects.filter(
        status__in=["approved", "returned"]
    ).order_by('-reviewed_at', '-updated_at')[:5]

    api_forms = api_client.get_all_forms()
    remaining_approvals = {}

    for app in pending_forms:
        try:
            rule = ApprovalRule.objects.get(form_type=app.type)
            required = set(rule.departments_required.all())
        except ApprovalRule.DoesNotExist:
            required = set()

        approved = set(
            Department.objects.filter(
                id__in=DepartmentApproval.objects.filter(application=app).values_list("department_id", flat=True)
            )
        )
        remaining = required - approved
        remaining_approvals[app.id] = [dept.name for dept in remaining]

    context = {
        "active_page": "ApplicationApprovals",
        "user": current_user,
        "pending_forms": pending_forms,
        "recent_forms": recent_forms,
        "pending_count": pending_forms.count(),
        "approved_count": approved_count,
        "returned_count": returned_count,
        "today_count": today_count,
        "api_forms": api_forms,
        "remaining_approvals": remaining_approvals,
    }
    return render(request, "admin_panel/ApplicationApprovalsDashboard.html", context)
############## END OF ApplicationApprovals FUNCTION #########################

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
        if form_type in ['ferpa_authorization', 'texas_affidavit']:
            application_type = {
                'ferpa_authorization': 'ferpa',
                'texas_affidavit': 'texas_residency'
            }.get(form_type)
            request.session['selected_form_type'] = application_type

            if form_type == 'ferpa_authorization':
                context = {'user': user, 'active_page': 'Applications'}
                return render(request, 'FERPA_Authorization_form.html', context)
            elif form_type == 'texas_affidavit':
                context = {'user': user, 'active_page': 'Applications'}
                return render(request, 'Texas_Residency_Affidavit_Form.html', context)
        elif form_type == 'special_circumstance':
            # Redirect to the special circumstance form
            return redirect('new_special_circumstance_form')
        elif form_type == 'course_drop':
            # Redirect to the course drop form
            return redirect('new_course_drop_form')
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
        is_draft = "save_as_draft" in request.POST
        is_submit = "submit_form" in request.POST

        if is_draft or is_submit:
            application_id = request.session.get('current_application_id')
            if not application_id:
                application_type = request.session.get('selected_form_type')
                if not application_type:
                    messages.error(request, "Form type not found. Please try again.")
                    return redirect('Applications')

                # Get dynamic department from ApprovalRule
                rule = ApprovalRule.objects.filter(form_type=application_type).first()
                assigned_dept = rule.departments_required.first() if rule else None

                application = Application.objects.create(
                    user=user,
                    type=application_type,
                    department=assigned_dept,
                    application_name=f"New {application_type.replace('_', ' ').title()} Application",
                    status="draft")
                request.session['current_application_id'] = application.id
            else:
                application = get_object_or_404(Application, id=application_id, user=user)

            ferpa_form, created = FERPAForm.objects.get_or_create(application=application)
            ferpa_form.student_name = request.POST.get("student_name", "")
            ferpa_form.university_division = request.POST.get("university_division", "")
            ferpa_form.peoplesoft_id = request.POST.get("peoplesoft_id", "")
            ferpa_form.offices = request.POST.getlist("offices[]", [])
            ferpa_form.info_categories = request.POST.getlist("info_categories[]", [])
            ferpa_form.release_to = request.POST.get("release_to", "")
            ferpa_form.additional_individuals = request.POST.get("additional_individuals", "")
            ferpa_form.purposes = request.POST.getlist("purposes[]", [])
            ferpa_form.password = request.POST.get("password", "")
            ferpa_form.form_date = timezone.now().date()
            ferpa_form.save()

            if is_submit:
                application.status = "pending"
                application.submitted_at = timezone.now()
            else:
                application.status = "draft"
            application.updated_at = timezone.now()
            application.application_name = f"FERPA Form - {ferpa_form.student_name}"
            application.save()

            for opt in ["current_application_id", "selected_form_type"]:
                request.session.pop(opt, None)

            messages.success(request, "FERPA Authorization saved successfully.")

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
        is_draft = "save_as_draft" in request.POST
        is_submit = "submit_form" in request.POST

        if is_draft or is_submit:
            application_id = request.session.get('current_application_id')
            if not application_id:
                application_type = request.session.get('selected_form_type')
                if not application_type:
                    messages.error(request, "Form type not found. Please try again.")
                    return redirect('Applications')
                
                rule = ApprovalRule.objects.filter(form_type=application_type).first()
                assigned_dept = rule.departments_required.first() if rule else None

                application = Application.objects.create(
                    user=user,
                    type=application_type,
                    department=assigned_dept,
                    application_name=f"New {application_type.replace('_', ' ').title()} Application",
                    status='draft' if is_draft else 'pending',
                    submitted_at=None if is_draft else timezone.now()
                )
                
                print(application.department)
            else:
                try:
                    application = Application.objects.get(id=application_id, user=user)
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

            try:
                student_dob = timezone.datetime.strptime(request.POST.get('student_dob', ''), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                student_dob = timezone.now().date()

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

            application.application_name = f"Texas Residency Affidavit - {texas_affidavit.full_name}"
            application.save()

            if is_submit:
                # If you have a submit method, call it here
                application.submit()

            request.session.pop('current_application_id', None)
            request.session.pop('selected_form_type', None)

            messages.success(request, "Texas Residency Affidavit saved successfully.")
        else:
            request.session.pop('selected_form_type', None)

        return redirect('Applications')

    return redirect('Applications')


def preview_application(request, app_id):
    """Display a read-only preview of an application form."""
    application = get_object_or_404(Application, id=app_id)
    current_user = User.objects.filter(email=request.session.get("user_email")).first()
    if not current_user or (current_user != application.user and current_user.role not in ["superuser", "manager"]):
        return HttpResponseForbidden("You do not have permission to view this application.")

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

    context = {
        "application": application,
        "user_signature": application.user.signature_image.url if application.user.signature_image else None,
    }
    if ferpa_form:
        context["ferpa_form"] = ferpa_form
    elif texas_affidavit:
        context["texas_affidavit"] = texas_affidavit

    return render(request, template_name, context)

def generate_pdf(request, app_id):


    # Retrieve the application by its ID.
    application = get_object_or_404(Application, id=app_id)

    # Branch based on the application type.
    if application.type == 'ferpa':
        ferpa_form = getattr(application, 'ferpa_form', None)
        if not ferpa_form:
            return HttpResponse("FERPA form not found", status=404)
        # Format list fields so that each item is preceded by \item.
        offices = "\n".join([f"\\item {office}" for office in ferpa_form.offices])
        info_categories = "\n".join([f"\\item {cat}" for cat in ferpa_form.info_categories])
        purposes = "\n".join([f"\\item {purpose}" for purpose in ferpa_form.purposes])
        context = {
            'student_name': ferpa_form.student_name,
            'university_division': ferpa_form.university_division,
            'peoplesoft_id': ferpa_form.peoplesoft_id,
            'offices': offices,
            'info_categories': info_categories,
            'release_to': ferpa_form.release_to,
            'additional_individuals': ferpa_form.additional_individuals or "",
            'purposes': purposes,
            'password': ferpa_form.password,
            'form_date': date_filter(ferpa_form.form_date, "F d, Y"),
            # For FERPA, use the signature image if available.
            'signature_path': 'signature.png' if application.user.signature_image else 'no_signature.png',
        }
        template_filename = 'ferpa_template.tex'
    elif application.type == 'texas_residency':
        texas_form = getattr(application, 'texas_residency_affidavit', None)
        if not texas_form:
            return HttpResponse("Texas residency form not found", status=404)
        # Prepare checkbox representations.
        graduated_checkbox = "$\\boxtimes$" if texas_form.graduated_check else "$\\square$"
        resided_checkbox = "$\\boxtimes$" if texas_form.resided_check else "$\\square$"
        permanent_resident_checkbox = "$\\boxtimes$" if texas_form.permanent_resident_check else "$\\square$"
        context = {
            'county': texas_form.county_name,
            'appeared_name': texas_form.appeared_name,
            'full_name': texas_form.full_name,
            'age': texas_form.age,
            'graduated_checkbox': graduated_checkbox,
            'resided_checkbox': resided_checkbox,
            'permanent_resident_checkbox': permanent_resident_checkbox,
            'college_name': texas_form.college_name,
            'day': texas_form.day_of_month,
            'month': texas_form.month,
            'year': texas_form.year,
            'student_id': texas_form.student_id,
            'dob': date_filter(texas_form.student_dob, "F d, Y"),
            'notary_day': texas_form.notary_day if texas_form.notary_day is not None else "",
            'notary_month': texas_form.notary_month if texas_form.notary_month else "",
            'notary_year': texas_form.notary_year if texas_form.notary_year is not None else "",
            'notary_name': texas_form.notary_name if texas_form.notary_name else "",
        }
        # Instead of printing the user's name, use their signature photo if available.
        if application.user.signature_image:
            context['signature_path'] = 'signature.png'
        else:
            context['signature_path'] = 'no_signature.png'
        template_filename = 'texas_residency_template.tex'
    else:
        return HttpResponse("Unsupported form type", status=400)

    # Get the LaTeX template file.
    tex_template_path = os.path.join(settings.LATEX_TEMPLATE_DIR, template_filename)
    if not os.path.exists(tex_template_path):
        return HttpResponse("Template not found", status=404)

    # Read the LaTeX template.
    with open(tex_template_path, "r", encoding="utf-8") as f:
        tex_template = f.read()

    # Replace all placeholders in the template.
    # We handle both <<key>> and << key >> forms.
    for key, value in context.items():
        tex_template = tex_template.replace(f"<<{key}>>", str(value))
        tex_template = tex_template.replace(f"<< {key} >>", str(value))

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the rendered LaTeX source to a file.
        tex_file_path = os.path.join(tmpdir, "form.tex")
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(tex_template)

        # For both form types, if a signature image is to be used, copy it into tmpdir.
        if context.get('signature_path') == 'signature.png':
            src = application.user.signature_image.path
            dest = os.path.join(tmpdir, "signature.png")
            if os.path.exists(src):
                from shutil import copyfile
                copyfile(src, dest)

        # Run pdflatex to compile the .tex file.
        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "form.tex"],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() + "\n" + e.stdout.decode()
            return HttpResponse(f"LaTeX compile error:\n\n{error_output}", status=500)

        pdf_path = os.path.join(tmpdir, "form.pdf")
        return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")


def approve_form(request, app_id):
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    current_user = User.objects.filter(email=email).first()

    if not current_user:
        return HttpResponseForbidden("Not logged in")

    application = get_object_or_404(Application, id=app_id, status="pending")

    # ✅ Superuser can approve directly
    if current_user.role == "superuser":
        application.approve(reviewer=current_user)
        return redirect("ApplicationApprovals")

    # ✅ Manager/Approver must belong to a department
    if not current_user.department:
        return HttpResponseForbidden("No department assigned")

    # ✅ Prevent duplicate approvals
    already_approved = DepartmentApproval.objects.filter(
        application=application,
        department=current_user.department
    ).exists()

    if not already_approved:
        # Record this department's approval
        DepartmentApproval.objects.create(
            application=application,
            department=current_user.department,
            approved_by=current_user
        )

    # ✅ Check if all required departments have approved
    rule = ApprovalRule.objects.filter(form_type=application.type).first()
    required_departments = rule.departments_required.all() if rule else []

    approved_departments = DepartmentApproval.objects.filter(
        application=application
    ).values_list("department", flat=True)

    if set(dept.id for dept in required_departments).issubset(set(approved_departments)):
        application.approve(reviewer=current_user)

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

    comments = request.POST.get("comments", "")
    if request.method != "POST":
        application = get_object_or_404(Application, id=app_id, status="pending")
        context = {"application": application, "user": current_user}
        return render(request, "return_form.html", context)

    application = get_object_or_404(Application, id=app_id, status="pending")
    application.return_for_revision(reviewer=current_user, comments=comments)
    DepartmentApproval.objects.filter(application=application).delete()
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

    application = get_object_or_404(
        Application,
        id=app_id,
        user=current_user,
        status__in=["draft", "returned"],
        type="ferpa"
    )

    try:
        ferpa_form = application.ferpa_form
    except FERPAForm.DoesNotExist:
        return HttpResponse("FERPA form data not found for this application.", status=404)

    if request.method == "POST":
        form_status = "draft" if "save_as_draft" in request.POST else "pending"
        submitted_time = None if form_status == "draft" else timezone.now()

        def latex_checkboxes(selected, all_options):
            lines = []
            for opt in all_options:
                symbol = r"\boxtimes" if opt in selected else r"\square"
                lines.append(f"\\item ${symbol}$ {opt}")
            return "\n".join(lines)

        selected_offices = request.POST.getlist("offices[]")
        selected_categories = request.POST.getlist("info_categories[]")
        selected_purposes = request.POST.getlist("purposes[]")

        ALL_OFFICES = [
            "Office of the University Registrar",
            "Scholarships and Financial Aid",
            "Student Business Services",
            "Admissions",
            "Student Success Center",
            "Academic Advising",
            "Academic Dean’s Office",
            "Other"
        ]
        ALL_CATEGORIES = [
            "Academic Records",
            "Billing/Financial Aid",
            "Student Conduct",
            "Grades/Academic Standing",
            "Enrollment",
            "Other"
        ]
        ALL_PURPOSES = [
            "Family",
            "Employer/Prospective Employer",
            "Health Insurance",
            "Legal",
            "Scholarships/Financial Aid",
            "Other"
        ]

        ferpa_form.student_name = request.POST.get("student_name", "")
        ferpa_form.university_division = request.POST.get("university_division", "")
        ferpa_form.peoplesoft_id = request.POST.get("peoplesoft_id", "")
        ferpa_form.offices = selected_offices
        ferpa_form.info_categories = selected_categories
        ferpa_form.release_to = request.POST.get("release_to", "")
        ferpa_form.additional_individuals = request.POST.get("additional_individuals", "")
        ferpa_form.purposes = selected_purposes
        ferpa_form.password = request.POST.get("password", "")
        ferpa_form.form_date = request.POST.get("form_date", timezone.now().date())
        ferpa_form.other_office_text = request.POST.get("other_office_text", "")
        ferpa_form.other_info_text = request.POST.get("other_info_text", "")
        ferpa_form.other_purpose_text = request.POST.get("other_purpose_text", "")
        ferpa_form.save()

        application.status = form_status
        application.submitted_at = submitted_time
        application.application_name = f"FERPA Authorization - {ferpa_form.student_name}"
        application.save()

        if form_status == "pending":
            application.submit()

        return redirect("Applications")

    context = {
        "ferpa_form": ferpa_form,
        "application": application,
        "user": current_user,
        "active_page": "Applications"
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






#v4 

def verify_cougar_id(request):
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")

    user = get_object_or_404(User, email=email)

    if request.method == "POST":
        entered = request.POST.get("cougar_id", "").strip()

        if not (entered.isdigit() and len(entered) == 7):
            messages.error(request, "Cougar‑ID must be exactly 7 digits.")
            return redirect("Applications")

        if user.cougar_id:
            # Already set → just compare
            if entered == user.cougar_id:
                print("good")
                request.session["cougar_verified"] = True
                messages.success(request, "Cougar‑ID verified ✔")
                
            else:
                
                messages.error(request, "Cougar‑ID doesn’t match our records.")
                print("not ")
        else:
            # First time → persist it
            user.cougar_id = entered
            user.save(update_fields=["cougar_id"])
            request.session["cougar_verified"] = True 
            messages.success(request, "Cougar‑ID saved and verified ✔")

    return redirect("Applications")

@csrf_exempt
def change_user_department(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        dept_code = request.POST.get("new_department")
        department = Department.objects.filter(code=dept_code).first()
        user.department = department
        print("Submitted code:", dept_code)
        print("Department found:", department)

        user.save()
        
        
    return redirect("admin_dashboard")

@csrf_exempt
def set_approval_rule(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        department_codes = request.POST.getlist("departments")

        if form_type and department_codes:
            rule, created = ApprovalRule.objects.get_or_create(form_type=form_type)
            rule.departments_required.clear()
            for code in department_codes:
                dept = Department.objects.filter(code=code).first()
                if dept:
                    rule.departments_required.add(dept)
            rule.save()
            messages.success(request, f"Approval rule updated for {form_type}")
        else:
            messages.error(request, "Please select a form type and at least one department.")

    return redirect("admin_dashboard")