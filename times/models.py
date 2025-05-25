from django.db import models
from django.db.models import Value, F, Func
from django.forms import ValidationError
from utils.ms_to_time import ms_to_time
from .validators import BrowserURLValidator
from urllib.parse import urlparse


class TimeIntervalManager(models.Manager):
    def filter_by_hostname(self, hostname):
        return self.annotate(
            url_hostname=Func(
                F('url'),
                Value(r'^(?:https?://)?([^/]+)'),
                function='SUBSTRING',
                output_field=models.CharField()
            )
        ).filter(url_hostname=hostname)


class TimeInterval(models.Model):
    url = models.CharField(max_length=500, validators=[BrowserURLValidator()], verbose_name="Ссылка")
    favicon_url = models.CharField(max_length=500, validators=[BrowserURLValidator()], verbose_name="Ссылка на иконку", null=True, blank=True)
    start_time = models.PositiveIntegerField(verbose_name="Время начала (с)")
    end_time = models.PositiveIntegerField(verbose_name="Время окончания (с)")
    date = models.DateField(verbose_name="Дата")
    
    objects = TimeIntervalManager()

    def __str__(self):
        return f"{self.url} [{self.date}]: {ms_to_time(self.start_time)}-{ms_to_time(self.end_time)}"
    
    def clean(self):
        super().clean()
        if not self.start_time:
            raise ValidationError("Время начала интервала - обязательное поле")
        if not self.end_time:
            raise ValidationError("Время конца интервала - обязательное поле")
        
        if self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': "Время окончания должно быть позже времени начала"
            })
        
    class Meta:
        verbose_name = "Интервал"
        verbose_name_plural = "Интервалы"
        ordering = ['-date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'start_time']),
        ]


class Statistics(models.Model):
    url = models.CharField(max_length=500, validators=[BrowserURLValidator()], verbose_name="Ссылка на сайт")
    favicon_url = models.CharField(max_length=500, validators=[BrowserURLValidator()], verbose_name="Ссылка на иконку", null=True, blank=True)
    session_count = models.PositiveIntegerField(default=0, verbose_name="Количество сессий")
    time_count = models.PositiveIntegerField(default=0, verbose_name="Проведенное время (с)")
    period_date = models.DateField(verbose_name="Дата периода")
    
    @property
    def intervals(self):        
        parsed_url = urlparse(self.url)
        if not parsed_url.hostname:
            parsed_url = urlparse(f"http://{self.url}")
            
        return TimeInterval.objects.filter_by_hostname(
            parsed_url.hostname
        ).filter(
            date=self.period_date
        ).order_by('-date', 'start_time')
    
    def __str__(self):
        return f"{self.url} [{self.period_date}]"
    
    class Meta:
        unique_together = ('url', 'period_date')
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['period_date']),
        ]
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"
