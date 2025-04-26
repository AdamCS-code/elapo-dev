from django.urls import path
from .views import edit_profile_worker, show_main_page, login, customer_register, worker_register, logout_user, show_register
app_name = 'main'

urlpatterns = [
    path('', show_main_page, name='home'),
    path('login/', login, name='login'),
    path('register/customer/', customer_register, name='customer_register'),
    path('register/worker/', worker_register, name='worker_register'),
    path('logout/', logout_user, name='logout'),
    path('register/', show_register, name='register'),
    path('edit-profile/', edit_profile_worker, name='edit_profile'),
]
