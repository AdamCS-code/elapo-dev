from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch

class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser@example.com',
            password='testpass123'
        )
        cls.login_url = reverse('main:login')

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_rate_limiting_on_failed_logins(self):
        login_url = reverse('main:login')
        
        for i in range(5):
            response = self.client.post(login_url, {
                'username': 'wrong@example.com',
                'password': 'wrongpassword',
                'recaptcha': 'PASSED'
            })
            self.assertContains(response, 'Email atau password salah', status_code=200)

        sixth_response = self.client.post(login_url, {
            'username': 'wrong@example.com',
            'password': 'wrongpassword',
            'recaptcha': 'PASSED'
        })
        self.assertEqual(sixth_response.status_code, 200)
        self.assertTemplateUsed(sixth_response, 'rate_limit_exceeded.html')
        self.assertContains(sixth_response, 'Too Many Requests')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_successful_login(self, mock_recaptcha):
        mock_recaptcha.return_value = True
        
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'g-recaptcha-response': 'test',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:home'))
