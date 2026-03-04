import os
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Item, Category  # adjust if models are elsewhere
from django.conf import settings

class Command(BaseCommand):
    help = "Import products from FakeStoreAPI into Item and Category models (with images)"

    def handle(self, *args, **kwargs):
        url = "https://fakestoreapi.com/products"
        self.stdout.write(self.style.NOTICE(f"Fetching products from {url}..."))

        try:
            response = requests.get(url)
            response.raise_for_status()
            products = response.json()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error fetching data: {e}"))
            return

        for product in products:
            # Handle category
            category_name = product.get("category", "Uncategorized").title()
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={"slug": slugify(category_name)},
            )

            # Handle item fields
            title = product.get("title", "Untitled")
            description = product.get("description", "")
            price = product.get("price", 0.0)
            image_url = product.get("image", None)

            # Avoid duplicates by title
            item, created = Item.objects.get_or_create(
                title=title,
                defaults={
                    "category": category,
                    "description": description,
                    "price": price,
                },
            )

            if created:
                # ✅ Download and save image if available
                if image_url:
                    try:
                        img_response = requests.get(image_url)
                        img_response.raise_for_status()
                        file_name = os.path.basename(image_url.split("?")[0])  # clean filename
                        item.image.save(file_name, ContentFile(img_response.content), save=True)
                        self.stdout.write(self.style.SUCCESS(f"Downloaded image for {title}"))
                    except Exception as e:
                        self.stderr.write(self.style.WARNING(f"Failed to download image for {title}: {e}"))

                self.stdout.write(self.style.SUCCESS(f"Added product: {title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Skipped existing product: {title}"))

        self.stdout.write(self.style.SUCCESS("✅ Import completed successfully!"))
