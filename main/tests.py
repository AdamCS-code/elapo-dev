from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Customer, Worker, Admin  # Sesuaikan dengan model kamu
from django.contrib.messages import get_messages

class MainViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.password = 'Monyet@1234()'

        self.user = User.objects.create_user(username='testuser', email='test@example.com', password=self.password)

        self.customer_user = User.objects.create_user(username='customeruser', password=self.password)
        self.customer = Customer.objects.create(user=self.customer_user)
        
        self.worker_user = User.objects.create_user(username='workeruser', password=self.password)
        self.worker = Worker.objects.create(user=self.worker_user)

        self.admin_user = User.objects.create_user(username='adminuser', password=self.password)
        self.admin = Admin.objects.create(user=self.admin_user)

    def test_show_main_page_as_customer(self):
        self.client.login(username='customeruser', password=self.password)
        response = self.client.get(reverse('main:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is_customer')

    def test_show_main_page_as_worker(self):
        self.client.login(username='workeruser', password=self.password)
        response = self.client.get(reverse('main:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is_worker')

    def test_show_main_page_as_admin(self):
        self.client.login(username='adminuser', password=self.password)
        response = self.client.get(reverse('main:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is_admin')

    def test_login_successful(self):
        response = self.client.post(reverse('main:login'), {
            'username': 'testuser',
            'password': self.password
        }, follow=True)
        self.assertRedirects(response, reverse('main:home'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("berhasil login" in str(m) for m in messages))

    def test_login_failure(self):
        response = self.client.post(reverse('main:login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        }, follow=True)
        self.assertContains(response, 'Email atau password salah')

    def test_customer_register(self):
        response = self.client.post(reverse('main:register_customer'), {
            'username': 'newcust',
            'email': 'newcust@example.com',
            'password1': 'passcust1234',
            'password2': 'passcust1234'
        }, follow=True)
        self.assertRedirects(response, reverse('main:login'))
        self.assertTrue(User.objects.filter(username='newcust').exists())

    def test_worker_register(self):
        response = self.client.post(reverse('main:register_worker'), {
            'username': 'newworker',
            'email': 'newworker@example.com',
            'password1': 'passworker1234',
            'password2': 'passworker1234'
        }, follow=True)
        self.assertRedirects(response, reverse('main:login'))
        self.assertTrue(User.objects.filter(username='newworker').exists())

    def test_logout(self):
        self.client.login(username='testuser', password=self.password)
        response = self.client.get(reverse('main:logout'), follow=True)
        self.assertRedirects(response, reverse('main:home'))
        self.assertFalse('_auth_user_id' in self.client.session)

