from django.db import models
from django.forms import ValidationError
from utils.ms_to_time import ms_to_time

class TimeInterval(models.Model):
    url = models.URLField(max_length=500, verbose_name="Ссылка")
    start_time = models.PositiveIntegerField(verbose_name="Время начала (мс)")
    end_time = models.PositiveIntegerField(verbose_name="Время окончания (мс)")
    date = models.DateField(verbose_name="Дата")

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
    url = models.URLField(max_length=500, verbose_name="Ссылка на сайт")
    favicon_url = models.URLField(max_length=500, verbose_name="Ссылка на иконку", null=True, blank=True)
    session_count = models.PositiveIntegerField(default=0, verbose_name="Количество сессий")
    time_count = models.PositiveIntegerField(default=0, verbose_name="Проведенное время (мс)")
    period_date = models.DateField(verbose_name="Дата периода")
    
    @property
    def intervals(self):
        return TimeInterval.objects.filter(
            url=self.url,
            date=self.period_date,
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
    