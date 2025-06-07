from django.urls import path
from .views import home , product, blog ,testimonial,about,cart,checkout,updateItem,processOrder,capture_order,create_order, login_user,logout_user,register_user

app_name = 'core'

urlpatterns = [
    path('',home, name='home'),
    path('index/',home, name='home'),
    path('product/', product, name='product'),
    path('blog_list/', blog, name='blog'),
    path('testimonial/', testimonial, name='testimonial'),
    path('about/', about, name='about'),
    path('cart/',cart, name='cart'),
    path('checkout/',checkout, name='checkout'),
    path('update_item/', updateItem, name='update_item'), 
    path('process_order/', processOrder, name='process_order'),
    path('paypal/create-order/',create_order, name='create_order'),
    path('paypal/capture-order/<str:order_id>/',capture_order, name='capture_order'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_user, name='register')
]


