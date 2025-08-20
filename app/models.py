from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import random
import re


# Email OTP
class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))


# Store
class Store(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=100)
    brand_logo = models.URLField(blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20)
    Bio = models.CharField(max_length=100)
    total_views = models.PositiveIntegerField(default=0)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.brand_name

    def save(self, *args, **kwargs):
        if not self.slug and self.brand_name:
            base_slug = slugify(self.brand_name)
            slug = base_slug
            counter = 1
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/shop/{self.slug}/"


# Store Image
class StoreImage(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='images')
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='extra_files', null=True, blank=True)
    image = models.ImageField(upload_to='store_images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    file = models.FileField(upload_to='store_media/', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True)
    price = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Extra file for {self.store.brand_name} - {self.item.name if self.item else 'No item'}"


# Item
class Item(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="No Caption")
    price = models.CharField(max_length=255, default="No Caption")
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    slug = models.SlugField(unique=True, blank=True)  # For /product/<slug>/

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Item.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/product/{self.slug}/"


# Product Media
class ProductMedia(models.Model):
    product = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='product_media/', blank=True, null=True)  # optional
    youtube_id = models.CharField(max_length=50, blank=True, null=True)
    youtube_url = models.URLField(max_length=255, blank=True, null=True)  # original link
    label = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True, null=True)

    def is_video_file(self):
        return self.file and self.file.name.lower().endswith(('.mp4', '.mov', '.webm'))

    def is_youtube_video(self):
        return bool(self.youtube_id)

    def save(self, *args, **kwargs):
        if self.youtube_url and not self.youtube_id:
            match = re.search(r"(?:v=|be/)([A-Za-z0-9_-]{11})", self.youtube_url)
            if match:
                self.youtube_id = match.group(1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Media for {self.product.name}"


# Item Views
class ItemView(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='views_log')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


# Item Likes
class ItemLike(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('item', 'user', 'session_key')  # prevent double likes

    def __str__(self):
        return f"{self.item.name} liked"
