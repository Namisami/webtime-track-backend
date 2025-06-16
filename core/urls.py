from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.decorators import authentication_classes, permission_classes
from users.views import custom_token_login, csrf

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('times.urls')),
    path('api/users/', include('users.urls')),
    path('api/login/', custom_token_login),
    path('api/csrf/', csrf),
    # path('api/login/', authentication_classes([])(permission_classes([])(obtain_auth_token))),
]
