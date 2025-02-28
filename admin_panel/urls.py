from django.urls import path
from . import views



from django.urls import path
from .views import show_login_page, trigger_microsoft_login, login_view, admin_dashboard,Applications, ApplicationApprovals

urlpatterns = [
    path("login/", show_login_page, name="login"),  # Shows login page with a button
    path("login/microsoft/", trigger_microsoft_login, name="trigger_microsoft_login"),  # Starts Microsoft login
    path("auth/callback/", login_view, name="login_view"),  # Handles login response from Microsoft
    path("dashboard/", admin_dashboard, name="admin_dashboard"),
    path('logout/', views.logout_view, name='logout'), # logout 
    path("toggle-user/<int:user_id>/", views.toggle_user_status, name="toggle_user_status"),
    path("change-role/<int:user_id>/", views.change_user_role, name="change_user_role"),  # ✅ New route
    path("ApplicationApprovals/", views.ApplicationApprovals, name="ApplicationApprovals"),  # ✅ New route
    path("Applications/", views.Applications, name="Applications"),  # ✅ New route
    
]
