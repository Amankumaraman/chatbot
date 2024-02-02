# chatwithpdf/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Include Django authentication views
    path('', include('chatwithpdf.urls')),
]
