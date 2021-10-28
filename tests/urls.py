from django.contrib import admin
from django.urls import path, include

import yubival.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('yubival.urls')),
]
