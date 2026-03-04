from django.shortcuts import render, redirect,get_object_or_404
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
from .serializers import ItemSerializer
from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rapidfuzz import process, fuzz
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from django.db.models import Q, Min, Max
from collections import OrderedDict
from django.http import HttpResponseRedirect
import pandas as pd
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Sum, Count, F
from django.urls import reverse
from .utils import guestOrder 
from django.urls import reverse
from django.http import Http404
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import io, qrcode
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
# Create your views here.


def home(request):
    # Create an ordered dictionary to maintain category order
    grouped_items = OrderedDict()

    # Loop through all categories
    for category in Category.objects.all():
        items = Item.objects.filter(category=category)[:4]  # Limit per category
        if items:
            grouped_items[category] = items

    # Also include Uncategorized items if they exist
    uncategorized_items = Item.objects.filter(category__isnull=True)[:4]
    if uncategorized_items:
        grouped_items['Uncategorized'] = uncategorized_items

    context = {
        'grouped_items': grouped_items,
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
    data = cartData(request)
    cart_items = data['cart_items']

    items = Item.objects.all()
    categories = Category.objects.all()

    # For price filter
    min_price = Item.objects.aggregate(Min("price"))["price__min"] or 0
    max_price = Item.objects.aggregate(Max("price"))["price__max"] or 1000

    context = {
        "items": items,
        "categories": categories,
        "cart_items": cart_items,
        "min_price": min_price,
        "max_price": max_price,
    }
    return render(request, "core/product.html", context)


def filter_products(request):
    search = request.GET.get("search", "")
    category_id = request.GET.get("category", "")
    min_price = request.GET.get("min_price", 0)
    max_price = request.GET.get("max_price", 1000000)

    items = Item.objects.all()

    if search:
        items = items.filter(title__icontains=search)

    if category_id:
        items = items.filter(category_id=category_id)

    items = items.filter(price__gte=min_price, price__lte=max_price)

    data = []
    for item in items:
        data.append({
            "id": item.id,
            "title": item.title,
            "price": float(item.price),
            "image": item.imageURL,
            "on_sale": item.on_sale,
        })

    return JsonResponse({"items": data})

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

@csrf_exempt
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    # ✅ Handle authenticated vs guest
    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)
        order, created = Order.objects.get_or_create(customer=customer, ordered=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id
    order.paypal_order_id = data['form'].get('paypal_order_id')

    # ✅ Payment validation
    if total == float(order.get_cart_total):
        order.ordered = True
        order.payment_status = "COMPLETED"
    else:
        order.payment_status = "FAILED"
    order.save()

    # ✅ Save shipping info
    shipping_details = None
    if order.shipping:
        shipping_details = Shippingdetails.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    # ✅ Build verification URL dynamically
    verify_url = request.build_absolute_uri(
        reverse("core:verify_order", args=[order.id])
    )

    # ✅ Determine recipient email
    customer_email = None
    if customer.user and customer.user.email:
        customer_email = customer.user.email
    elif data['form'].get('email'):
        customer_email = data['form']['email']

    recipient_list = []
    if customer_email:
        recipient_list.append(customer_email)
    recipient_list.append(settings.EMAIL_HOST_USER)  # always CC yourself

    # ✅ Render HTML template with context
    html_content = render_to_string("core/email_order_confirmation.html", {
        "order": order,
        "total": total,
        "verify_url": verify_url,
        "shipping": shipping_details,
    })

    # Plain-text fallback
    text_content = (
        f"Thank you for your purchase!\n\n"
        f"Order ID: {order.id}\n"
        f"Total: ${total}\n"
        f"Status: {order.payment_status}\n\n"
        f"Verify your order: {verify_url}"
    )

    # ✅ Send email
    try:
        email = EmailMultiAlternatives(
            subject="Order Confirmation - YourShop",
            body=text_content,  # fallback text for clients that can’t render HTML
            from_email=settings.EMAIL_HOST_USER,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    except Exception as e:
        print("❌ Email sending failed:", str(e))

    # ✅ JSON Response (redirect)
    return JsonResponse({
        "redirect_url": reverse("core:payment_success", args=[order.id]),
    })


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


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'core/item_detail.html', {'item': item})


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    items = Item.objects.filter(category=category)
    data = cartData(request)
    cart_items = data['cart_items']

    context = {
        'category': category,
        'items': items,
        'cart_items': cart_items,
    }

    return render(request, 'core/category_products.html', context)


@api_view(['GET'])
def ItemAutocompleteView(request):
    query = request.GET.get('q', '')
    if query:
        items = Item.objects.filter(
            Q(title__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
        items = items[:10]  # apply slicing AFTER distinct()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)
    return Response([])


@api_view(['GET'])
def SearchResultAPIView(request):
    query = request.GET.get('q', '')
    if query:
        items = Item.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)
    return Response([]) 


def SearchResultPageView(request):
    query = request.GET.get('q', '')
    items = []
    
    if query:
        items = Item.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

        # 🔁 Redirect to item detail page if exactly 1 result found
        if items.count() == 1:
            return redirect('core:item_detail', pk=items.first().id)

    return render(request, 'core/search_results.html', {
        'items': items,
        'query': query
    })



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


def is_admin(user):
    return user.is_superuser or user.is_staff

def is_vendor(user):
    return hasattr(user, "vendorprofile")

# -----------------------------
# Admin Dashboard
# -----------------------------
@staff_member_required
def admin_dashboard(request):
    role = "Admin"
    query = request.GET.get("q", "").strip()  # For search/filtering vendors

    # Stats
    total_sales = OrderItem.objects.aggregate(total=Sum("item__price"))["total"] or 0
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    top_product = (
        OrderItem.objects.values("item__title")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")
        .first()
    )

    # Vendor approval lists
    pending_vendors = VendorProfile.objects.filter(approved=False)
    approved_vendors = VendorProfile.objects.filter(approved=True)

    # Apply search filter if query exists
    if query:
        pending_vendors = pending_vendors.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(shop_name__icontains=query)
        )
        approved_vendors = approved_vendors.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(shop_name__icontains=query)
        )

    # Handle Approve / Reject via AJAX
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        vendor_id = request.POST.get("vendor_id")
        action = request.POST.get("action")
        vendor = get_object_or_404(VendorProfile, id=vendor_id)

        if action == "approve":
            vendor.approved = True
            vendor.save()
            message = f"{vendor.shop_name} has been approved."
        elif action == "reject":
            vendor.delete()
            message = f"{vendor.shop_name}'s application was rejected."
        else:
            return JsonResponse({"success": False, "message": "Invalid action."})

        return JsonResponse({"success": True, "message": message, "vendor_id": vendor_id, "action": action})

    context = {
        "role": role,
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "top_product": top_product["item__title"] if top_product else "N/A",
        "pending_vendors": pending_vendors,
        "approved_vendors": approved_vendors,
        "query": query,
    }

    return render(request, "dashboard/dashboard.html", context)


# -----------------------------
# Vendor / Customer Dashboard
# -----------------------------
@login_required
def dashboard_view(request):
    user = request.user

    # -------------------
    # Vendor
    # -------------------
    if hasattr(user, "vendorprofile"):
        vendor = user.vendorprofile           # VendorProfile instance
        vendor_user = vendor.user             # The actual User instance linked to items

    # If vendor not approved yet
        if not vendor.approved:
            return render(request, "vendor/pending_approval.html")

        # TOTAL SALES
        total_sales = (
            OrderItem.objects.filter(item__vendor=vendor_user)
            .aggregate(total=Sum("item__price"))["total"] or 0
        )

        # TOTAL ORDERS
        total_orders = (
            Order.objects.filter(orderitem__item__vendor=vendor_user)
            .distinct()
            .count()
        )

        # TOTAL PRODUCTS
        total_products = Item.objects.filter(vendor=vendor_user).count()

        # TOP PRODUCT
        top_product_qs = (
            OrderItem.objects.filter(item__vendor=vendor_user)
            .values("item__title")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")
        )
        top_product = top_product_qs.first()["item__title"] if top_product_qs.exists() else "N/A"

        # PRODUCT LIST
        vendor_products = Item.objects.filter(vendor=vendor_user)

        # ORDERS FOR THIS VENDOR
        vendor_orders = Order.objects.filter(orderitem__item__vendor=vendor_user).distinct()

        context = {
            "role": "Vendor",
            "total_sales": total_sales,
            "total_orders": total_orders,
            "total_products": total_products,
            "top_product": top_product,
            "vendor_products": vendor_products,
            "vendor_orders": vendor_orders,
        }
    # -------------------
    # Customer
    # -------------------
    else:
        customer = user.customer
        total_orders = Order.objects.filter(customer=customer).count()
        total_spent = (
            OrderItem.objects.filter(order__customer=customer)
            .aggregate(total=Sum("item__price"))["total"] or 0
        )
        total_items = (
            OrderItem.objects.filter(order__customer=customer)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        context = {
            "role": "Customer",
            "total_orders": total_orders,
            "total_sales": total_spent,
            "total_items": total_items,
            "top_product": "N/A",
        }

    return render(request, "dashboard/dashboard.html", context)


def apply_filters(queryset, request, via_order=True):
    """Helper to apply date/category filters from GET params"""
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    category_id = request.GET.get("category")

    if start_date:
        if via_order:
            queryset = queryset.filter(created_at__date__gte=parse_date(start_date))
        else:
            queryset = queryset.filter(order__created_at__date__gte=parse_date(start_date))

    if end_date:
        if via_order:
            queryset = queryset.filter(created_at__date__lte=parse_date(end_date))
        else:
            queryset = queryset.filter(order__created_at__date__lte=parse_date(end_date))

    if category_id:
        if via_order:
            queryset = queryset.filter(orderitem__item__category_id=category_id)
        else:
            queryset = queryset.filter(item__category_id=category_id)

    return queryset


@login_required
def sales_data(request):
    # Determine user role safely
    if hasattr(request.user, "vendorprofile"):
        role = "Vendor"
    elif request.user.is_staff or request.user.is_superuser:
        role = "Admin"
    else:
        role = "Customer"

    # --- ADMIN SALES DATA ---
    if role == "Admin":
        orders = Order.objects.filter(complete=True)
        orders = apply_filters(orders, request, via_order=True)

        sales = (
            orders.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum(F("orderitem__quantity") * F("orderitem__item__price")))
            .order_by("month")
        )
        return JsonResponse(list(sales), safe=False)

    # --- VENDOR SALES DATA ---
    elif role == "Vendor":
        sales = (
            OrderItem.objects.filter(item__vendor=request.user)
            .annotate(month=TruncMonth("order__created_at"))
            .values("month")
            .annotate(total=Sum(F("quantity") * F("item__price")))
            .order_by("month")
        )
        sales = apply_filters(sales, request, via_order=False)
        return JsonResponse(list(sales), safe=False)

    # --- CUSTOMER PURCHASE DATA ---
    else:
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            return JsonResponse([], safe=False)

        purchases = (
            Order.objects.filter(customer=customer, complete=True)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum(F("orderitem__quantity") * F("orderitem__item__price")))
            .order_by("month")
        )
        purchases = apply_filters(purchases, request, via_order=True)
        return JsonResponse(list(purchases), safe=False)


@login_required
def top_products(request):
    # Determine user role safely
    if hasattr(request.user, "vendorprofile"):
        role = "Vendor"
    elif request.user.is_staff or request.user.is_superuser:
        role = "Admin"
    else:
        role = "Customer"

    # --- ADMIN TOP PRODUCTS ---
    if role == "Admin":
        qs = OrderItem.objects.all()
        qs = apply_filters(qs, request, via_order=False)

        products = (
            qs.values("item__title")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )
        return JsonResponse(list(products), safe=False)

    # --- VENDOR TOP PRODUCTS ---
    elif role == "Vendor":
        products = (
            OrderItem.objects.filter(item__vendor=request.user)
            .values("item__title")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )
        products = apply_filters(products, request, via_order=False)
        return JsonResponse(list(products), safe=False)

    # --- CUSTOMERS DON'T NEED THIS DATA ---
    return JsonResponse([], safe=False)


@login_required
def user_growth(request):
    # Determine user role safely
    if hasattr(request.user, "vendorprofile"):
        role = "Vendor"
    elif request.user.is_staff or request.user.is_superuser:
        role = "Admin"
    else:
        role = "Customer"

    # --- ADMIN USER GROWTH ---
    if role == "Admin":
        users = (
            Customer.objects.annotate(month=TruncMonth("user__date_joined"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        return JsonResponse(list(users), safe=False)

    # --- OTHER ROLES DON'T GET GROWTH DATA ---
    return JsonResponse([], safe=False)


# ---------------- Export Options ---------------- #
@login_required
def export_sales_csv(request):
    orders = Order.objects.all().values("id", "customer__user__username", "transaction_id", "date_ordered")
    df = pd.DataFrame(orders)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=sales.csv"
    df.to_csv(path_or_buf=response, index=False)
    return response


@login_required
def export_sales_excel(request):
    orders = Order.objects.all().values("id", "customer__user__username", "transaction_id", "date_ordered")
    df = pd.DataFrame(orders)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=sales.xlsx"
    df.to_excel(response, index=False)
    return response


@login_required
def export_sales_pdf(request):
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=sales.pdf"

    doc = SimpleDocTemplate(response, pagesize=A4)
    orders = Order.objects.all().values_list("id", "customer__user__username", "transaction_id", "date_ordered")

    table_data = [["ID", "User", "Total", "Date"]] + list(orders)
    table = Table(table_data)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                               ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("GRID", (0, 0), (-1, -1), 1, colors.black)]))
    doc.build([table])
    return response

def verify_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    shipping = order.shippingdetails_set.first()  # get the first shipping record if exists

    if not order.ordered or order.payment_status != "COMPLETED":
        raise Http404("Order not found or not completed")

    return render(request, "core/verify_order.html", {"order": order, "shipping": shipping})

def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, ordered=True)

    verify_url = request.build_absolute_uri(
        reverse("core:verify_order", args=[order.id])
    )

    context = {
        "order": order,
        "verify_url": verify_url,
    }
    return render(request, "core/payment_success.html", context)

def order_qr_code(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)

        # ✅ Build ngrok/public URL (if running with ngrok)
        public_url = getattr(settings, "PUBLIC_URL", None)
        if not public_url:
            try:
                resp = requests.get("http://127.0.0.1:4040/api/tunnels")
                tunnels = resp.json().get("tunnels", [])
                for tunnel in tunnels:
                    if tunnel["proto"] == "https":
                        public_url = tunnel["public_url"]
                        settings.PUBLIC_URL = public_url
                        break
            except Exception:
                raise Http404("Ngrok tunnel not running")

        if not public_url:
            raise Http404("No public URL found")

        # ✅ Full verify URL
        verify_url = f"{public_url}{reverse('core:verify_order', args=[order.id])}"

        # ✅ Generate QR code as PNG
        qr = qrcode.make(verify_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")

    except Order.DoesNotExist:
        raise Http404("Order not found")
    
def register_vendor(request):
    shop_name_error = None  # For template error display

    if request.method == "POST":
        form = SignUpForm(request.POST)
        shop_name = request.POST.get("shop_name", "").strip()

        # Validate shop_name
        if not shop_name:
            shop_name_error = "Shop name is required."

        if form.is_valid() and not shop_name_error:
            # Save the User
            user = form.save()

            # Create VendorProfile linked to this user
            VendorProfile.objects.create(
                user=user,
                shop_name=shop_name,
                approved=False  # Vendor requires admin approval
            )

            # Authenticate user to select correct backend
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if user is not None:
                login(request, user)  # Now login works even with multiple backends

            messages.success(
                request,
                "Vendor account created successfully! Your application is awaiting admin approval."
            )
            return redirect("core:dashboard")  # Adjust to your URL name

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = SignUpForm()

    return render(
        request,
        "vendor/register_vendor.html",
        {"form": form, "shop_name_error": shop_name_error}
    )


@user_passes_test(is_admin)
def vendor_approval_list(request):
    pending = VendorProfile.objects.filter(approved=False)
    return render(request, "admin/vendor_approval_list.html", {"pending": pending})

@login_required
def reject_product(request, item_id):
    role = getattr(request.user.profile, "role", "Customer")
    if role != "Admin":
        return redirect("core:dashboard")

    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        item.is_approved = False
        item.approval_status = "Rejected"
        item.rejection_reason = reason
        item.save()

        # optional email notify vendor
        # send_mail(...)

        messages.error(request, f"{item.title} rejected.")
        return redirect("core:pending_products")

    return render(request, "admin/reject_product.html", {"item": item})

@login_required
def approve_product(request, item_id):
    role = getattr(request.user.profile, "role", "Customer")
    if role != "Admin":
        return redirect("core:dashboard")

    item = get_object_or_404(Item, id=item_id)
    item.is_approved = True
    item.approval_status = "Approved"
    item.rejection_reason = ""
    item.save()

    # optional email notify vendor
    # send_mail(...)

    messages.success(request, f"{item.title} has been approved.")
    return redirect("core:pending_products")

@login_required
def pending_products(request):
    role = getattr(request.user.profile, "role", "Customer")
    if role != "Admin":
        return redirect("core:dashboard")

    pending = Item.objects.filter(approval_status="Pending")

    return render(request, "admin/pending_products.html", {
        "pending": pending,
        "role": role
    })

@login_required
def vendor_products(request):
    role = getattr(request.user.profile, "role", "Customer")
    if role != "Vendor":
        return redirect("core:dashboard")

    items = Item.objects.filter(vendor=request.user)

    return render(request, "vendor/vendor_products.html", {
        "items": items,
        "role": role
    })

@user_passes_test(is_admin)
def approve_vendor(request, vendor_id):
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    vendor.approved = True
    vendor.save()

    messages.success(request, f"{vendor.shop_name} has been approved as a vendor.")
    return redirect("vendor_approval_list")



@staff_member_required
def vendor_pending(request):
    query = request.GET.get("q", "").strip()  # Get search query

    # Base QuerySets
    pending_vendors = VendorProfile.objects.filter(approved=False)
    approved_vendors = VendorProfile.objects.filter(approved=True)

    # Apply search filter if query exists
    if query:
        pending_vendors = pending_vendors.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(shop_name__icontains=query)
        )
        approved_vendors = approved_vendors.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(shop_name__icontains=query)
        )

    # Handle Approve/Reject POST actions
    if request.method == "POST":
        vendor_id = request.POST.get("vendor_id")
        action = request.POST.get("action")
        vendor = get_object_or_404(VendorProfile, id=vendor_id)

        # AJAX request handling
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            if action == "approve":
                vendor.approved = True
                vendor.save()
                message = f"{vendor.shop_name} has been approved."
            elif action == "reject":
                vendor.delete()
                message = f"{vendor.shop_name}'s application was rejected."
            else:
                return JsonResponse({"success": False, "message": "Invalid action."})
            
            return JsonResponse({
                "success": True,
                "message": message,
                "vendor_id": vendor_id,
                "action": action
            })

        # Regular POST (non-AJAX)
        if action == "approve":
            vendor.approved = True
            vendor.save()
            messages.success(request, f"{vendor.shop_name} has been approved as a vendor.")
        elif action == "reject":
            vendor.delete()
            messages.warning(request, f"{vendor.shop_name}'s vendor application was rejected.")

        return redirect("vendor_pending")

    return render(request, "admin/vendor_pending.html", {
        "pending_vendors": pending_vendors,
        "approved_vendors": approved_vendors,
        "query": query
    })

@csrf_exempt
@login_required
def vendor_delete_product(request, product_id):
    vendor_user = request.user

    product = Item.objects.filter(id=product_id, vendor=vendor_user).first()

    if not product:
        return JsonResponse({"error": "Product not found"}, status=404)

    product.delete()
    return JsonResponse({"message": "Product deleted successfully"})

@csrf_exempt
@login_required
def vendor_update_order_status(request, order_id):
    if request.method == "POST":
        vendor_user = request.user

        order = (
            Order.objects.filter(
                id=order_id,
                orderitem__item__vendor=vendor_user
            ).distinct().first()
        )

        if not order:
            return JsonResponse({"error": "Order not found"}, status=404)

        body = json.loads(request.body)
        new_status = body.get("status")

        valid_statuses = ["Pending", "Shipped", "Delivered", "Cancelled"]

        if new_status not in valid_statuses:
            return JsonResponse({"error": "Invalid status"}, status=400)

        order.status = new_status
        order.save()

        return JsonResponse({"message": "Order updated successfully"})

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def add_product(request):
    user = request.user
    
    # User must be a vendor
    if not hasattr(user, "vendorprofile"):
        messages.error(request, "Only vendors can add products.")
        return redirect("core:dashboard")

    if request.method == "POST":
        title = request.POST.get("title")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        description = request.POST.get("description")

        # Create the product
        Item.objects.create(
            vendor=user,  # IMPORTANT: vendor is a User FK
            title=title,
            price=price,
            stock=stock,
            description=description,
        )

        messages.success(request, "Product added successfully!")
        return redirect("core:dashboard")

    return render(request, "vendor/add_product.html")

