from django.urls import path
from .views import create_intervals

urlpatterns = [
    path('create_intervals/', create_intervals, name='create-intervals'),
]
