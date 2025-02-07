from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
import msal
import requests
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from admin_panel.models import User 
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden



# Create your views here.

def show_login_page(request):
    return render(request, "admin_panel/login.html")

@csrf_exempt  # Allows form submission without CSRF issues
def trigger_microsoft_login(request):
    auth_url =  auth_url = (
        f"{settings.MICROSOFT_AUTH['AUTHORITY']}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_AUTH['CLIENT_ID']}"
        f"&response_type=code"
        f"&redirect_uri={settings.MICROSOFT_AUTH['REDIRECT_URI']}"
        f"&response_mode=query"
        f"&scope=User.Read"
        f"&prompt=select_account"  # ✅ Allows switching accounts but keeps session if same user
    )
    return redirect(auth_url)

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

            if not user.status:  # ✅ Prevent disabled users from logging in
                return redirect("login")

            request.session["access_token"] = access_token
            return redirect("admin_dashboard")

    return redirect("login")


    # Always return a response
    return redirect("login")

def logout_view(request):
    # Clear session
    request.session.flush()   
      
    # Force logout from Microsoft
    logout_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/logout?post_logout_redirect_uri={settings.MICROSOFT_AUTH['REDIRECT_URI']}"
    
    return redirect('login')

def admin_dashboard(request):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")

    headers = {"Authorization": f"Bearer {access_token}"}
    user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()

    # ✅ Get the logged-in user from the database
    current_user = User.objects.filter(email=user_info.get("mail")).first()

    return render(request, "admin_panel/dashboard.html", {
        "user_name": user_info.get("displayName", "User"),
        "user_role": current_user.role if current_user else "basicuser",  # Clearly pass the logged-in user's role
        "users": User.objects.all(),  # Pass all users for the table
    })


    
    
    




def toggle_user_status(request, user_id):
    if "access_token" not in request.session:
        return redirect("login")  # ✅ Redirect if user is not logged in

    # ✅ Get the logged-in user from the database
    current_user = User.objects.filter(email=request.session.get("user_email")).first()
    
    if not current_user or current_user.role != "superuser":  
        return HttpResponseForbidden("You do not have permission to perform this action.")  # ✅ Block non-superusers

    # ✅ Get the user whose status is being toggled
    user = get_object_or_404(User, id=user_id)
    user.status = not user.status  # ✅ Toggle status
    user.save()

    return redirect("admin_dashboard")  # ✅ Refresh dashboard

