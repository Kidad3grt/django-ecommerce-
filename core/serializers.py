from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    imageURL = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'title', 'category', 'description', 'price', 'imageURL', 'digital', 'on_sale']

    def get_imageURL(self, obj):
        return obj.imageURL