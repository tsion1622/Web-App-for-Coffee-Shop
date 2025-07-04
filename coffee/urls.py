from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('coffee/', views.coffee_list, name='coffee_list'),
     path('cart/', views.cart, name='cart'),  # <-- Make sure this exists
    path('login/', views.login_view, name='login'),
    path('start-payment/<int:coffee_id>/', views.start_payment, name='start_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('initiate-payment/', views.initiate_payment_view, name='initiate_payment'),
]
