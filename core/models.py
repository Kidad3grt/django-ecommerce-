from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


# Create your models here.

class Customer(models.Model):
	user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
	name = models.CharField(max_length=200, null=True)
	email = models.EmailField(null=True, blank=True)

def __str__(self):
  return self.name or self.email or "Guest Customer"

class Item(models.Model):
    title = models.CharField(max_length=100, null=True)
    price = models.DecimalField(max_digits=7,decimal_places=2) 
    image = models.ImageField(null=True, blank=True)
    digital = models.BooleanField(default=False, null= True, blank= False)


    def __str__(self):
        return self.title
    
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url




class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null= True)

    def __str__(self):
        return str(self.id)
        
    @property
    def shipping(self):
        shipping = False
        orderItem = self.orderitem_set.all()
        for i in orderItem:
            if i.item.digital == False:
              shipping = True
        return shipping
    
    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total
    
       
    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total
    
class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, blank= True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    data_added = models.DateTimeField(default= timezone.now)


    @property
    def get_total(self):
        total = self.item.price * self.quantity
        return total

    

class Shippingdetails(models.Model):
  customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
  order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
  address = models.CharField(max_length=200, null=False)
  city = models.CharField(max_length=200, null=False)
  state = models.CharField(max_length=200, null=False)
  zipcode = models.CharField(max_length=200, null=False)
  date_added = models.DateTimeField(auto_now_add=True)

  def __str__(self):
     return self.address


