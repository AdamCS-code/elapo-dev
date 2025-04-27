from django.http import HttpResponseForbidden
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.contrib import messages
from main.models import Customer, Worker
from product.models import Product
from cart.models import Cart, ProductCart
from order.models import Order, OrderStatus
import uuid


class WorkerTakeOrderTest(TestCase):
    def setUp(self):
        # ===== 1. Create Users & Profiles =====
        # Customer
        self.customer_user = User.objects.create_user(
            username='customer',
            password='testpass123',
            email='customer@example.com'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            first_name="Test",
            last_name="Customer",
            email="customer@example.com",
            nomor_hp='081212341234',
            domicile="jaksel"
        )
        
        # Worker
        self.worker_user = User.objects.create_user(
            username='worker',
            password='testpass123',
            email='worker@example.com'
        )
        self.worker = Worker.objects.create(
            user=self.worker_user,
            first_name="Test",
            last_name="Worker",
            nomor_hp='081256785678',
            email="worker@example.com",
            domicile="jakbar"
        )

        # ===== 2. Create Product =====
        self.product = Product.objects.create(
            product_name="Test Product",
            price=50000,
            description="Test description",
            stock=10
        )

        # ===== 3. Create Cart with ProductCart =====
        self.cart = Cart.objects.create(
            customer=self.customer,
            is_checked_out=True
        )
        ProductCart.objects.create(
            product=self.product,
            quantity=2,
            cart=self.cart
        )

        # ===== 4. Create Order Statuses =====
        self.pending_status = OrderStatus.objects.create(
            id=uuid.uuid4(),
            status='pending'
        )
        self.delivered_status = OrderStatus.objects.create(
            id=uuid.uuid4(),
            status='delivered'
        )

        # ===== 5. Create Order =====
        self.order = Order.objects.create(
            id=uuid.uuid4(),
            cart=self.cart,
            status=self.pending_status,
            total=100000,
            delivery_fee=20000
        )

        self.client = Client()

        self.take_order_url = reverse('worker:take_order_status', kwargs={'pk': self.order.id})
        self.worker_home_url = reverse('main:home')

    def test_take_order_unauthenticated(self):
        response = self.client.get(self.take_order_url)
        self.assertRedirects(response, f'/login/?next={self.take_order_url}')


    def test_take_order_not_worker(self):
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(self.take_order_url)
        self.assertRedirects(response, reverse('main:login'))

    def test_take_order_get_form(self):
        self.client.login(username='worker', password='testpass123')
        response = self.client.get(self.take_order_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Take Order")
        self.assertEqual(response.context['order_id'], self.order.id)
        self.assertEqual(response.context['customer'], self.customer)

    def test_take_order_success(self):
        self.client.login(username='worker', password='testpass123')
        response = self.client.post(self.take_order_url, {'action': 'take'})
        
        self.order.refresh_from_db()
        self.worker.refresh_from_db()
        
        self.assertRedirects(response, reverse('order:order_detail', kwargs={'id': self.order.id}))
        self.assertEqual(self.order.worker, self.worker)
        self.assertEqual(self.order.status.status, 'delivered')
        self.assertFalse(self.worker.available)


    def test_take_already_taken_order(self):
        other_worker = Worker.objects.create(
            user=User.objects.create_user(username='other_worker', password='testpass123'),
            available=True
        )
        self.order.worker = other_worker
        self.order.save()
        
        self.client.login(username='worker', password='testpass123')
        response = self.client.post(self.take_order_url, {'action': 'take'})
        
        self.assertRedirects(response, self.worker_home_url)
        
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(str(messages_list[0]), "This order has already been taken by someone else.")

    def test_decline_order(self):
        self.client.login(username='worker', password='testpass123')
        response = self.client.post(self.take_order_url, {'action': 'decline'})
        
        self.assertRedirects(response, self.worker_home_url)
        
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(str(messages_list[0]), "Declined")

    def test_worker_homepage_shows_available_orders(self):
        # Create another available order
        another_cart = Cart.objects.create(
            customer=self.customer,
            is_checked_out=True
        )
        ProductCart.objects.create(
            product=self.product,
            quantity=1,
            cart=another_cart
        )
        another_order = Order.objects.create(
            id=uuid.uuid4(),
            cart=another_cart,
            status=self.pending_status,
            total=50000,
            delivery_fee=15000
        )

        self.client.login(username='worker', password='testpass123')
        response = self.client.get(reverse('worker:homepage'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'worker_homepage.html')
        
        # Check both orders appear in context (since neither has a worker)
        self.assertEqual(len(response.context['orders']), 2)
        self.assertIn(self.order, response.context['orders'])
        self.assertIn(another_order, response.context['orders'])
        

    def test_worker_homepage_hides_taken_orders(self):
        # Assign our test order to the worker
        self.order.worker = self.worker
        self.order.save()

        self.client.login(username='worker', password='testpass123')
        response = self.client.get(reverse('worker:homepage'))
        
        # Only orders with no worker should appear
        self.assertEqual(len(response.context['orders']), 0)

    def test_unavailable_worker_sees_no_orders(self):
        # Create multiple available orders
        for i in range(3):
            cart = Cart.objects.create(
                customer=self.customer,
                is_checked_out=True
            )
            ProductCart.objects.create(
                product=self.product,
                quantity=1,
                cart=cart
            )
            Order.objects.create(
                id=uuid.uuid4(),
                cart=cart,
                status=self.pending_status,
                total=50000,
                delivery_fee=15000
            )
        
        # Make worker unavailable
        self.worker.available = False
        self.worker.save()
        
        self.client.login(username='worker', password='testpass123')
        response = self.client.get(reverse('main:home'))
        
        # Should see no orders even though 3 exist
        self.assertEqual(len(response.context['orders']), 0)




class CompleteOrderStatusTest(TestCase):
    def setUp(self):
        # ===== 1. Create Users & Profiles =====
        # Customer
        self.customer_user = User.objects.create_user(
            username='customer',
            password='testpass123',
            email='customer@example.com'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            first_name="Test",
            last_name="Customer",
            email="customer@example.com",
            nomor_hp='081212341234',
            domicile="jaksel"
        )
        
        # Worker
        self.worker_user = User.objects.create_user(
            username='worker1',
            password='testpass123',
            email='worker@example.com'
        )
        self.worker = Worker.objects.create(
            user=self.worker_user,
            first_name="Test",
            last_name="Worker",
            nomor_hp='081256785678',
            email="worker@example.com",
            domicile="jakbar"
        )

        # Create another worker
        self.other_worker_user = User.objects.create_user(
            username='worker2',
            password='testpass456',
            email='otherworker@example.com'
        )
        self.other_worker = Worker.objects.create(
            user=self.other_worker_user,
            first_name="Other",
            last_name="Worker",
            nomor_hp='085612345678',
            email="otherworker@example.com",
            domicile="jakpus"
        )

        # Create product and order
        self.product = Product.objects.create(
            product_name="Test Product",
            price=50000,
            stock=10
        )
        self.cart = Cart.objects.create(
            customer=self.customer,
            is_checked_out=True
        )
        ProductCart.objects.create(
            product=self.product,
            quantity=2,
            cart=self.cart
        )

        # Create order statuses
        self.delivered_status = OrderStatus.objects.create(
            id=uuid.uuid4(),
            status='delivered'
        )
        self.completed_status = OrderStatus.objects.create(
            id=uuid.uuid4(),
            status='completed'
        )

        # Create order assigned to our worker
        self.order = Order.objects.create(
            id=uuid.uuid4(),
            cart=self.cart,
            status=self.delivered_status,
            worker=self.worker,
            total=100000,
            delivery_fee=20000
        )

        # Test client and URLs
        self.client = Client()
        self.complete_url = reverse('worker:complete_order_status', kwargs={'pk': self.order.id})
        self.complete_page_url = reverse('worker:order_complete_page')
        self.home_url = reverse('main:home')

    def test_complete_order_success(self):
        self.client.login(username='worker1', password='testpass123')
        response = self.client.post(self.complete_url)
        
        # Refresh from DB
        self.order.refresh_from_db()
        self.worker.refresh_from_db()

        print("Order status after completion:")
        print(self.order.status.status)
        
        # Check status changed
        self.assertEqual(self.order.status.status, 'completed')
        
        # Check worker availability
        self.assertTrue(self.worker.available)
        
        # Check redirect
        self.assertRedirects(response, self.complete_page_url)


    def test_complete_other_workers_order(self):
        # Assign order to other worker
        self.order.worker = self.other_worker
        self.order.save()
        
        self.client.login(username='worker1', password='testpass123')
        response = self.client.post(self.complete_url)

        print("Response content:")
        print(response)


        
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.content.decode(), "You are not authorized to complete this order")

    def test_unauthenticated_access(self):
        response = self.client.post(self.complete_url)
        self.assertRedirects(
            response,
            f"/login/?next={self.complete_url}"
        )

    def test_non_worker_access(self):
        """Regular users should be prevented from accessing"""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(self.complete_url)
        self.assertRedirects(response, reverse('main:login'))
