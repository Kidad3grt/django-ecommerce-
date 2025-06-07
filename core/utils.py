import json
import datetime 
from . models import *
from .models import Customer 

def cookieCart(request):
    try:
          cart = json.loads(request.COOKIES['cart'])
    except:
          cart = {}
    print('CART:', cart)

    items = []
    order = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False }
    cart_items = order['get_cart_items']

    for i in cart:
        try:
            item = Item.objects.get(id=int(i))  
            quantity = cart[i]['quantity']
            total = item.price * quantity

            order['get_cart_total'] += total
            order['get_cart_items'] += quantity
            cart_items += quantity
            item = {
			'item':{
				'id':item.id,
				'title':item.title, 
				'price':item.price, 
				'imageURL':item.imageURL
				}, 
            
			'quantity':quantity,
			'get_total':total
         
				}
            items.append(item)
        except Item.DoesNotExist:
            print(f"Item with id {i} not found.")
            continue
        except Exception as e:
           print(f"Error with item {i}: {e}")
           continue
    
    return{'items': items, 'order' :order, 'cart_items' :cart_items}

def cartData(request):
    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)
        order, created = Order.objects.get_or_create(customer=customer, ordered= False)
        items = order.orderitem_set.all()
        cart_items = order.get_cart_items
    else:
        cookieData = cookieCart(request)
        cart_items = cookieData['cart_items']
        order = cookieData['order']
        items = cookieData['items']

    return{'items': items, 'order' :order, 'cart_items' :cart_items}

def guestOrder(request, data):
    print('User is not logged in...')

    print('COOKIES:', request.COOKIES)
    name = data['form']['name']
    email = data['form']['email']
    
    cookieData = cookieCart(request)
    items = cookieData['items']
    customer, created = Customer.objects.get_or_create(
		email= email,
        )
    
    customer.name = name
    customer.save()

    order = Order.objects.create(
	customer=customer,
	ordered=False,
		)

    for item in items:
        item_obj = Item.objects.get(id=item['item']['id'])
        orderItem = OrderItem.objects.create(
        item=item_obj,
        order=order,
        quantity=item['quantity']
        )
    return customer, order