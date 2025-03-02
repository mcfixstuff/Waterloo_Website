from django.urls import path
from . import views



from django.urls import path
from .views import show_login_page, trigger_microsoft_login, login_view, admin_dashboard,Applications, ApplicationApprovals,preview_application,generate_pdf,approve_ferpa_form,return_ferpa_form

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
    
    
    # form sellection
    path("select-form/", views.select_form_type, name="select_form_type"),
    
        # Add this new URL for signature upload
    path("upload-signature/", views.upload_signature, name="upload_signature"),
    
    
    # storing data from from 1 
    path('save-ferpa-form/', views.save_ferpa_form, name='save_ferpa_form'),
    
    path("preview_application/<int:form_id>/", preview_application, name="preview_application"),
    
    path("ferpa/<int:form_id>/pdf/", generate_pdf, name="generate_pdf"),
    
    
    path("approve_form/<int:form_id>/", approve_ferpa_form, name="approve_form"),
    
    path("return_form/<int:form_id>/", return_ferpa_form, name="return_form"),
    
    path("edit-ferpa/<int:form_id>/", views.edit_ferpa_form, name="edit_ferpa_form"),
]
