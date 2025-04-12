from django.urls import path
from .views import show_order
app_name = 'order'

urlpatterns = [
    path('', show_order, name="show_order"),
]
