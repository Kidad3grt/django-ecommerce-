from django.urls import path
from .views import home , product, blog ,testimonial,about,cart,checkout,updateItem,processOrder,capture_order,create_order, login_user,logout_user,register_user,item_detail,category_view,ItemAutocompleteView,SearchResultAPIView,SearchResultPageView,sales_data,top_products,user_growth,export_sales_csv,export_sales_excel,export_sales_pdf,dashboard_view,verify_order,payment_success,order_qr_code,filter_products, approve_product, reject_product, pending_products, vendor_products, register_vendor, vendor_pending, vendor_approval_list, approve_vendor, admin_dashboard, vendor_delete_product, vendor_update_order_status, add_product
app_name = 'core'

urlpatterns = [
    path('',home, name='home'),
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
    path("verify-order/<int:order_id>/",verify_order, name="verify_order"),
    path("order-qr/<int:order_id>/",order_qr_code, name="order_qr_code"),
    path("payment-success/<int:order_id>/",payment_success, name="payment_success"),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_user, name='register'),
    path('item/<int:pk>/', item_detail, name='item_detail'),
    path('category/<slug:slug>/', category_view, name='category_products'),
    path('api/autocomplete/', ItemAutocompleteView, name='item-autocomplete'),
    path('api/search/', SearchResultAPIView, name='item-search-api'),
    path('search/', SearchResultPageView, name='search-results-page'),
    path("filter-products/",filter_products, name="filter_products"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    # APIs for charts
    path('dashboard/sales-data/', sales_data, name='sales_data'),
    path('dashboard/top-products/', top_products, name='top_products'),
    path('dashboard/user-growth/', user_growth, name='user_growth'),

    # Export
    path('dashboard/export/csv/', export_sales_csv, name='export_sales_csv'),
    path('dashboard/export/excel/', export_sales_excel, name='export_sales_excel'),
    path('dashboard/export/pdf/', export_sales_pdf, name='export_sales_pdf'),

    path("admin/products/pending/", pending_products, name="pending_products"),
    path("admin/products/approve/<int:item_id>/", approve_product, name="approve_product"),
    path("admin/products/reject/<int:item_id>/", reject_product, name="reject_product"),

   # VENDOR VIEW APPROVAL STATUS
    path("vendor/my-products/", vendor_products, name="vendor_products"),
    
    path("vendor/register/", register_vendor, name="register_vendor"),
    path("vendor/pending/", vendor_pending, name="vendor_pending"),

    # PRODUCT ACTIONS
    path("product/delete/<int:product_id>/", vendor_delete_product, name="vendor_delete_product"),

    # ORDER ACTIONS
    path("order/status/<int:order_id>/", vendor_update_order_status,name="vendor_update_order_status"),

   # Admin approval
    path("admin/vendors/pending/", vendor_approval_list, name="vendor_approval_list"),
    path("admin/vendors/approve/<int:vendor_id>/", approve_vendor, name="approve_vendor"),
    path("vendor/product/add/", add_product, name="add_product")
]
