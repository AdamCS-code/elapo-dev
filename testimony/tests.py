from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from testimony.models import Testimony
from product.models import Product
from testimony.forms import TestimonyForm
import uuid
from django.contrib.messages import get_messages


class TestimonyViewsTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='12345')
        self.user2 = User.objects.create_user(username='testuser2', password='12345')
        
        # Create test products
        self.product1 = Product.objects.create(
            id=uuid.uuid4(),
            product_name="Test Product 1",
            price=50000,
            description="Test description",
            stock=10
        )
        
        # Create test testimonies
        self.testimony1 = Testimony.objects.create(
            testimony_id=uuid.uuid4(),
            user=self.user1,
            product=self.product1,
            message="This is a great product!",
            rating=5
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_create_testimony_get(self):
        """Test that the create testimony page loads correctly"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:create_testimony', args=[str(self.product1.pk)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_testimoni.html')
        self.assertIsInstance(response.context['form'], TestimonyForm)
    
    def test_create_testimony_post_success(self):
        """Test successful testimony creation"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:create_testimony', args=[str(self.product1.pk)])
        
        data = {
            'message': 'This is a test testimony',
            'rating': 4
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if testimony was created
        self.assertEqual(Testimony.objects.count(), 2)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Testimoni berhasil dikirim!")
    
    def test_create_testimony_post_invalid_form(self):
        """Test testimony creation with invalid form data"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:create_testimony', args=[str(self.product1.pk)])
        
        # Missing required rating field
        data = {
            'message': 'This is an invalid testimony'
        }
        
        response = self.client.post(url, data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        
        # No new testimony should be created
        self.assertEqual(Testimony.objects.count(), 1)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Terjadi kesalahan dalam pengisian formulir.")
    
    def test_create_testimony_xss_sanitization(self):
        """Test that XSS input is properly sanitized"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:create_testimony', args=[str(self.product1.pk)])
        
        xss_script = '<script>alert("XSS")</script>'
        data = {
            'message': xss_script,
            'rating': 3
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Verify sanitization worked
        new_testimony = Testimony.objects.latest('created_at')
        self.assertNotEqual(new_testimony.message, xss_script)
        self.assertEqual(new_testimony.message, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')
    
    def test_edit_testimony_get(self):
        """Test that the edit testimony page loads correctly"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:edit_testimony', args=[str(self.testimony1.pk)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_testimoni.html')
        self.assertIsInstance(response.context['form'], TestimonyForm)
    
    def test_edit_testimony_post_success(self):
        """Test successful testimony editing"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:edit_testimony', args=[str(self.testimony1.pk)])
        
        updated_message = 'Updated testimony message'
        data = {
            'message': updated_message,
            'rating': 4
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if testimony was updated
        updated_testimony = Testimony.objects.get(pk=self.testimony1.pk)
        self.assertEqual(updated_testimony.rating, 4)
        self.assertEqual(updated_testimony.message, updated_message)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Testimoni berhasil diperbarui!")
    
    def test_edit_testimony_unauthorized_user(self):
        """Test testimony editing by unauthorized user"""
        # Login as user2 (who did not create the testimony)
        self.client.login(username='testuser2', password='12345')
        url = reverse('testimony:edit_testimony', args=[str(self.testimony1.pk)])
        
        response = self.client.get(url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Anda tidak memiliki izin untuk mengedit testimoni ini.")
    
    def test_delete_testimony_success(self):
        """Test successful testimony deletion"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('testimony:delete_testimony', args=[str(self.testimony1.pk)])
        
        response = self.client.post(url)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if testimony was deleted
        self.assertEqual(Testimony.objects.count(), 0)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Testimoni berhasil dihapus.")
    
    def test_delete_testimony_unauthorized_user(self):
        """Test testimony deletion by unauthorized user"""
        # Login as user2 (who did not create the testimony)
        self.client.login(username='testuser2', password='12345')
        url = reverse('testimony:delete_testimony', args=[str(self.testimony1.pk)])
        
        response = self.client.post(url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Testimony should still exist
        self.assertEqual(Testimony.objects.count(), 1)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Anda tidak memiliki izin untuk menghapus testimoni ini.")
    
    def test_get_testimony_for_customer(self):
        """Test getting testimonies for a customer"""
        # Mock the get_user_role function to return 'Customer'
        with self.settings(TEST_GET_USER_ROLE='Customer'):
            # Patch the get_user_role function
            from unittest.mock import patch
            with patch('testimony.views.get_user_role', return_value='Customer'):
                self.client.login(username='testuser1', password='12345')
                url = reverse('testimony:my_testimony')
                
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'user_testimoni.html')
                self.assertTrue(response.context['is_customer'])
                self.assertEqual(len(response.context['testimoni']), 1)
    
    def test_get_testimony_for_non_customer(self):
        """Test getting testimonies for a non-customer user"""
        # Mock the get_user_role function to return 'Staff'
        with self.settings(TEST_GET_USER_ROLE='Staff'):
            # Patch the get_user_role function
            from unittest.mock import patch
            with patch('testimony.views.get_user_role', return_value='Staff'):
                self.client.login(username='testuser1', password='12345')
                url = reverse('testimony:my_testimony')
                
                response = self.client.get(url)
                
                # Should return JsonResponse
                self.assertEqual(response.status_code, 200)
                self.assertJSONEqual(
                    str(response.content, encoding='utf8'),
                    {'message': 'Anda tidak bisa melihat testimoni karena bukan customer.'}
                )

    def test_sql_injection_in_product_id(self):
        """Test SQL injection in product_id parameter during testimony creation"""
        # Attempt simple SQL Injection in URL
        response = self.client.get(f'/testimony/create/1 OR 1=1')
        # URL resolver should reject it
        self.assertEqual(response.status_code, 404)

    def test_csrf_protection_on_create_testimony(self):
        """Test CSRF protection on create testimony POST"""
        client = Client(enforce_csrf_checks=True)
        client.login(username='customer', password='password123')
        
        url = reverse('testimony:create_testimony', kwargs={'product_id': self.product1.id})
        # POST tanpa CSRF token
        response = client.post(url, data={'message': 'Test CSRF attack'})
        self.assertEqual(response.status_code, 403)

    def test_ssrf_attempt_by_header_manipulation(self):
        """Test SSRF attempt by manipulating headers on viewing testimonies"""
        url = reverse('testimony:my_testimony')
        response = self.client.get(
            url,
            HTTP_HOST='evil-site.com',
            HTTP_REFERER='http://evil-site.com'
        )
    
        self.assertEqual(response.status_code, 400)

