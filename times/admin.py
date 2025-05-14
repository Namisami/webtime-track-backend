from django.contrib import admin
from .models import TimeInterval, Statistics

@admin.register(TimeInterval)
class TimeIntervalAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'url')
    list_filter = ('date',)
    search_fields = ('url',)
    date_hierarchy = 'date'

admin.site.register(Statistics)
