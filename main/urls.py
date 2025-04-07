from django.urls import path
from .views import show_main_page, login, customer_register, worker_register, logout_user
app_name = 'main'

urlpatterns = [
    path('', show_main_page, name='home'),
    path('login', login, name='login'),
    path('register/customer', customer_register, name='customer_register'),
    path('register/worker', worker_register, name='worker_register'),
    path('logout', logout_user, name='logout')
]
