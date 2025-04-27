from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from order.models import Order, OrderStatus
from review.models import FraudReport, Review
from review.forms import FraudReportForm, ReviewForm
import uuid
from django.contrib.messages import get_messages
from cart.models import Cart
from main.models import Customer
from main.models import Worker

class FraudReportViewsTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='12345')
        self.user2 = User.objects.create_user(username='testuser2', password='12345')
        self.worker1 = User.objects.create_user(username='testworker1', password='12345')

        self.customer1 = Customer.objects.create(
            user = self.user1,
        )

        self.worker1 = Worker.objects.create(
            user = self.worker1
        )

        # Create order status objects
        self.status_completed = OrderStatus.objects.create(status='COMPLETED')
        self.status_reviewed = OrderStatus.objects.create(status='reviewed')

        self.cart1 = Cart.objects.create(
            id=uuid.uuid4(),
            customer=self.customer1,
            is_checked_out=True
        )
        
        # Create test orders
        self.order1 = Order.objects.create(
            id=uuid.uuid4(),
            cart=self.cart1,
            total=15,
            status=self.status_completed,
            worker=self.worker1,
            delivery_fee=5000
        )
        
        # Create test fraud report
        self.report1 = FraudReport.objects.create(
            report_id=uuid.uuid4(),
            user=self.user1,
            order=self.order1,
            description="This is a test fraud report"
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_create_fraud_report_get(self):
        """Test that the create fraud report page loads correctly"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:report_fraud', args=[str(self.order1.pk)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_report.html')
        self.assertIsInstance(response.context['form'], FraudReportForm)
    
    def test_create_fraud_report_post_success(self):
        """Test successful fraud report creation"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:report_fraud', args=[str(self.order1.pk)])
        
        data = {
            'description': 'This is a test fraud report submission'
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to order detail page
        self.assertRedirects(response, reverse('order:order_detail', args=[str(self.order1.pk)]))
        
        # Check if report was created
        self.assertEqual(FraudReport.objects.count(), 2)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Fraud Report berhasil dikirim!")
    
    def test_create_fraud_report_post_invalid_form(self):
        """Test fraud report creation with invalid form data"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:report_fraud', args=[str(self.order1.pk)])
        
        # Empty form data
        data = {}
        
        response = self.client.post(url, data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        
        # No new report should be created
        self.assertEqual(FraudReport.objects.count(), 1)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Terjadi kesalahan dalam pengisian formulir.")
    
    def test_create_fraud_report_xss_sanitization(self):
        """Test that XSS input is properly sanitized"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:report_fraud', args=[str(self.order1.pk)])
        
        xss_script = '<script>alert("XSS")</script>'
        data = {
            'description': xss_script
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to order detail page
        self.assertRedirects(response, reverse('order:order_detail', args=[str(self.order1.pk)]))
        
        # Verify sanitization worked
        new_report = FraudReport.objects.exclude(pk=self.report1.pk).first()
        self.assertNotEqual(new_report.description, xss_script)
        self.assertEqual(new_report.description, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')
    
    def test_update_fraud_report_get(self):
        """Test that the edit fraud report page loads correctly"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:update_report', args=[str(self.report1.pk)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_report.html')
        self.assertIsInstance(response.context['form'], FraudReportForm)
        self.assertEqual(response.context['report'], self.report1)
    
    def test_update_fraud_report_post_success(self):
        """Test successful fraud report updating"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:update_report', args=[str(self.report1.pk)])
        
        updated_description = 'Updated fraud report description'
        data = {
            'description': updated_description
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if report was updated
        updated_report = FraudReport.objects.get(pk=self.report1.pk)
        self.assertEqual(updated_report.description, updated_description)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Report berhasil diperbarui!")
    
    def test_update_fraud_report_unauthorized_user(self):
        """Test fraud report editing by unauthorized user"""
        # Login as user2 (who did not create the report)
        self.client.login(username='testuser2', password='12345')
        url = reverse('review:update_report', args=[str(self.report1.pk)])
        
        response = self.client.get(url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Anda tidak memiliki izin untuk mengedit report ini.")
    
    def test_update_fraud_report_post_invalid_form(self):
        """Test fraud report updating with invalid form data"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:update_report', args=[str(self.report1.pk)])
        
        # Empty form data (assuming description is required)
        data = {'description': ''}
        
        response = self.client.post(url, data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        
        # Report should not be updated
        unchanged_report = FraudReport.objects.get(pk=self.report1.pk)
        self.assertEqual(unchanged_report.description, "This is a test fraud report")
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Terjadi kesalahan dalam pengisian formulir.")
    
    def test_delete_fraud_report_success(self):
        """Test successful fraud report deletion"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:delete_report', args=[str(self.report1.pk)])
        
        response = self.client.post(url)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if report was deleted
        self.assertEqual(FraudReport.objects.count(), 0)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Report berhasil dihapus.")
    
    def test_get_report_for_customer(self):
        """Test getting fraud reports for a customer"""
        # Mock the get_user_role function to return 'Customer'
        from unittest.mock import patch
        with patch('review.views.get_user_role', return_value='Customer'):
            self.client.login(username='testuser1', password='12345')
            url = reverse('review:my_report')
            
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'user_report.html')
            self.assertTrue(response.context['is_customer'])
            self.assertEqual(len(response.context['reports']), 1)
    
    def test_get_report_for_non_customer(self):
        """Test getting fraud reports for a non-customer user"""
        # Mock the get_user_role function to return 'Staff'
        from unittest.mock import patch
        with patch('review.views.get_user_role', return_value='Staff'):
            self.client.login(username='testuser1', password='12345')
            url = reverse('review:my_report')
            
            response = self.client.get(url)
            
            # Should return JsonResponse
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(
                str(response.content, encoding='utf8'),
                {'message': 'hmm you cannot see this, your not customer'}
            )
    
    def test_delete_nonexistent_report(self):
        """Test deleting a nonexistent fraud report"""
        self.client.login(username='testuser1', password='12345')
        
        # Create a random UUID that doesn't exist in the database
        fake_uuid = uuid.uuid4()
        while FraudReport.objects.filter(pk=fake_uuid).exists():
            fake_uuid = uuid.uuid4()
            
        url = reverse('review:delete_report', args=[str(fake_uuid)])
        
        # This should raise a 404 Not Found
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sql_injection_in_order_id(self):
        """Test SQL injection in order_id parameter during report creation"""
        # Attempt simple SQL Injection in URL
        response = self.client.get(f'/review/report-fraud/1 OR 1=1')
        # URL resolver should reject it
        self.assertEqual(response.status_code, 404)

    def test_csrf_protection_on_create_report(self):
        """Test CSRF protection on create report POST"""
        client = Client(enforce_csrf_checks=True)
        client.login(username='customer', password='password123')
        
        url = reverse('review:report_fraud', kwargs={'order_id': self.order1.id})
        # POST tanpa CSRF token
        response = client.post(url, data={'message': 'Test CSRF attack'})
        self.assertEqual(response.status_code, 403)

    def test_ssrf_attempt_by_header_manipulation(self):
        """Test SSRF attempt by manipulating headers on viewing report"""
        url = reverse('review:my_report')
        response = self.client.get(
            url,
            HTTP_HOST='evil-site.com',
            HTTP_REFERER='http://evil-site.com'
        )
    
        self.assertEqual(response.status_code, 400)


class ReviewViewsTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='12345')
        self.user2 = User.objects.create_user(username='testuser2', password='12345')
        self.worker1 = User.objects.create_user(username='testworker1', password='12345')
        
        self.customer1 = Customer.objects.create(
            user = self.user1,

        )

        self.worker1 = Worker.objects.create(
            user = self.worker1
        )

        # Create order status objects
        self.status_completed = OrderStatus.objects.create(status='COMPLETED')
        self.status_reviewed = OrderStatus.objects.create(status='reviewed')

        self.cart1 = Cart.objects.create(
            id=uuid.uuid4(),
            customer=self.customer1,
            is_checked_out=True
        )
        
        # Create test orders
        self.order1 = Order.objects.create(
            id=uuid.uuid4(),
            cart=self.cart1,
            total=15,
            status=self.status_completed,
            worker=self.worker1,
            delivery_fee=5000
        )
        
        # Create test review
        self.review1 = Review.objects.create(
            review_id=uuid.uuid4(),
            user=self.user1,
            order=self.order1,
            description="This is a test review",
            rating=4
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_create_review_get(self):
        """Test that the create review page loads correctly"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:create_review', args=[str(self.order1.pk)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_review_form.html')
        self.assertIsInstance(response.context['form'], ReviewForm)
    
    def test_create_review_post_success(self):
        """Test successful review creation"""
        self.client.login(username='testuser1', password='12345')

        cart2 = Cart.objects.create(
            id=uuid.uuid4(),
            customer=self.customer1,
            is_checked_out=True
        )
        
        # Create a new order for this test to avoid duplicate reviews
        new_order = Order.objects.create(
            id=uuid.uuid4(),
            cart=cart2,
            total=15,
            status=self.status_completed,
            worker=self.worker1,
            delivery_fee=5000
        )
        
        url = reverse('review:create_review', args=[str(new_order.pk)])
        
        data = {
            'description': 'This is a new test review',
            'rating': 5
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if review was created
        self.assertEqual(Review.objects.count(), 2)
        
        # Check if order status was updated to 'reviewed'
        new_order.refresh_from_db()
        self.assertEqual(new_order.status, self.status_reviewed)
        
        # Check the content of the new review
        new_review = Review.objects.exclude(pk=self.review1.pk).first()
        self.assertEqual(new_review.description, 'This is a new test review')
        self.assertEqual(new_review.rating, 5)
    
    def test_create_review_post_invalid_form(self):
        """Test review creation with invalid form data"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:create_review', args=[str(self.order1.pk)])
        
        # Missing required rating field
        data = {
            'description': 'This is an invalid review'
        }
        
        response = self.client.post(url, data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        
        # No new review should be created
        self.assertEqual(Review.objects.count(), 1)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Terjadi kesalahan dalam pengisian formulir.")
    
    def test_create_review_xss_sanitization(self):
        """Test that XSS input is properly sanitized"""
        self.client.login(username='testuser1', password='12345')
        
        cart2 = Cart.objects.create(
            id=uuid.uuid4(),
            customer=self.customer1,
            is_checked_out=True
        )
        
        # Create a new order for this test to avoid duplicate reviews
        new_order = Order.objects.create(
            id=uuid.uuid4(),
            cart=cart2,
            total=15,
            status=self.status_completed,
            worker=self.worker1,
            delivery_fee=5000
        )
        
        url = reverse('review:create_review', args=[str(new_order.pk)])
        
        xss_script = '<script>alert("XSS")</script>'
        data = {
            'description': xss_script,
            'rating': 3
        }
        
        response = self.client.post(url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Verify sanitization worked
        new_review = Review.objects.exclude(pk=self.review1.pk).first()
        self.assertNotEqual(new_review.description, xss_script)
        self.assertEqual(new_review.description, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')
    
    def test_get_review_for_customer(self):
        """Test getting reviews for a customer"""
        # Mock the get_user_role function to return 'Customer'
        from unittest.mock import patch
        with patch('review.views.get_user_role', return_value='Customer'):
            self.client.login(username='testuser1', password='12345')
            url = reverse('review:my_review')
            
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'user_review.html')
            self.assertTrue(response.context['is_customer'])
            self.assertEqual(len(response.context['reviews']), 1)
            self.assertEqual(response.context['reviews'][0], self.review1)
    
    def test_get_review_for_non_customer(self):
        """Test getting reviews for a non-customer user"""
        # Mock the get_user_role function to return 'Staff'
        from unittest.mock import patch
        with patch('review.views.get_user_role', return_value='Staff'):
            self.client.login(username='testuser1', password='12345')
            url = reverse('review:my_review')
            
            response = self.client.get(url)
            
            # Should return JsonResponse
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(
                str(response.content, encoding='utf8'),
                {'message': 'hmm you cannot see this, your not customer'}
            )
    
    def test_update_review_get(self):
        """Test that the edit review page loads correctly"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:update_review', args=[str(self.review1.pk)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_review.html')
        self.assertIsInstance(response.context['form'], ReviewForm)
    
    def test_update_review_post_success(self):
        """Test successful review updating"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:update_review', args=[str(self.review1.pk)])
        
        updated_description = 'Updated review description'
        data = {
            'description': updated_description,
            'rating': 5
        }
        
        response = self.client.post(url, data)
        
        # Now we can check for the redirect since the bug is fixed
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if review was updated
        updated_review = Review.objects.get(pk=self.review1.pk)
        self.assertEqual(updated_review.description, updated_description)
        self.assertEqual(updated_review.rating, 5)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Review berhasil diperbarui!")
    
    def test_update_review_unauthorized_user(self):
        """Test review editing by unauthorized user"""
        # Login as user2 (who did not create the review)
        self.client.login(username='testuser2', password='12345')
        url = reverse('review:update_review', args=[str(self.review1.pk)])
        
        response = self.client.get(url)
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Anda tidak memiliki izin untuk mengedit report ini.")
    
    def test_update_review_post_invalid_form(self):
        """Test review updating with invalid form data"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:update_review', args=[str(self.review1.pk)])
        
        # Invalid rating (assuming rating has validation rules, e.g., must be positive)
        data = {
            'description': 'Valid description',
            'rating': -1  # Invalid rating
        }
        
        response = self.client.post(url, data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Terjadi kesalahan dalam pengisian formulir.")
        
        # Review should not be updated
        unchanged_review = Review.objects.get(pk=self.review1.pk)
        self.assertEqual(unchanged_review.description, "This is a test review")
        self.assertEqual(unchanged_review.rating, 4)
    
    def test_delete_review_success(self):
        """Test successful review deletion"""
        self.client.login(username='testuser1', password='12345')
        url = reverse('review:delete_review', args=[str(self.review1.pk)])
        
        response = self.client.post(url)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('main:home'))
        
        # Check if review was deleted
        self.assertEqual(Review.objects.count(), 0)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Review berhasil dihapus.")
    
    def test_delete_nonexistent_review(self):
        """Test deleting a nonexistent review"""
        self.client.login(username='testuser1', password='12345')
        
        # Create a random UUID that doesn't exist in the database
        fake_uuid = uuid.uuid4()
        while Review.objects.filter(pk=fake_uuid).exists():
            fake_uuid = uuid.uuid4()
            
        url = reverse('review:delete_review', args=[str(fake_uuid)])
        
        # This should raise a 404 Not Found
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
    
    def test_review_order_not_found(self):
        """Test creating a review for a non-existent order"""
        self.client.login(username='testuser1', password='12345')
        
        # Generate a random order ID that doesn't exist
        fake_order_id = uuid.uuid4()
        while Order.objects.filter(pk=fake_order_id).exists():
            fake_order_id = uuid.uuid4()
            
        url = reverse('review:create_review', args=[str(fake_order_id)])
        
        # Should return 404 Not Found
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_sql_injection_in_order_id(self):
        """Test SQL injection in order_id parameter during review creation"""
        # Attempt simple SQL Injection in URL
        response = self.client.get(f'/review/create-review/1 OR 1=1')
        # URL resolver should reject it
        self.assertEqual(response.status_code, 404)

    def test_csrf_protection_on_create_review(self):
        """Test CSRF protection on create report POST"""
        client = Client(enforce_csrf_checks=True)
        client.login(username='customer', password='password123')
        
        url = reverse('review:create_review', kwargs={'order_id': self.order1.id})
        # POST tanpa CSRF token
        response = client.post(url, data={'message': 'Test CSRF attack'})
        self.assertEqual(response.status_code, 403)

    def test_ssrf_attempt_by_header_manipulation(self):
        """Test SSRF attempt by manipulating headers on viewing review"""
        url = reverse('review:my_review')
        response = self.client.get(
            url,
            HTTP_HOST='evil-site.com',
            HTTP_REFERER='http://evil-site.com'
        )
    
        self.assertEqual(response.status_code, 400)
