from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from product.models import Product
from .models import Testimony

class TestimonyTests(TestCase):

    def setUp(self):
        # Buat user dan product untuk testing
        self.user = User.objects.create_user(username='user1', password='password')
        self.product = Product.objects.create(
            id='3282910e-54ff-41fe-be6e-4b1a96160145', 
            product_name='air mineral', 
            price=10000, 
            description='minuman asli dari afrika', 
            stock=100
        )

    def test_create_testimony(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('create_testimony', args=[self.product.id]), {
            'message': 'Testimoni baru',
            'rating': 5,
        })
        self.assertEqual(response.status_code, 302)  # redirect setelah berhasil
        self.assertTrue(Testimony.objects.filter(user=self.user).exists())

    def test_edit_testimony(self):
        testimony = Testimony.objects.create(
            user=self.user,
            product=self.product,
            message='Testimoni lama',
            rating=4,
        )
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('edit_testimony', args=[testimony.testimony_id]), {
            'message': 'Testimoni yang sudah diperbarui',
            'rating': 5,
        })
        testimony.refresh_from_db()
        self.assertEqual(testimony.message, 'Testimoni yang sudah diperbarui')
        self.assertEqual(response.status_code, 302)

    def test_delete_testimony(self):
        testimony = Testimony.objects.create(
            user=self.user,
            product=self.product,
            message='Testimoni yang akan dihapus',
            rating=3,
        )
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('delete_testimony', args=[testimony.testimony_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Testimony.objects.filter(pk=testimony.pk).exists())

    def test_user_cannot_edit_or_delete_others_testimony(self):
        other_user = User.objects.create_user(username='user2', password='password')
        testimony = Testimony.objects.create(
            user=other_user,
            product=self.product,
            message='Testimoni orang lain',
            rating=4,
        )
        self.client.login(username='user1', password='password')

        # Test tidak bisa edit testimoni orang lain
        response = self.client.post(reverse('edit_testimony', args=[testimony.testimony_id]), {
            'message': 'Testimoni yang diperbarui',
            'rating': 5,
        })
        self.assertEqual(response.status_code, 302)

        # Test tidak bisa hapus testimoni orang lain
        response = self.client.post(reverse('delete_testimony', args=[testimony.testimony_id]))
        self.assertEqual(response.status_code, 302)

    def test_create_testimony_with_sanitization(self):
        # Login sebagai user
        self.client.login(username='user1', password='password')
        
        # Kirim input dengan HTML berbahaya
        response = self.client.post(reverse('create_testimony', args=[self.product.id]), {
            'message': '<script>alert("XSS")</script>Testimoni baru',
            'rating': 5,
        })
            
        # Verifikasi bahwa input sudah disanitasi
        testimony = Testimony.objects.latest('created_at')
        self.assertNotIn('<script>', testimony.message)  # Pastikan <script> tidak ada di dalam pesan
        self.assertNotIn('</script>', testimony.message)
        self.assertIn('Testimoni baru', testimony.message)  # Pastikan pesan yang disanitasi ada

        # Verifikasi redirect
        self.assertEqual(response.status_code, 302)  # Redirect setelah berhasil
        
    def test_create_testimony_with_csrf(self):
        # Login sebagai user
        self.client.login(username='user1', password='password')

        # Kirim POST request dengan CSRF token (secara otomatis oleh client)
        response = self.client.post(reverse('create_testimony', args=[self.product.id]), {
            'message': 'Testimoni dengan CSRF',
            'rating': 5,
        })

        # Verifikasi bahwa testimoni berhasil dibuat
        self.assertEqual(response.status_code, 302)  # Redirect setelah berhasil
        self.assertTrue(Testimony.objects.filter(user=self.user).exists())

    def test_edit_testimony_with_sanitization(self):
        # Membuat testimoni untuk user
        testimony = Testimony.objects.create(
            user=self.user,
            product=self.product,
            message='Testimoni lama',
            rating=4,
        )

        # Login sebagai user
        self.client.login(username='user1', password='password')

        # Kirim POST request dengan HTML berbahaya pada edit
        response = self.client.post(reverse('edit_testimony', args=[testimony.testimony_id]), {
            'message': '<script>alert("XSS")</script>Testimoni yang sudah diperbarui',
            'rating': 5,
        })

        testimony.refresh_from_db()

        # Verifikasi bahwa input sudah disanitasi
        self.assertNotIn('<script>', testimony.message)
        self.assertNotIn('</script>', testimony.message)
        self.assertIn('Testimoni yang sudah diperbarui', testimony.message)

        # Verifikasi redirect
        self.assertEqual(response.status_code, 302)  # Redirect setelah berhasil