from django.urls import path
from .views import download_report, index, login_view, logout_view, register_view

urlpatterns = [
    path("", index, name="index"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("reports/<int:report_id>/download/", download_report, name="download_report"),
]
