from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from core.utils import cartData, guestOrder
from. models import *
from django.conf import settings
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm
from django import forms
from django.views.decorators.csrf import csrf_exempt




# Create your views here.

def home(request):
    items = Item.objects.all()

    context = { 
           'items': items, 
           }
         
    return render(request, "core/index.html", context)

def checkout(request):

    data = cartData(request)
    cart_items = data['cart_items']
    order = data['order']
    items = data['items']
    
    context = { 
        'items': items,'order' :order,'cart_items' :cart_items

        }
    return render(request, "core/checkout.html", context)

# view for adding to cart 

def cart(request):

    data = cartData(request)
    cart_items = data['cart_items']
    order = data['order']
    items = data['items']
    
    context = { 
        'items': items, 'order' :order, 'cart_items' :cart_items

        }
    
    return render(request, "core/cart.html", context)


def product(request):
     items = Item.objects.all()
     
     data = cartData(request)
     cart_items = data['cart_items']
        
    
     context = { 
           'items': items,'cart_items' :cart_items
           }
   
     return render(request, "core/product.html", context)

#view that handles the  update of the cart 

def updateItem(request):
    data = json.loads(request.body)
    productId = data.get('productId') 
    action = data.get('action')
    print('action:', action)
    print('productId:', productId)

    customer, created = Customer.objects.get_or_create(user=request.user)
    item = Item.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, ordered= False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, item=item)

    if action == 'add':
      orderItem.quantity += 1

    elif action == 'remove':
     orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    
    # Get updated cart totals
    cart_items = order.get_cart_items 
    return JsonResponse({
        'message': 'Item was updated',
        'cartItems': cart_items,
    })

def processOrder(request):
    transaction_id =datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)
        order, created = Order.objects.get_or_create(customer=customer, ordered= False)
       

    else:
        customer, order = guestOrder(request,data)

        total =float (data['form']['total'])
        order.transaction_id =transaction_id

        if total == float(order.get_cart_total):
          order.ordered = True
          order.save()

        if order.shipping == True:
            Shippingdetails.objects.create(
             customer = customer,
             order= order,
             address= data['shipping']['address'],
             city= data['shipping']['city'],
             state= data['shipping']['state'],
             zipcode= data['shipping']['zipcode'],

         )


        return JsonResponse('Payment complete!', safe=False)



def blog(request):
    context = { 
        }
       
    return render(request, "core/blog_list.html", context)


def login_user(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been logged in!')
            return redirect('core:home')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'core/login.html', {})  
    else:
        return render(request, 'core/login.html', {})
    

def logout_user(request):
    logout(request)
    messages.success(request, ('You have been logged out ...'))
    return redirect('core:home')

def register_user(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
           form.save()
           username= form.cleaned_data['username']
           password = form.cleaned_data['password1']
           #log in  user
           user= authenticate(username=username, password=password)
           login(request,user)
           messages.success(request, ('You have Registered successfully...'))
           return redirect ('core:home')
        else:
            messages.success(request, ('whoops! There was a problem, please try again... '))
            return redirect ('core:register')
    else:       
         return render(request, 'core/register.html', {'form': form })


def about(request):
    context = { 
        }
       
    return render(request, "core/about.html.", context)


def testimonial(request):
    context = { 
        }
    return render(request, "core/testimonial.html", context)



def get_access_token():
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post('https://api-m.sandbox.paypal.com/v1/oauth2/token', headers=headers, data=data, auth=auth)
    return response.json()['access_token']


@csrf_exempt
def create_order(request):
    try:
        data = json.loads(request.body)
        total = str(float(data.get('total', '0.00')))  # ✅ Parse and ensure it's a valid string
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    token = get_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": total
            }
        }]
    }

    response = requests.post("https://api-m.sandbox.paypal.com/v2/checkout/orders", headers=headers, data=json.dumps(body))
    if response.status_code in [200, 201]:
        data = response.json()
        return JsonResponse({'id': data['id']})
    else:
        return JsonResponse({'error': 'Failed to create PayPal order'}, status=500)

@csrf_exempt
def capture_order(request, order_id):
    token = get_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
    response = requests.post(url, headers=headers)
    return JsonResponse(response.json())

