from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
#from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login
import requests
from .models import Coffee


def home(request):
    coffee = Coffee.objects.all()
    return render(request, 'home.html', {'coffee': coffee})


def coffee_list(request):
    query = request.GET.get('q')
    origin_filter = request.GET.get('origin')

    coffees = Coffee.objects.all()
    if query:
        coffees = coffees.filter(name__icontains=query)
    if origin_filter:
        coffees = coffees.filter(origin=origin_filter)

    top_rated = Coffee.objects.order_by('-rating')[:3]
    origins = Coffee.objects.values_list('origin', flat=True).distinct()

    context = {
        'coffee': coffees,
        'top_rated_coffees': top_rated,
        'unique_origins': origins,
        'cart_count': request.session.get('cart_count', 0),
    }
    return render(request, 'coffee_list.html', context)


def cart_view(request):
    # You can customize this later with real cart logic
    return render(request, 'coffee/cart.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
    return render(request, 'login.html')


def start_payment(request):
    amount = 100  # hardcoded for demo, replace with actual cart total

    chapa_url = "https://api.chapa.co/v1/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    callback_url = request.build_absolute_uri(reverse('verify_payment'))

    data = {
        "amount": amount,
        "currency": "ETB",
        "email": request.user.email if request.user.is_authenticated else "customer@example.com",
        "first_name": request.user.first_name if request.user.is_authenticated else "Guest",
        "last_name": request.user.last_name if request.user.is_authenticated else "User",
        "callback_url": callback_url,
        "return_url": callback_url,
        "description": "Coffee Shop Purchase"
    }

    response = requests.post(chapa_url, json=data, headers=headers)
    res_data = response.json()

    if res_data.get("status") == "success":
        payment_url = res_data["data"]["checkout_url"]
        return redirect(payment_url)
    else:
        error_message = res_data.get("message", "Payment initialization failed.")
        return render(request, "payment_failed.html", {"error": error_message})


def verify_payment(request):
    tx_ref = request.GET.get('tx_ref')

    if not tx_ref:
        return JsonResponse({"error": "Transaction reference missing"}, status=400)

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
    }

    verify_url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
    response = requests.get(verify_url, headers=headers)
    res_data = response.json()

    if res_data.get("status") == "success" and res_data["data"]["status"] == "success":
        # You can update order/payment status here in DB if needed
        return render(request, "payment_success.html", {"payment_data": res_data["data"]})
    else:
        error_msg = res_data.get("message", "Payment verification failed.")
        return render(request, "payment_failed.html", {"error": error_msg})


def payment_success(request):
    return render(request, "payment_success.html")


def payment_failed(request):
    return render(request, "payment_failed.html")


def initiate_payment_view(request):
    context = {
        "chapa_public_key": settings.CHAPA_PUBLIC_KEY,
        "callback_url": request.build_absolute_uri(reverse('verify_payment')),
        "return_url": request.build_absolute_uri(reverse('payment_success')),
    }
    return render(request, "initiate_payment.html", context)