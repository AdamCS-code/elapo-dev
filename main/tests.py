import itertools
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch
from main.forms import LoginForm
from main.models import Customer, Worker
from django.contrib.messages import get_messages
from django.contrib.auth.models import Group
import html

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

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_rate_limiting_on_failed_logins(self, mock_recaptcha):
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

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_login_with_invalid_email_format(self, mock_recaptcha):
        """Test login with malformed email addresses"""
        invalid_emails = [
            'testuser',
            'test@user',
            'testuser@.com',
            '@testuser.com',
            'test user@email.com',
            '<script>alert("XSS")</script>@testuser.com',
            'attacker@example.com\nBCC: victim@example.com'
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                form = LoginForm(data={
                    'username': email,
                    'password': 'testpass123',
                    'g-recaptcha-response': 'test',
                })
                self.assertFalse(form.is_valid())
                self.assertIn('username', form.errors)
                self.assertEqual(form.errors['username'][0], "Enter a valid email address.")


class ClientSideRegistrationTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name='Customer')
        Group.objects.get_or_create(name="Worker")

    def tearDown(self):
        self.client = Client()
        cache.clear()


    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_registration_success(self, mock_recaptcha):
        mock_recaptcha.return_value = True
        
        # Define the common data for registration
        data = {
            'first_name': 'John', 
            'last_name': 'Doe', 
            'email': 'johndoe@example.com',  
            'nomor_hp': '081234567890',
            'domicile': 'jaksel',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
            'g-recaptcha-response': 'test',
        }
        
        user_types = {
            'customer': 'Customer berhasil ditambahkan, silahkan login ya',
            'worker': 'Worker berhasil ditambahkan, silahkan login ya'
        }

        for user_type, success_message in user_types.items():
            with self.subTest(user_type=user_type):
                if user_type == 'customer':
                    data['email'] = 'johndoe@example.com'
                    register_url = reverse('main:customer_register')
                else:
                    data['email'] = 'janedoe@example.com'
                    register_url = reverse('main:worker_register')

                # Send the POST request for registration
                response = self.client.post(register_url, data)
                
                # Check if redirection occurs to login page
                self.assertRedirects(response, reverse('main:login'))
                
                # Check if the user is created in the correct model
                if user_type == 'customer':
                    self.assertTrue(Customer.objects.filter(user__email=data['email']).exists())
                else:
                    self.assertTrue(Worker.objects.filter(user__email=data['email']).exists())

                # Check for the success message in the response
                messages = [msg.message for msg in get_messages(response.wsgi_request)]
                self.assertIn(success_message, messages)

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_empty_input_registration_validation(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        required_field = ['first_name', 'last_name', 'email', 'nomor_hp', 'domicile', 'password1', 'password2']

        user_types = ['customer', 'worker'] 

        for user_type in user_types:
            with self.subTest(user_type=user_type):
                register_url = reverse(f'main:{user_type}_register')

                for field in required_field:
                    with self.subTest(field=field):
                        data = {
                            field: '',
                            'g-recaptcha-response': 'passed',
                        }
                        response = self.client.post(register_url, data)

                        # Retrieve the form from the response context
                        form = response.context['form']
                        
                        # Ensure that the form has an error for the required field
                        self.assertTrue(form.errors.get(field))
                        self.assertIn('This field is required.', form.errors[field])

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_invalid_phone_registration_validation(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        user_types = ['customer', 'worker']

        invalid_phone_data = {
            '': 'This field is required.',                    # Empty phone number
            '12345': 'Phone number must be 8-16 digits',       # Too short (less than 8 digits)
            '12345678901234567': 'Phone number must be 8-16 digits',  # Too long (more than 16 digits)
            'abcdefgh': 'Phone number must be 8-16 digits',          # Non-numeric characters
            '+123': 'Phone number must be 8-16 digits',        # Too short for international phone
            '+12345678901234567890': 'Phone number must be 8-16 digits',  # Too long for international phone
        }

        for user_type in user_types:
            with self.subTest(user_type=user_type):
                register_url = reverse(f'main:{user_type}_register')
                
                for phone, expected_error_msg in invalid_phone_data.items():
                    with self.subTest(phone=phone):
                        data = {
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'email': 'john@example.com', 
                            'nomor_hp': phone,
                            'domicile': 'jaksel',
                            'password1': 'TestPassword123',
                            'password2': 'TestPassword123',
                            'g-recaptcha-response': 'test',
                        }

                        response = self.client.post(register_url, data)
                        
                        # Retrieve the form from the response context
                        form = response.context['form']
                        
                        # Ensure the form has an error for 'nomor_hp' and that the error matches the expected message
                        self.assertFalse(form.is_valid())
                        self.assertIn('nomor_hp', form.errors)
                        self.assertEqual(form.errors['nomor_hp'][0], expected_error_msg)

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_invalid_email_registration_validation(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        user_types = ['customer', 'worker']

        invalid_email_data = {
            '': 'This field is required.',                   # Empty email
            'johngmail.com': 'Enter a valid email address.',  # Missing '@'
            'john@.com': 'Enter a valid email address.',  # Missing domain
            'john@.com': 'Enter a valid email address.',      # Domain name missing
            '@gmail.com': 'Enter a valid email address.',  # Missing user name
            'a' * 256 + '@example.com': 'Email cannot exceed 255 characters',  # Exceeds 255 characters
        }

        for user_type in user_types:
            with self.subTest(user_type=user_type):
                register_url = reverse(f'main:{user_type}_register')
                
                for email, expected_error_msg in invalid_email_data.items():
                    with self.subTest(email=email):
                        data = {
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'email': email, 
                            'nomor_hp': '081234567890',
                            'domicile': 'jaksel',
                            'password1': 'TestPassword123',
                            'password2': 'TestPassword123',
                            'g-recaptcha-response': 'test',
                        }

                        response = self.client.post(register_url, data)
                        
                        # Retrieve the form from the response context
                        form = response.context['form']
                        
                        # Ensure the form has an error for 'email' and that the error matches the expected message
                        self.assertFalse(form.is_valid())
                        self.assertIn('email', form.errors)
                        self.assertEqual(form.errors['email'][0], expected_error_msg)

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_sanitize_registration(self, mock_recaptcha):
        print("TEST SANITIZE REGISTRATION")
        mock_recaptcha.return_value = True

        test_cases = [
            ("' OR 1=1 --", html.escape("' OR 1=1 --")),  # SQL Injection
            ("<script>alert('XSS')</script>", html.escape("<script>alert('XSS')</script>")),  # XSS
        ]

        for user_type in ['customer', 'worker']:
            register_url = reverse(f'main:{user_type}_register')

            for i, (raw_input, expected_sanitized) in enumerate(test_cases):
                with self.subTest(user_type=user_type, input=raw_input):
                    data = {
                        'first_name': raw_input,
                        'last_name': 'ValidLastName',
                        'email': f'test{i}{user_type}@example.com',
                        'nomor_hp': '081234567890',
                        'domicile': 'jaksel',
                        'password1': 'ValidPassword123!',
                        'password2': 'ValidPassword123!',
                        'g-recaptcha-response': 'test',
                    }

                    response = self.client.post(register_url, data)

                    self.assertEqual(response.status_code, 302)

                    if user_type == 'customer':
                        user = Customer.objects.get(email=data['email'])
                    else:
                        user = Worker.objects.get(email=data['email'])

                    self.assertEqual(user.first_name, expected_sanitized,)

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_registration_password_mismatch(self, mock_recaptcha):
        print("TEST PASSWORD MISMATCH")
        mock_recaptcha.return_value = True

        for user_type in ['customer', 'worker']:
            register_url = reverse(f'main:{user_type}_register')

            with self.subTest(user_type=user_type):
                data = {
                    'first_name': 'ValidFirstName',
                    'last_name': 'ValidLastName',
                    'email': f'testpasswordmismatch{user_type}@example.com',
                    'nomor_hp': '081234567890',
                    'domicile': 'jaksel',
                    'password1': 'Password',
                    'password2': 'DifferentPassword', 
                    'g-recaptcha-response': 'test',
                }

                response = self.client.post(register_url, data)

                self.assertNotEqual(response.status_code, 302)
                self.assertEqual(response.status_code, 200)

                form = response.context.get('form')
                self.assertIsNotNone(form)
                self.assertIn('password2', form.errors)

                if user_type == 'customer':
                    self.assertFalse(Customer.objects.filter(email=data['email']).exists())
                else:
                    self.assertFalse(Worker.objects.filter(email=data['email']).exists())
