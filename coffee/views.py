import re
import uuid
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate, login as auth_login
from .models import Coffee


def home(request):
    coffee = Coffee.objects.all()
    context = {
        'coffee': coffee,
        'now': timezone.now(),
        'callback_url': request.build_absolute_uri(reverse('payment_success')),
        'return_url': request.build_absolute_uri(reverse('payment_failed')),
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


def cart(request):
    # your cart logic here
    return render(request, 'cart.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            # Optionally, add a message for invalid credentials
            pass
    return render(request, 'login.html')


def is_valid_email(email):
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return bool(re.match(email_regex, email))


def start_payment(request, coffee_id):
    coffee = get_object_or_404(Coffee, id=coffee_id)
    amount = coffee.price

    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')

        # Validate email
        if not is_valid_email(email):
            return render(request, 'payment_failed.html', {'error': 'Invalid email address'})

        chapa_url = "https://api.chapa.co/v1/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        callback_url = request.build_absolute_uri(reverse('payment_success'))
        return_url = request.build_absolute_uri(reverse('payment_failed'))

        tx_ref = f"TX-{coffee.id}-{uuid.uuid4()}"

        data = {
            "amount": amount,
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "callback_url": callback_url,
            "return_url": return_url,
            "tx_ref": tx_ref,
            "description": f"Buying {coffee.name}",
        }

        response = requests.post(chapa_url, json=data, headers=headers)
        res_data = response.json()

        if res_data.get("status") == "success":
            return redirect(res_data["data"]["checkout_url"])
        else:
            error_message = res_data.get("message", "Payment initialization failed.")
            return render(request, "payment_failed.html", {"error": error_message, "details": res_data})

    # If GET request, just show a form or redirect
    return redirect('home')

def payment_failed(request):
    error = request.GET.get('error', '')
    return render(request, "payment_failed.html", {"error": error})


def verify_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tx_ref = data.get('tx_ref')
            status = data.get('status')
            # You could add more verification or update DB records here
            return JsonResponse({"message": "Payment verified"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


def initiate_payment_view(request):
    context = {
        "chapa_public_key": settings.CHAPA_PUBLIC_KEY,
        "callback_url": request.build_absolute_uri(reverse('payment_success')),
        "return_url": request.build_absolute_uri(reverse('payment_failed')),
    }
    return render(request, "initiate_payment.html", context)
