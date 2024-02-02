# urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from .views import index, ask, upload_pdf, download_csv, ask_page, upload_page, download_csv_page, AskPageView, SignupView

urlpatterns = [
    path('', LoginView.as_view(template_name='login.html'), name='login'),
    path('index/', index, name='index'),
    path('ask/', AskPageView.as_view(), name='ask_page'),
    path('api/ask/', ask, name='ask'),
    path('upload/', upload_page, name='upload_page'),
    path('api/admin/upload/', upload_pdf, name='upload_pdf'),
    path('download-csv/', download_csv_page, name='download_csv_page'),
    path('api/admin/download-csv/', download_csv, name='download_csv'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),
]
