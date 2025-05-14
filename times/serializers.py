from rest_framework import serializers
from .models import TimeInterval

class TimeIntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeInterval
        fields = '__all__'
        extra_kwargs = {
            'url': {'required': True},
            'date': {'required': True},
            'start_time': {'required': True},
            'end_time': {'required': True}
        }
        
    def validate(self, data):
        # if (data['start_time'] is None):
        #     raise serializers.ValidationError(
        #         "Время начала является обязате"
        #     )
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError(
                "Время окончания должно быть позже времени начала"
            )
        
        if TimeInterval.objects.filter(
            date=data['date'],
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time']
        ).exists():
            raise serializers.ValidationError(
                "Временной слот пересекается с существующим"
            )
        
        return data