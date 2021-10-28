from django.urls import path

from yubival import views

urlpatterns = [
    path('wsapi/2.0/verify', views.VerifyView.as_view(), name='verify'),
]
