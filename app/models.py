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

    # # ===== DESIGN =====
    # background_color = models.CharField(
    #     max_length=20,
    #     default="#ffffff",
    #     help_text="Hex color (e.g. #F5F5F5)"
    # )

    # ===== ANALYTICS =====
    total_views = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)

    # ===== META =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def display_about(self):
        return self.about or (
            f"{self.brand_name} was created with a vision to deliver a refined "
            "and modern shopping experience built around quality, trust, and "
            "strong brand identity. Every product showcased through the store "
            "is carefully presented to create a seamless digital experience "
            "that feels premium, immersive, and customer-focused."
        )

    @property
    def display_mission(self):
        return self.mission or (
            f"The mission of {self.brand_name} is to redefine the way customers "
            "experience online shopping by combining premium presentation, "
            "reliable service, and curated collections into one seamless platform."
        )

    @property
    def display_founder(self):
        return self.founder_name or (
            f"The vision behind {self.brand_name} is rooted in creativity, "
            "innovation, consistency, and the desire to build a memorable "
            "customer experience."
        )
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
                    "template_slug": self.template.slug if self.template else "starter",
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
    slug = models.SlugField(unique=True, blank=True, max_length=255,)

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
# subscription

class Subscription(models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("premium_monthly", "Premium Monthly"),
        ("premium_yearly", "Premium Yearly"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    plan = models.CharField(
        max_length=30,
        choices=PLAN_CHOICES,
        default="free"
    )

    is_active = models.BooleanField(default=True)

    started_at = models.DateTimeField(
        default=timezone.now
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    paystack_customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    paystack_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    last_payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    auto_renew = models.BooleanField(
        default=False
    )

    def is_premium(self):
        if not self.is_active:
            return False

        return self.plan in [
            "premium_monthly",
            "premium_yearly",
        ]

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    TYPE_CHOICES = [
        ("earning", "Earning"),
        ("withdrawal", "Withdrawal"),
        ("commission", "Commission"),
        ("subscription", "Subscription"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
class CustomDomain(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE)

    domain = models.CharField(max_length=255)

    is_verified = models.BooleanField(default=False)

    purchased_from_waapfolio = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
class WithdrawalRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    account_name = models.CharField(max_length=255)

    account_number = models.CharField(max_length=20)

    bank_name = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

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
class Payment(models.Model):
    PLAN_CHOICES = [
        ("premium_monthly", "Premium Monthly"),
        ("premium_yearly", "Premium Yearly"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_payments"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    plan = models.CharField(
        max_length=30,
        choices=PLAN_CHOICES
    )

    reference = models.CharField(
        max_length=150,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.reference}"


class PaymentHistory(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PLAN_CHOICES = [
        ("free", "Free"),
        ("premium_monthly", "Premium Monthly"),
        ("premium_yearly", "Premium Yearly"),
        ("store_order", "Store Order"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payment_history"
    )

    reference = models.CharField(
        max_length=100,
        unique=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    plan = models.CharField(
        max_length=50,
        choices=PLAN_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    paystack_response = models.JSONField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

class Wallet(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    pending_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    available_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    lifetime_earnings = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    total_withdrawn = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} wallet"
class WalletTransaction(models.Model):

    TYPES = [
        ("sale", "Sale"),
        ("withdrawal", "Withdrawal"),
        ("refund", "Refund"),
        ("commission", "Commission"),
        ("hold_release", "Hold Release"),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TYPES
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    description = models.TextField()

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
class SellerTrust(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    successful_orders = models.IntegerField(
        default=0
    )

    disputes = models.IntegerField(
        default=0
    )

    chargebacks = models.IntegerField(
        default=0
    )

    fraud_flags = models.IntegerField(
        default=0
    )

    instant_withdrawal = models.BooleanField(
        default=False
    )

    risk_score = models.IntegerField(
        default=0
    )

    def evaluate(self):

        self.instant_withdrawal = (
            self.successful_orders >= 10
            and self.disputes == 0
            and self.chargebacks == 0
            and self.fraud_flags == 0
        )

        self.save()
import uuid
import random

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Order(models.Model):

    STATUS_CHOICES = [
        ("PENDING_PAYMENT", "Pending Payment"),
        ("PAID", "Paid"),
        ("ACCEPTED", "Accepted"),
        ("ON_HOLD", "On Hold"),
        ("AVAILABLE_FOR_WITHDRAWAL", "Available For Withdrawal"),
        ("WITHDRAWN", "Withdrawn"),
        ("REFUNDED", "Refunded"),
        ("DISPUTED", "Disputed"),
    ]

    order_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    store = models.ForeignKey(
        "Store",
        on_delete=models.CASCADE,
        related_name="orders"
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sales"
    )

    customer_name = models.CharField(
        max_length=255
    )

    customer_email = models.EmailField()

    customer_phone = models.CharField(
        max_length=30
    )

    delivery_address = models.TextField()

    delivery_city = models.CharField(
        max_length=100,
        blank=True
    )

    delivery_state = models.CharField(
        max_length=100,
        blank=True
    )

    delivery_note = models.TextField(
        blank=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    seller_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    paystack_reference = models.CharField(
        max_length=100,
        unique=True
    )

    verification_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    status = models.CharField(
        max_length=35,
        choices=STATUS_CHOICES,
        default="PENDING_PAYMENT"
    )

    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_orders"
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    hold_until = models.DateTimeField(
        null=True,
        blank=True
    )

    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):
        if not self.order_id:
            while True:
                order = f"WPF-{random.randint(10000000, 99999999)}"
                if not Order.objects.filter(order_id=order).exists():
                    self.order_id = order
                    break

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.store.brand_name}"
class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_name = models.CharField(
        max_length=255
    )

    product_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

class Cart(models.Model):

    customer_session = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return self.customer_session

    @property
    def total(self):

        return sum(

            item.product.price * item.quantity

            for item in self.items.all()

        )

    @property
    def total(self):

        return sum(

            item.product.price * item.quantity

            for item in self.items.all()

        )

        
class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Item,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "cart",
            "product",
        )

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

class AuditLog(models.Model):

    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL
    )

    action = models.CharField(
        max_length=255
    )

    object_type = models.CharField(
        max_length=100
    )

    object_id = models.CharField(
        max_length=100
    )

    ip_address = models.GenericIPAddressField(
        null=True
    )

    metadata = models.JSONField(
        default=dict
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
class BankAccount(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    bank_name = models.CharField(
        max_length=100
    )

    bank_code = models.CharField(
        max_length=20
    )

    account_number = models.CharField(
        max_length=20
    )

    account_name = models.CharField(
        max_length=255
    )

    recipient_code = models.CharField(
        max_length=255,
        unique=True
    )

    is_verified = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.bank_name} "
            f"({self.account_number})"
        )
class SupplierAccess(models.Model):

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="suppliers"
    )

    supplier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="supplier_for"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        unique_together = (
            "seller",
            "supplier",
        )

    def __str__(self):

        return (
            f"{self.seller.username} → "
            f"{self.supplier.username}"
        )