from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Store, Item

class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Store.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()   # uses Store.get_absolute_url


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Item.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()   # uses Item.get_absolute_url
