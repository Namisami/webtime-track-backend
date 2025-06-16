from rest_framework import viewsets, pagination, views, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, api_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from urllib.parse import urlparse
from datetime import datetime
import json
from .models import TimeInterval, Statistics
from .serializers import TimeIntervalSerializer, StatisticsSerializer

class TimeIntervalViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated] 
    queryset = TimeInterval.objects.all().order_by('-date', 'start_time')
    serializer_class = TimeIntervalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'start_time', 'end_time']
    
    pagination_class = pagination.PageNumberPagination
    pagination_class.page_size = 20
        

class StatisticsRangeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated] 
    
    def get(self, request):
        period_date_start = request.query_params.get('period_date_start')
        period_date_end = request.query_params.get('period_date_end')

        if not period_date_start or not period_date_end:
            return Response(
                {"error": "Оба параметра period_date_start и period_date_end обязательны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(period_date_start, "%Y-%m-%d").date()
            end_date = datetime.strptime(period_date_end, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:
            return Response(
                {"error": "Дата начала периода должна быть раньше или равна дате окончания"},
                status=status.HTTP_400_BAD_REQUEST
            )

        statistics = Statistics.objects.filter(
            period_date__gte=start_date,
            period_date__lte=end_date,
            user__pk=request.user.pk,
        ).order_by('-time_count')

        if not statistics.exists():
            return Response(
                {"message": "Данные за указанный период не найдены"},
                status=status.HTTP_200_OK
            )

        serializer = StatisticsSerializer(statistics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@csrf_exempt
@transaction.atomic
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_intervals(request):
    try:
        data = request.data
        
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
                favicon_url=favicon_url if favicon_url is not None and len(favicon_url) <= 500 else None,
                user=request.user,
            )
            
            interval.full_clean()
            
            check_duplicates.append({
                'url': interval.url,
                'date': interval.date,
                'start_time': interval.start_time,
                'end_time': interval.end_time,
                'favicon_url': interval.favicon_url,
                'user': interval.user,
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
                    user=item['user'],
                )
            
            existing = TimeInterval.objects.filter(q_objects).values_list(
                'url', 'date', 'start_time', 'end_time', 'user'
            )
            existing_intervals = {
                (item[0], item[1], item[2], item[3], item[4]) for item in existing
            }
            
        new_intervals = []
        for interval in intervals:
            key = (
                interval.url,
                interval.date,
                interval.start_time,
                interval.end_time,
                interval.user,
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
                url=urlparse(url).hostname,
                period_date=date,
                user=request.user,
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
