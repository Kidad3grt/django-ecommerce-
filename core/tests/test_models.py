from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from core.models import Category, Customer, Item, Order, OrderItem

class CategoryModelTest(TestCase):
    def test_category_slug_auto_generation(self):
        category = Category.objects.create(name="Electronics")
        self.assertEqual(category.slug, slugify("Electronics"))

    def test_category_str(self):
        category = Category.objects.create(name="Shoes")
        self.assertEqual(str(category), "Shoes")


class CustomerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="john", password="pass123")

    def test_customer_str_name(self):
        customer = Customer.objects.create(user=self.user, name="John Doe")
        self.assertEqual(str(customer), "John Doe")

    def test_customer_str_email(self):
        customer = Customer.objects.create(user=self.user, email="john@example.com")
        self.assertEqual(str(customer), "john@example.com")

    def test_customer_str_guest(self):
        customer = Customer.objects.create()
        self.assertEqual(str(customer), "Guest Customer")


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jane", password="pass123")
        self.customer = Customer.objects.create(user=self.user, name="Jane Doe")

    def test_order_str(self):
        order = Order.objects.create(customer=self.customer, transaction_id="abc123")
        self.assertEqual(str(order), str(order.id))


class OrderItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="admin123")
        self.customer = Customer.objects.create(user=self.user, name="Admin")
        self.category = Category.objects.create(name="Gadgets")
        self.item = Item.objects.create(title="Phone", price=200.00, category=self.category)
        self.order = Order.objects.create(customer=self.customer)

    def test_order_item_creation(self):
        order_item = OrderItem.objects.create(item=self.item, order=self.order, quantity=2)
        self.assertEqual(order_item.item.title, "Phone")
        self.assertEqual(order_item.order.id, self.order.id)
        self.assertEqual(order_item.quantity, 2)
        self.assertTrue(isinstance(order_item.data_added, timezone.datetime))


class ItemModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Clothing")

    def test_item_str(self):
        item = Item.objects.create(title="T-shirt", price=29.99, category=self.category)
        self.assertEqual(str(item), "T-shirt")

    def test_item_fields(self):
        item = Item.objects.create(
            title="Sneakers",
            price=59.99,
            category=self.category,
            description="Comfortable running shoes",
            digital=False,
            on_sale=True
        )
        self.assertEqual(item.title, "Sneakers")
        self.assertEqual(item.description, "Comfortable running shoes")
        self.assertFalse(item.digital)
        self.assertTrue(item.on_sale)
        self.assertEqual(item.category.name, "Clothing")