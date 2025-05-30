from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.urls import reverse
from django.utils import timezone
import requests
import json
from .models import Coffee


def home(request):
    coffee = Coffee.objects.all()
    callback_url = request.build_absolute_uri(reverse('payment_success'))
    return_url = request.build_absolute_uri(reverse('payment_failed'))

    context = {
        'coffee': coffee,
        'now': timezone.now(),
        'callback_url': callback_url,
        'return_url': return_url,
    }
    return render(request, 'home.html', context)

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

def is_valid_email(email):
    # Simple regex for email validation
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return bool(re.match(email_regex, email))


def start_payment(request, coffee_id):
    coffee = get_object_or_404(Coffee, id=coffee_id)
    amount = coffee.price

    chapa_url = "https://api.chapa.co/v1/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    callback_url = request.build_absolute_uri(reverse('verify_payment'))

    data = {
        "amount": amount,
        "currency": "ETB",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "callback_url": callback_url,
        "return_url": callback_url,
        "tx_ref": f"TX-{coffee.id}-guest",
        "description": f"Buying {coffee.name}"
    }

    print("DEBUG: Sending to Chapa:", data)

    response = requests.post(chapa_url, json=data, headers=headers)
    res_data = response.json()

    if res_data.get("status") == "success":
        return redirect(res_data["data"]["checkout_url"])
    else:
        error_message = res_data.get("message", "Payment initialization failed.")
        return render(request, "payment_failed.html", {"error": error_message, "details": res_data})

def payment_success(request):
    return render(request, "payment_success.html")

def payment_failed(request):
    return render(request, "payment_failed.html")

def initiate_payment_view(request):
    context = {
        "chapa_public_key": settings.CHAPA_PUBLIC_KEY,
        "callback_url": request.build_absolute_uri(reverse('payment_success')),
        "return_url": request.build_absolute_uri(reverse('payment_failed')),
    }
    return render(request, "initiate_payment.html", context)

def verify_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tx_ref = data.get('tx_ref')
            status = data.get('status')
            return JsonResponse({"message": "Payment verified"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)
