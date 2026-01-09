from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import random
import re
from django.urls import reverse

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


from django.utils.text import slugify
from django.urls import reverse
from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify

class StoreTemplate(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)
    preview_image = models.ImageField(
        upload_to='template_previews/',
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Store(models.Model):
    # ===== CORE IDENTITY =====
    brand_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    brand_logo = models.ImageField(upload_to='brands/')
    brand_logo_url = models.URLField(max_length=500, blank=True, null=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="stores"
    )

    # ===== TEMPLATE =====
    template = models.ForeignKey(
        StoreTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stores"
    )

    # ===== BRAND CONTENT =====
    bio = models.TextField(help_text="Short brand description")

    about = models.TextField(blank=True, null=True, default="No About Set")
    mission = models.TextField(blank=True, null=True, default="No Mission Set")
    founder_name = models.CharField(max_length=100, blank=True, null=True, default="Unknown")
    brand_story = models.TextField(blank=True, null=True, default="No Story Set")


    # ===== BUSINESS INFO =====
    BUSINESS_CHOICES = [
        ('retail', 'Retail'),
        ('services', 'Services'),
        ('food', 'Food & Beverage'),
        ('fashion', 'Fashion'),
        ('tech', 'Technology'),
        ('other', 'Other'),
    ]

    business_type = models.CharField(
        max_length=50,
        choices=BUSINESS_CHOICES,
        blank=True,
        null=True
    )

    address = models.CharField(max_length=255, blank=True, null=True)

    # ===== ORDER SYSTEM =====
    ORDER_SYSTEM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('facebook', 'Facebook Messenger'),
    ]

    order_system = models.CharField(
        max_length=20,
        choices=ORDER_SYSTEM_CHOICES,
        default='whatsapp'
    )

    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    telegram_username = models.CharField(max_length=50, blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)
    tiktok_link = models.URLField(blank=True, null=True)

    # ===== DESIGN =====
    background_color = models.CharField(
        max_length=20,
        default="#ffffff",
        help_text="Hex color (e.g. #F5F5F5)"
    )

    # ===== ANALYTICS =====
    total_views = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)

    # ===== META =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug or self.brand_name_changed():
            self.slug = slugify(self.brand_name)
        super().save(*args, **kwargs)

    def brand_name_changed(self):
        if not self.pk:
            return True
        old = Store.objects.filter(pk=self.pk).first()
        return old and old.brand_name != self.brand_name

    def get_absolute_url(self):
        if settings.DEBUG:
            return reverse(
                "store_template_home",
                kwargs={
                    "store_slug": self.slug,
                    "template_slug": self.template.slug if self.template else "default",
                },
            )
        return f"https://{self.slug}.waapfolio.com/"

    def __str__(self):
        return self.brand_name

    @staticmethod
    def get_user_store(user):
        return Store.objects.filter(owner=user).first()



# Store Image
class StoreImage(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='images')
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='extra_files', null=True, blank=True)
    image = models.ImageField(upload_to='store_images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    file = models.FileField(upload_to='store_media/', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True)
    CURRENCY_CHOICES = [
        ("NGN", "Naira (₦)"),
        ("USD", "US Dollar ($)"),
        ("EUR", "Euro (€)"),
        ("GBP", "British Pound (£)"),
    ]

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,  # allows form to be empty
        null=True    # allows database to store NULL
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="NGN",
        null=False,
        blank=False
    )


    def __str__(self):
        return f"Extra file for {self.store.brand_name} - {self.item.name if self.item else 'No item'}"


# Item
class Item(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=1000, default="No Caption")
    price = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        blank=True, 
        null=True
    )    
    currency = models.CharField(max_length=5, blank=True, null=True,)  # ✅ give safe default
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)
    ORDER_SYSTEM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('depop', 'Depop'),
    ]

    order_system = models.CharField(
        max_length=20,
        choices=ORDER_SYSTEM_CHOICES,
        default='whatsapp'
    )

    # Optional links if vendor wants specific ones per product
    facebook_link = models.URLField(max_length=255, blank=True, null=True)
    tiktok_link = models.URLField(max_length=255, blank=True, null=True)
    depop_link = models.URLField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, max_length=1000,)

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
        return reverse(
            "store_product_detail",
            kwargs={
                "store_slug": self.store.slug,
                "product_slug": self.slug,
            },
        )

    def get_store_url(self):
        return self.store.get_absolute_url()


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
class Report(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="reports")
    reported_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on {self.store.brand_name} by {self.reported_by or 'Anonymous'}"
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    link = models.URLField(blank=True, null=True)  # optional: link to the page/item
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
class Comment(models.Model):
    product = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # newest first

    def __str__(self):
        return f"{self.user.username} on {self.product.name}"