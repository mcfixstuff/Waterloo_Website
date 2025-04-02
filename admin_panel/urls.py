from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("login/", views.show_login_page, name="login"),
    path("login/microsoft/", views.trigger_microsoft_login, name="trigger_microsoft_login"),
    path("auth/callback/", views.login_view, name="login_view"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard & User Management
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("toggle-user/<int:user_id>/", views.toggle_user_status, name="toggle_user_status"),
    path("change-role/<int:user_id>/", views.change_user_role, name="change_user_role"),

    # Applications & Approvals
    path("Applications/", views.Applications, name="Applications"),
    path("ApplicationApprovals/", views.ApplicationApprovals, name="ApplicationApprovals"),

    # Form Handling
    path("select-form/", views.select_form_type, name="select_form_type"),
    path("upload-signature/", views.upload_signature, name="upload_signature"),
    path("save-ferpa-form/", views.save_ferpa_form, name="save_ferpa_form"),
    path("save-texas-affidavit-form/", views.save_texas_affidavit_form, name="save_texas_affidavit_form"),

    # Edit Forms
    path("edit_ferpa_form/<int:app_id>/", views.edit_ferpa_form, name="edit_ferpa_form"),
    path("edit_texas_residency/<int:app_id>/", views.edit_texas_residency, name="edit_texas_residency"),

    # Review / Actions
    path("approve_form/<int:app_id>/", views.approve_form, name="approve_form"),
    path("return_form/<int:app_id>/", views.return_form, name="return_form"),
    path("preview_application/<int:app_id>/", views.preview_application, name="preview_application"),

    # PDF Generation (LaTeX-powered)
    path("application/<int:app_id>/pdf/", views.generate_pdf, name="generate_pdf"),

]
