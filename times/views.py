# views.py
from rest_framework import viewsets, pagination
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from urllib.parse import urlparse
from .models import TimeInterval, Statistics
from .serializers import TimeIntervalSerializer
import json

class TimeIntervalViewSet(viewsets.ModelViewSet):
    queryset = TimeInterval.objects.all().order_by('-date', 'start_time')
    serializer_class = TimeIntervalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'start_time', 'end_time']
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly] 
    
    pagination_class = pagination.PageNumberPagination
    pagination_class.page_size = 20

    # def perform_create(self, serializer):
        # serializer.save()  # Можно добавить owner=self.request.user и т.д.

@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def create_intervals(request):
    try:
        data = json.loads(request.body)
        
        intervals_data = data.get('intervals', [])
        intervals = []
        check_duplicates = []
        stats_updates = {}

        for item in intervals_data:
            favicon_url = item.get('faviconUrl')
            
            interval = TimeInterval(
                start_time=item['startTime'],
                end_time=item['endTime'],
                date=item['date'],
                url=item['url'] if len(item['url']) <= 500 else '{url.scheme}://{url.netloc}'.format(url=urlparse(item["url"])),
                favicon_url=favicon_url if favicon_url and len(favicon_url) <= 500 else None,
            )
            
            interval.full_clean()
            
            check_duplicates.append({
                'url': interval.url,
                'date': interval.date,
                'start_time': interval.start_time,
                'end_time': interval.end_time,
                'favicon_url': interval.favicon_url,
            })
            
            intervals.append(interval)
            
        existing_intervals = set()
        if check_duplicates:
            q_objects = Q()
            for item in check_duplicates:
                q_objects |= Q(
                    url=item['url'],
                    date=item['date'],
                    start_time=item['start_time'],
                    end_time=item['end_time'],
                    favicon_url=item['favicon_url'],
                )
            
            existing = TimeInterval.objects.filter(q_objects).values_list(
                'url', 'date', 'start_time', 'end_time'
            )
            existing_intervals = {
                (item[0], item[1], item[2], item[3]) for item in existing
            }
            
        new_intervals = []
        for interval in intervals:
            key = (
                interval.url,
                interval.date,
                interval.start_time,
                interval.end_time
            )
            if key not in existing_intervals:
                new_intervals.append(interval)
                
                stats_key = (interval.url, interval.date)
                if stats_key not in stats_updates:
                    stats_updates[stats_key] = {
                        'session_count': 0,
                        'time_count': 0,
                        'favicon_url': interval.favicon_url
                    }
                
                stats_updates[stats_key]['session_count'] += 1
                stats_updates[stats_key]['time_count'] += interval.end_time - interval.start_time            

        for (url, date), data in stats_updates.items():
            stat, created = Statistics.objects.update_or_create(
                url=url,
                period_date=date,
                defaults={
                    'session_count': data['session_count'],
                    'time_count': data['time_count'],
                    'favicon_url': data.get('favicon_url') or Statistics.objects.filter(url=url).values_list('favicon_url', flat=True).first()
                }
            )

            if not created:
                Statistics.objects.filter(pk=stat.pk).update(
                    session_count=F('session_count') + data['session_count'],
                    time_count=F('time_count') + data['time_count']
                )

        TimeInterval.objects.bulk_create(new_intervals)
        
        return JsonResponse({
                'status': 'success', 
                'processed': len(intervals),
                'duplicates': len(intervals) - len(new_intervals),
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
