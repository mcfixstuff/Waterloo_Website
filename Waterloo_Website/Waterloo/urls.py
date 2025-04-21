from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


##################################################################
#################### DO NOT TOUCH THIS FILE ######################
########### USE URLS.PY FILE IN ADMIN_PANEL FOLDER ###############
##################################################################


urlpatterns = [
    path("admin/", include("admin_panel.urls")),# Custom admin panel
    path('academic/', include('academic_forms.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
