"""
URL configuration for elapo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

app_name = 'main'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('product/', include('product.urls', namespace='product')),
    path('wallet/', include('wallet.urls', namespace='wallet')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('order/', include('order.urls', namespace='order')),
    path('payment', include('payment.urls', namespace='payment')),
    path('delivery', include('delivery.urls', namespace='delivery')),
    path('worker/', include('worker.urls', namespace='worker')),
    path('review/', include('review.urls', namespace='review')),
    path('administrator/', include('administrator.urls', namespace='administrator')),
    path('testimony/', include('testimony.urls')),

]
