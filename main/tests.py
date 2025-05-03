import itertools
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch
from main.forms import AdminEditForm, AdminRegistrationForm, LoginForm, WorkerEditForm
from main.models import Admin, Customer, Worker
from django.contrib.messages import get_messages
from django.contrib.auth.models import Group
import html
from django.contrib.auth import get_user_model


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


    
class AdminRegistrationTests(TestCase):
    def test_successful_admin_creation(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'newadmin@example.com',
            'nomor_hp': '081234567890',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        form = AdminRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())


    def test_input_sanitization(self):
        form_data = {
            'first_name': '<script>alert("XSS")</script>',
            'last_name': 'admin',
            'email': 'validadmin@example.com',
            'nomor_hp': '+62-856-7745-9090',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }

        form = AdminRegistrationForm(data=form_data)

        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())
        
        self.assertEqual(form.cleaned_data['first_name'], html.escape('<script>alert("XSS")</script>'))
        self.assertEqual(form.cleaned_data['nomor_hp'], '6285677459090') 

    def test_password_mismatch(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'otheradmin@example.com',
            'nomor_hp': '081234567890',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
        }
        
        form = AdminRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['password2'][0], "The two password fields didn’t match.")



class EditWorkerProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test user - with username if required
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser@example.com',  # Add this if your model requires username
            email='testuser@example.com', 
            password='password123'
        )
        
        # Create Worker instance
        self.worker = Worker.objects.create(
            user=self.user,
            first_name="TestWorkerFirstName",
            last_name="TestWorkerLastName",
            nomor_hp="081234567890",
            email="testworker@example.com"
        )
        
        # Test data
        self.worker_data = {
            'first_name': 'UpdatedFirstName',
            'last_name': 'UpdatedLastName',
            'nomor_hp': '089876543210',
            'domicile': 'jaksel'
        }

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_worker_edit_form_valid(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        # Perform login with captcha field
        login_url = reverse('main:login')
        login_response = self.client.post(login_url, {
            'username': 'testuser@example.com',
            'password': 'password123',
            'g-recaptcha-response': 'test',
        })
        self.assertEqual(login_response.status_code, 302)  


        edit_url = reverse('main:edit_profile_worker')  
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(edit_url, self.worker_data)
        self.assertEqual(response.status_code, 302)
        
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.first_name, 'UpdatedFirstName')
        self.assertEqual(self.worker.nomor_hp, '089876543210')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_worker_invalid_phone_number(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_worker')
        
        # Invalid phone number (too short)
        invalid_data = self.worker_data.copy()
        invalid_data['nomor_hp'] = '123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')  

        # Invalid phone number (too long)
        invalid_data['nomor_hp'] = '12345678901234567890'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_worker_invalid_names(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_worker')

        # Invalid first name (contains number)
        invalid_data = self.worker_data.copy()
        invalid_data['first_name'] = 'John123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertEqual(form.errors.get("first_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        # Invalid last name (contains special characters/code)
        invalid_data = self.worker_data.copy()
        invalid_data['last_name'] = '<script>alert("XSS")</script>'  # XSS payload

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200) 

        form = response.context['form']
        self.assertEqual(form.errors.get("last_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")



class EditCustomerProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test user - with username if required
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser@example.com',  # Add this if your model requires username
            email='testuser@example.com', 
            password='password123'
        )
        
        # Create Customer instance
        self.customer = Customer.objects.create(
            user=self.user,
            first_name="TestCustFirstName",
            last_name="TestCustLastName",
            nomor_hp="081234567890",
            email="testcust@example.com"
        )
        
        # Test data
        self.customer_data = {
            'first_name': 'UpdatedFirstName',
            'last_name': 'UpdatedLastName',
            'nomor_hp': '089876543210',
            'domicile': 'jakut'
        }

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_cust_edit_form_valid(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        # Perform login with captcha field
        login_url = reverse('main:login')
        login_response = self.client.post(login_url, {
            'username': 'testuser@example.com',
            'password': 'password123',
            'g-recaptcha-response': 'test',
        })
        self.assertEqual(login_response.status_code, 302)  


        edit_url = reverse('main:edit_profile_customer')  
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(edit_url, self.cust_data)
        self.assertEqual(response.status_code, 302)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, 'UpdatedFirstName')
        self.assertEqual(self.customer.nomor_hp, '089876543210')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_cust_invalid_phone_number(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_customer')
        
        # Invalid phone number (too short)
        invalid_data = self.customer_data.copy()
        invalid_data['nomor_hp'] = '123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')  

        # Invalid phone number (too long)
        invalid_data['nomor_hp'] = '12345678901234567890'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_customer_invalid_names(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_customer')

        # Invalid first name (contains number)
        invalid_data = self.customer_data.copy()
        invalid_data['first_name'] = 'John123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertEqual(form.errors.get("first_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        # Invalid last name (contains special characters/code)
        invalid_data = self.customer_data.copy()
        invalid_data['last_name'] = '<script>alert("XSS")</script>'  # XSS payload

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200) 

        form = response.context['form']
        self.assertEqual(form.errors.get("last_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")




    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_customer_edit_form_valid(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        # Perform login with captcha field
        login_url = reverse('main:login')
        login_response = self.client.post(login_url, {
            'username': 'testuser@example.com',
            'password': 'password123',
            'g-recaptcha-response': 'test',
        })
        self.assertEqual(login_response.status_code, 302)  


        edit_url = reverse('main:edit_profile_customer')  
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(edit_url, self.customer_data)
        self.assertEqual(response.status_code, 302)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, 'UpdatedFirstName')
        self.assertEqual(self.customer.nomor_hp, '089876543210')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_customer_invalid_phone_number(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_customer')
        
        # Invalid phone number (too short)
        invalid_data = self.customer_data.copy()
        invalid_data['nomor_hp'] = '123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')  

        # Invalid phone number (too long)
        invalid_data['nomor_hp'] = '12345678901234567890'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_customer_invalid_names(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_customer')

        # Invalid first name (contains number)
        invalid_data = self.customer_data.copy()
        invalid_data['first_name'] = 'John123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertEqual(form.errors.get("first_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        # Invalid last name (contains special characters/code)
        invalid_data = self.customer_data.copy()
        invalid_data['last_name'] = '<script>alert("XSS")</script>'  # XSS payload

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200) 

        form = response.context['form']
        self.assertEqual(form.errors.get("last_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")




class EditAdminProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test user - with username if required
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser@example.com',  # Add this if your model requires username
            email='testuser@example.com', 
            password='password123'
        )
        
        # Create Admin instance
        self.admin = Admin.objects.create(
            user=self.user,
            first_name="TestCustFirstName",
            last_name="TestCustLastName",
            nomor_hp="081234567890",
            email="testcust@example.com"
        )
        
        # Test data
        self.admin_data = {
            'first_name': 'UpdatedFirstName',
            'last_name': 'UpdatedLastName',
            'nomor_hp': '089876543210',
        }

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_admin_edit_form_valid(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        # Perform login with captcha field
        login_url = reverse('main:login')
        login_response = self.client.post(login_url, {
            'username': 'testuser@example.com',
            'password': 'password123',
            'g-recaptcha-response': 'test',
        })
        self.assertEqual(login_response.status_code, 302)  


        edit_url = reverse('main:edit_profile_admin')  
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(edit_url, self.admin_data)
        self.assertEqual(response.status_code, 302)
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'UpdatedFirstName')
        self.assertEqual(self.admin.nomor_hp, '089876543210')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_admin_invalid_phone_number(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_admin')
        
        # Invalid phone number (too short)
        invalid_data = self.admin_data.copy()
        invalid_data['nomor_hp'] = '123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')  

        # Invalid phone number (too long)
        invalid_data['nomor_hp'] = '12345678901234567890'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_admin_invalid_names(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_admin')

        # Invalid first name (contains number)
        invalid_data = self.admin_data.copy()
        invalid_data['first_name'] = 'John123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertEqual(form.errors.get("first_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        # Invalid last name (contains special characters/code)
        invalid_data = self.admin_data.copy()
        invalid_data['last_name'] = '<script>alert("XSS")</script>'  # XSS payload

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200) 

        form = response.context['form']
        self.assertEqual(form.errors.get("last_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")




    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_admin_edit_form_valid(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        # Perform login with captcha field
        login_url = reverse('main:login')
        login_response = self.client.post(login_url, {
            'username': 'testuser@example.com',
            'password': 'password123',
            'g-recaptcha-response': 'test',
        })
        self.assertEqual(login_response.status_code, 302)  


        edit_url = reverse('main:edit_profile_admin')  
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(edit_url, self.admin_data)
        self.assertEqual(response.status_code, 302)
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'UpdatedFirstName')
        self.assertEqual(self.admin.nomor_hp, '089876543210')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_admin_invalid_phone_number(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_admin')
        
        # Invalid phone number (too short)
        invalid_data = self.admin_data.copy()
        invalid_data['nomor_hp'] = '123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')  

        # Invalid phone number (too long)
        invalid_data['nomor_hp'] = '12345678901234567890'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form'] 
        self.assertFormError(form, 'nomor_hp', 'Phone number must be 8-16 digits')

    @patch('django_recaptcha.fields.ReCaptchaField.validate')
    def test_edit_profile_admin_invalid_names(self, mock_recaptcha):
        mock_recaptcha.return_value = True

        self.client.login(username='testuser@example.com', password='password123')

        edit_url = reverse('main:edit_profile_admin')

        # Invalid first name (contains number)
        invalid_data = self.admin_data.copy()
        invalid_data['first_name'] = 'John123'

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertEqual(form.errors.get("first_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        # Invalid last name (contains special characters/code)
        invalid_data = self.admin_data.copy()
        invalid_data['last_name'] = '<script>alert("XSS")</script>'  # XSS payload

        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200) 

        form = response.context['form']
        self.assertEqual(form.errors.get("last_name")[0], "Only letters, spaces, hyphens, apostrophes and periods allowed")
