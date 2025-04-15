from django.urls import path
from . import views

app_name = 'administrator'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('no-permission/', views.no_permission, name='no_permission')
]

