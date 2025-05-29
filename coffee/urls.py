from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
import coffee.views as views


urlpatterns = [
    path('', views.home, name='home'),
    path('coffee/', views.coffee_list, name='coffee_list'),
    #path('cart/', views.cart_view, name='cart_view'),
    path('login/', views.login_view, name='login'),
    path('initiate-payment/', views.initiate_payment_view, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
    


]