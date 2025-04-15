from django.urls import path
from . import views

urlpatterns = [
    path('new/special-circumstance/', views.new_special_circumstance_form, name='new_special_circumstance_form'),
    path('new/course-drop/', views.new_course_drop_form, name='new_course_drop_form'),
    path('view/<int:form_id>/', views.view_form, name='view_form'),
    path('edit/<int:form_id>/', views.edit_form, name='edit_form'),
    path('delete/<int:form_id>/', views.delete_form, name='delete_form'),

    # New URL patterns for approve and return
    path('approve/<int:form_id>/', views.approve_form, name='approve_form_api'),
    path('return/<int:form_id>/', views.return_form, name='return_form_api'),
    
        # New URL pattern for PDF generation
    path('pdf/<int:form_id>/', views.generate_form_pdf, name='generate_form_pdf'),
    
]