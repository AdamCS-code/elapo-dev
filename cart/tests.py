from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
import json
import uuid
from unittest.mock import patch, MagicMock

from cart.models import Cart, ProductCart
from product.models import Product
from order.models import Order, OrderStatus
from main.models import Customer


class CartViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user with needed permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
        )
        
        # Create customer for the user
        self.customer = Customer.objects.create(
            user=self.user,
        )
        
        # Add required permissions
        content_type = ContentType.objects.get_for_model(Cart)
        permissions = Permission.objects.filter(content_type=content_type)
        for permission in permissions:
            self.user.user_permissions.add(permission)
            
        content_type = ContentType.objects.get_for_model(ProductCart)
        permissions = Permission.objects.filter(content_type=content_type)
        for permission in permissions:
            self.user.user_permissions.add(permission)
        
        # Create test product
        self.product = Product.objects.create(
            product_name='Test Product',
            price=10.0,
            stock=20,
            description='Test description'
        )
        
        # Create test cart
        self.cart = Cart.objects.create(
            customer=self.customer,
            is_checked_out=False
        )
        
        # Create test product cart
        self.product_cart = ProductCart.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=5
        )
        
        # Create order status
        self.order_status = OrderStatus.objects.create(
            status='not paid'
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

    def test_delete_cart_success(self):
        """Test successful cart deletion"""
        cart_id = str(self.cart.id)
        response = self.client.post(
            reverse('cart:delete_cart'),
            json.dumps({'cart_id': cart_id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['message'], 'success to delete cart')
        self.assertFalse(Cart.objects.filter(id=cart_id).exists())

    def test_delete_cart_not_found(self):
        """Test deleting a non-existent cart"""
        non_existent_id = str(uuid.uuid4())
        response = self.client.post(
            reverse('cart:delete_cart'),
            json.dumps({'cart_id': non_existent_id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['error'], 'failed to delete, cannot find cart')

    def test_delete_productcart_success(self):
        """Test successful product cart deletion"""
        product_cart_id = str(self.product_cart.id)
        response = self.client.post(
            reverse('cart:delete_product_cart'),
            json.dumps({'productcart_id': product_cart_id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['success'], 'delete product')
        self.assertFalse(ProductCart.objects.filter(id=product_cart_id).exists())

    def test_delete_productcart_not_found(self):
        """Test deleting a non-existent product cart"""
        non_existent_id = str(uuid.uuid4())
        response = self.client.post(
            reverse('cart:delete_product_cart'),
            json.dumps({'productcart_id': non_existent_id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['error'], 'product cart is not found')

    def test_show_cart_existing(self):
        """Test showing an existing cart"""
        response = self.client.get(reverse('cart:show_cart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_cart.html')
        self.assertIn('cart_id', response.context)
        self.assertEqual(response.context['cart_id'], str(self.cart.id))

    def test_show_cart_create_new(self):
        """Test showing cart when none exists (should create new)"""
        # Delete existing cart
        self.cart.delete()
        
        response = self.client.get(reverse('cart:show_cart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_cart.html')
        self.assertIn('cart_id', response.context)
        self.assertTrue(Cart.objects.filter(customer=self.customer, is_checked_out=False).exists())

    def test_show_cart_no_customer(self):
        """Test showing cart when user is not a customer"""
        # Create new user without customer profile
        user_no_customer = User.objects.create_user(
            username='nocustomer',
            password='testpassword'
        )
        
        # Add permissions
        content_type = ContentType.objects.get_for_model(ProductCart)
        permission = Permission.objects.get(content_type=content_type, codename='view_productcart')
        user_no_customer.user_permissions.add(permission)
        
        client = Client()
        client.login(username='nocustomer', password='testpassword')
        
        with patch('django.contrib.auth.models.User.customer', None):
            response = client.get(reverse('cart:show_cart'))
            
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content)
            self.assertEqual(content['status'], 'failed to access cart page, you are not customer')

    def test_checkout_cart_success(self):
        """Test successful cart checkout"""
        response = self.client.post(
            reverse('cart:checkout_cart'),
            json.dumps({
                'cart_id': str(self.cart.id),
                'total': 50.0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['status'], 'success')
        
        # Check cart is marked as checked out
        self.cart.refresh_from_db()
        self.assertTrue(self.cart.is_checked_out)
        
        # Check order was created
        self.assertTrue(Order.objects.filter(cart=self.cart, total=50.0).exists())

    def test_checkout_cart_cart_not_found(self):
        """Test checkout with non-existent cart"""
        non_existent_id = str(uuid.uuid4())
        response = self.client.post(
            reverse('cart:checkout_cart'),
            json.dumps({
                'cart_id': non_existent_id,
                'total': 50.0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['message'], 'fail')

    def test_view_cart_success(self):
        """Test successful cart view"""
        response = self.client.get(
            reverse('cart:view_cart', kwargs={'id': str(self.cart.id)})
        )
        
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertIn('product_carts', content)
        self.assertEqual(len(content['product_carts']), 1)
        
        product_data = content['product_carts'][0]
        self.assertEqual(product_data['id'], str(self.product_cart.id))
        self.assertEqual(product_data['quantity'], 5)
        self.assertEqual(product_data['product']['product_name'], 'Test Product')

    def test_view_cart_not_found(self):
        """Test viewing a non-existent cart"""
        non_existent_id = str(uuid.uuid4())
        response = self.client.get(
            reverse('cart:view_cart', kwargs={'id': non_existent_id})
        )
        
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'cannot get cart object with such uuid')

    def test_edit_product_in_cart_success(self):
        """Test successful product cart edit"""
        response = self.client.post(
            reverse('cart:edit_product_cart'),
            json.dumps({
                'product_cart_id': str(self.product_cart.id),
                'amount': 10
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['message'], 'success')
        
        # Check quantity was updated
        self.product_cart.refresh_from_db()
        self.assertEqual(self.product_cart.quantity, 10)

    def test_edit_product_in_cart_delete_when_zero(self):
        """Test product cart gets deleted when quantity is set to zero"""
        response = self.client.post(
            reverse('cart:edit_product_cart'),
            json.dumps({
                'product_cart_id': str(self.product_cart.id),
                'amount': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        # Check product cart was deleted
        self.assertFalse(ProductCart.objects.filter(id=self.product_cart.id).exists())

    def test_edit_product_in_cart_invalid_quantity(self):
        """Test edit with invalid quantity"""
        response = self.client.post(
            reverse('cart:edit_product_cart'),
            json.dumps({
                'product_cart_id': str(self.product_cart.id),
                'amount': -1
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertIn('must be greater than 0', content['message'])
        
        # Check quantity remains unchanged
        self.product_cart.refresh_from_db()
        self.assertEqual(self.product_cart.quantity, 5)

    def test_edit_product_in_cart_exceeds_stock(self):
        """Test edit with quantity exceeding stock"""
        response = self.client.post(
            reverse('cart:edit_product_cart'),
            json.dumps({
                'product_cart_id': str(self.product_cart.id),
                'amount': 25  # Stock is 20
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertIn('must be greater than 0 and less than', content['message'])

    def test_add_product_to_cart_new_product(self):
        """Test adding a new product to cart"""
        # Create another product
        new_product = Product.objects.create(
            product_name='New Product',
            price=15.0,
            stock=30,
            description='New description'
        )
        
        response = self.client.post(
            reverse('cart:add_product_cart'),
            json.dumps({
                'product_id': str(new_product.id),
                'amount': 3
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['message'], 'success')
        
        # Check product cart was created
        product_cart = ProductCart.objects.filter(
            cart=self.cart,
            product=new_product
        ).first()
        
        self.assertIsNotNone(product_cart)
        self.assertEqual(product_cart.quantity, 3)

    def test_add_product_to_cart_existing_product(self):
        """Test adding more of an existing product to cart"""
        response = self.client.post(
            reverse('cart:add_product_cart'),
            json.dumps({
                'product_id': str(self.product.id),
                'amount': 3
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['message'], 'success')
        
        # Check quantity was updated
        self.product_cart.refresh_from_db()
        self.assertEqual(self.product_cart.quantity, 8)  # 5 + 3

    def test_add_product_to_cart_exceed_stock(self):
        """Test adding more than available stock"""
        response = self.client.post(
            reverse('cart:add_product_cart'),
            json.dumps({
                'product_id': str(self.product.id),
                'amount': 20  # Would make total 25, stock is 20
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['message'], 'Out of stock')

    def test_add_product_to_cart_invalid_amount(self):
        """Test adding invalid amount"""
        response = self.client.post(
            reverse('cart:add_product_cart'),
            json.dumps({
                'product_id': str(self.product.id),
                'amount': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['message'], 'Amount has to be positive integer')

    def test_add_product_to_cart_product_not_found(self):
        """Test adding non-existent product"""
        non_existent_id = uuid.uuid4()
        response = self.client.post(
            reverse('cart:add_product_cart'),
            json.dumps({
                'product_id': str(non_existent_id),
                'amount': 1
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['message'], 'Product does not exist')

    def test_add_product_to_cart_create_cart(self):
        """Test adding product when no cart exists (should create new)"""
        # Delete existing cart
        self.cart.delete()
        
        response = self.client.post(
            reverse('cart:add_product_cart'),
            json.dumps({
                'product_id': str(self.product.id),
                'amount': 2
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check new cart was created
        new_cart = Cart.objects.filter(customer=self.customer, is_checked_out=False).first()
        self.assertIsNotNone(new_cart)
        
        # Check product was added to cart
        product_cart = ProductCart.objects.filter(
            cart=new_cart,
            product=self.product
        ).first()
        
        self.assertIsNotNone(product_cart)
        self.assertEqual(product_cart.quantity, 2)

    def test_unauthorized_access(self):
        """Test accessing views without proper permissions"""
        # Create user with no permissions
        user_no_perms = User.objects.create_user(
            username='noperms',
            password='testpassword'
        )
        
        client = Client()
        client.login(username='noperms', password='testpassword')
        
        # Try to delete cart
        response = client.post(
            reverse('cart:delete_cart'),
            json.dumps({'cart_id': str(self.cart.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        
        # Try to view cart
        response = client.get(reverse('cart:show_cart'))
        self.assertEqual(response.status_code, 403)

    def test_csrf_protection_on_create_cart(self):
        """Test CSRF protection on create cart POST"""
        client = Client(enforce_csrf_checks=True)
        client.login(username='customer', password='password123')
        
        url = reverse('cart:add_product_cart')
        # POST tanpa CSRF token
        response = client.post(url, data={'message': 'Test CSRF attack'})
        self.assertEqual(response.status_code, 403)

    def test_ssrf_attempt_by_header_manipulation(self):
        """Test SSRF attempt by manipulating headers on viewing cart"""
        url = reverse('cart:show_cart')
        response = self.client.get(
            url,
            HTTP_HOST='evil-site.com',
            HTTP_REFERER='http://evil-site.com'
        )
    
        self.assertEqual(response.status_code, 400)