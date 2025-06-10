from django.test import TestCase
from users.models import CustomUser
import json
from rest_framework.authtoken.models import Token
from .models import TimeInterval, Statistics

class CreateIntervalsTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='testuser@test.test', 
            password='testpass'
        )
        self.token = Token.objects.create(user=self.user)
        self.url = 'http://localhost:8000/api/create_intervals/' 
        
        self.valid_data = {
            'intervals': [
                {
                    'startTime': 100,
                    'endTime': 200,
                    'date': '2025-01-01',
                    'url': 'https://example.com',
                    'faviconUrl': 'https://example.com/favicon.ico',
                }
            ]
        }

    def send_request(self, data):
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

    def test_successful_creation(self):
        """Успешное создание новых интервалов"""
        response = self.send_request(self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TimeInterval.objects.count(), 1)
        self.assertEqual(response.json()['processed'], 1)
        self.assertEqual(response.json()['duplicates'], 0)

    def test_invalid_json(self):
        """Обработка невалидного JSON"""
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_field(self):
        """Отсутствие обязательного поля"""
        invalid_data = {'intervals': [{'url': 'https://example.com'}]}
        response = self.send_request(invalid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing field', response.json()['error'])

    def test_validation_error(self):
        """Ошибка валидации модели"""
        invalid_data = self.valid_data.copy()
        invalid_data['intervals'][0]['endTime'] = 50 
        response = self.send_request(invalid_data)
        self.assertEqual(response.status_code, 400)

    def test_url_truncation(self):
        """Обрезка длинных URL"""
        long_url = 'https://example.com/' + ('a' * 600)
        data = self.valid_data.copy()
        data['intervals'][0]['url'] = long_url
        
        response = self.send_request(data)
        interval = TimeInterval.objects.first()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(interval.url, 'https://example.com')

    def test_favicon_url_handling(self):
        """Обработка faviconUrl (null при длинном URL)"""
        long_favicon = 'http://example.com/' + ('a' * 600)
        data = self.valid_data.copy()
        data['intervals'][0]['faviconUrl'] = long_favicon
        
        response = self.send_request(data)
        interval = TimeInterval.objects.first()
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(interval.favicon_url)

    def test_statistics_creation(self):
        """Создание записи статистики"""
        self.send_request(self.valid_data)
        stat = Statistics.objects.first()
        
        self.assertEqual(stat.session_count, 1)
        self.assertEqual(stat.time_count, 100) 
        self.assertEqual(stat.url, 'example.com')

    def test_statistics_update(self):
        """Обновление существующей статистики"""
        # Первый интервал
        self.send_request(self.valid_data)
        
        # Второй интервал для того же URL и даты
        new_data = self.valid_data.copy()
        new_data['intervals'][0].update({
            'startTime': 300,
            'endTime': 500
        })
        self.send_request(new_data)
        
        stat = Statistics.objects.first()
        self.assertEqual(stat.session_count, 2)
        self.assertEqual(stat.time_count, 400)  

    def test_multiple_intervals(self):
        """Обработка нескольких интервалов за раз"""
        data = {
            'intervals': [
                {
                    'startTime': 100,
                    'endTime': 200,
                    'date': '2025-01-01',
                    'url': 'https://site1.com',
                },
                {
                    'startTime': 300,
                    'endTime': 400,
                    'date': '2025-01-02',
                    'url': 'https://site2.com',
                }
            ]
        }
        response = self.send_request(data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TimeInterval.objects.count(), 2)
        self.assertEqual(Statistics.objects.count(), 2)

    def test_favicon_in_statistics(self):
        """Favicon сохраняется в статистике"""
        self.send_request(self.valid_data)
        stat = Statistics.objects.first()
        self.assertEqual(
            stat.favicon_url,
            'https://example.com/favicon.ico'
        )
