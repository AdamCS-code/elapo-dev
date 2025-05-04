from django.urls import path
from .views import order_complete_page, complete_order_status, take_order_status, worker_homepage, worker_profile_page, complete_order

app_name = "worker"

urlpatterns = [
    path('complete-order/<uuid:id>', complete_order, name='complete_order' ),
    path("order-complete-page/", order_complete_page, name="order_complete_page"),
    path("complete-order-status/<uuid:pk>", complete_order_status, name="complete_order_status"),
    path("take-order-status/<uuid:pk>/", take_order_status, name="take_order_status"),
    path("", worker_homepage, name="homepage"),
    path("profile/", worker_profile_page, name="profile"),
]
