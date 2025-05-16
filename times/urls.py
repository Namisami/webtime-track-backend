from django.urls import path
from .views import create_intervals, TimeIntervalViewSet, StatisticsRangeView

time_interval_list = TimeIntervalViewSet.as_view({
    'get': 'list',
})

urlpatterns = [
    path('create_intervals/', create_intervals, name='create-intervals'),
    path('intervals/', time_interval_list, name='interval-list'),
    path('statistics/', StatisticsRangeView.as_view(), name='statistics-range'),
]
