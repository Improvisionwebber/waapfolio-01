from django.contrib import admin
from .models import (
    EmailOTP, Store, StoreImage, Item, ProductMedia, ItemView, ItemLike
)


# Email OTP
@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_expired')
    search_fields = ('user__username', 'code')
    readonly_fields = ('created_at',)
    list_filter = ('created_at', 'expires_at')


# Store
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'owner', 'total_views', 'slug')
    search_fields = ('brand_name', 'owner__username', 'whatsapp_number')
    readonly_fields = ('slug',)
    prepopulated_fields = {"slug": ("brand_name",)}


# Store Image
@admin.register(StoreImage)
class StoreImageAdmin(admin.ModelAdmin):
    list_display = ('store', 'item', 'name', 'price')
    search_fields = ('store__brand_name', 'item__name', 'name')
    list_filter = ('store', 'item')


# Item
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'views', 'slug')
    search_fields = ('name', 'store__brand_name')
    readonly_fields = ('slug',)
    prepopulated_fields = {"slug": ("name",)}


# Product Media
@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ('product', 'label', 'youtube_id', 'is_video_file', 'is_youtube_video')
    search_fields = ('product__name', 'label', 'youtube_url')
    list_filter = ('product',)


# Item Views
@admin.register(ItemView)
class ItemViewAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'session_key', 'timestamp')
    search_fields = ('item__name', 'user__username', 'session_key')
    list_filter = ('timestamp', 'item')


# Item Likes
@admin.register(ItemLike)
class ItemLikeAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'session_key', 'created_at')
    search_fields = ('item__name', 'user__username', 'session_key')
    list_filter = ('created_at', 'item')
