from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from django.forms import modelformset_factory
from django.utils.text import slugify
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q

import requests
import base64

from .models import (
    Store, StoreImage, Item, ItemView, EmailOTP, ProductMedia, ItemLike
)
from .forms import (
    StoreForm, StoreImageForm, ProductForm
)
from .utils import upload_to_imgbb
from utils.email_service import send_email


# -------------------------
# Forms
# -------------------------
class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# -------------------------
# Public Views
# -------------------------
def home(request):
    store = None
    if request.user.is_authenticated:
        # Get all stores for the user
        stores = Store.objects.filter(owner=request.user)
        # Pick the first one if it exists
        store = stores.first()  # returns None if the user has no stores
    return render(request, 'home.html', {'store': store})


def about(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, 'about.html', {'store': store})


def profile(request):
    if not request.user.is_authenticated:
        return render(request, "login_required.html")
    store = Store.objects.filter(owner=request.user).first()
    return render(request, "profile.html", {'store': store})


def problem_solving(request):
    return render(request, "problem_solving.html")


def money(request):
    return render(request, "money.html")


def create_tutorial(request):
    return render(request, "create_tutorial.html")


def share_tutorial(request):
    return render(request, "share_tutorial.html")


def faqs(request):
    return render(request, "faqs.html")


def contact(request):
    return render(request, "contact.html")


def privacy(request):
    return render(request, "privacy_policy.html")


def security_settings(request):
    return render(request, 'security_settings.html')


@login_required
def account_information(request):
    user = request.user
    return render(request, 'account_information.html', {'user': user})


# -------------------------
# Registration / OTP
# -------------------------
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            otp_code = EmailOTP.generate_otp()
            EmailOTP.objects.create(
                user=user,
                code=otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )

            html_content = f"<p>Your OTP is <strong>{otp_code}</strong>. It expires in 5 minutes.</p>"
            status, resp = send_email(
                "Your WAAPFOLio Verification Code", html_content, user.email
            )
            print("Email API Response:", status, resp)

            return redirect('verify_email', user_id=user.id)
    else:
        form = RegistrationForm()

    return render(request, "register.html", {'form': form})


def verify_email(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        otp_input = request.POST['otp']
        otp_obj = EmailOTP.objects.get(user=user)
        if not otp_obj.is_expired() and otp_obj.code == otp_input:
            user.is_active = True
            user.save()
            otp_obj.delete()
            return redirect('login')
        return render(request, 'verify_email.html', {'error': 'Invalid or expired OTP'})
    return render(request, 'verify_email.html')


def send_otp_to_user(user):
    otp_code = EmailOTP.generate_otp()
    expires = timezone.now() + timezone.timedelta(minutes=10)
    EmailOTP.objects.update_or_create(
        user=user, defaults={"code": otp_code, "expires_at": expires}
    )
    subject = "Your Verification Code"
    html_content = f"<p>Your OTP is: <strong>{otp_code}</strong></p><p>It expires in 10 minutes.</p>"
    send_email(user.email, subject, html_content)


# -------------------------
# Store Views
# -------------------------
@login_required
def create_store(request, id=0):
    store_instance = get_object_or_404(Store, pk=id) if id else None

    if request.method == 'GET':
        form = StoreForm(instance=store_instance)
        return render(request, 'store/create_store.html', {'form': form})

    form = StoreForm(request.POST, request.FILES, instance=store_instance)
    if form.is_valid():
        store = form.save(commit=False)
        store.owner = request.user

        # Generate slug
        if not store.slug:
            base_slug = slugify(store.brand_name)
            slug = base_slug
            counter = 1
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            store.slug = slug

        # Upload brand logo to imgbb
        logo_file = request.FILES.get('brand_logo')
        if logo_file:
            try:
                url = 'https://api.imgbb.com/1/upload'
                payload = {
                    'key': 'c346e6e29bbc0340846deb957f6d510a',
                    'image': base64.b64encode(logo_file.read()).decode('utf-8')
                }
                response = requests.post(url, data=payload)
                data = response.json()
                if response.status_code == 200 and data.get('success'):
                    store.brand_logo = data['data']['url']
                else:
                    messages.error(request, f"Logo upload failed: {data.get('error', 'Unknown error')}")
            except Exception as e:
                messages.error(request, f"Logo upload failed: {str(e)}")

        store.save()
        messages.success(request, "Store saved successfully!")
        return redirect(store.get_absolute_url())

    return render(request, 'store/create_store.html', {'form': form})


def view_store(request, slug):
    store = get_object_or_404(Store, slug=slug)
    items = Item.objects.filter(store=store)
    full_url = request.build_absolute_uri()
    whatsapp_link = f"https://wa.me/{store.whatsapp_number}"

    # Track unique views
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    for item in items:
        view_filter = Q(session_key=session_key)
        if request.user.is_authenticated:
            view_filter |= Q(user=request.user)

        already_viewed = ItemView.objects.filter(item=item).filter(view_filter).exists()
        if not already_viewed:
            item.views += 1
            item.save()
            store.total_views += 1
            store.save()
            ItemView.objects.create(
                item=item,
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key
            )

    return render(request, 'store/view_store.html', {
        'store': store,
        'items': items,
        'full_url': full_url,
        'whatsapp_link': whatsapp_link,
    })



# -------------------------
# Product Management
# -------------------------
@login_required
def manage_store(request, slug, item_id=None):
    store = get_object_or_404(Store, slug=slug, owner=request.user)

    if item_id:
        item = get_object_or_404(Item, id=item_id, store=store)
        form = ProductForm(request.POST or None, request.FILES or None, instance=item)
        edit_mode = True
    else:
        item = None
        form = ProductForm(request.POST or None, request.FILES or None)
        edit_mode = False

    if request.method == "POST":
        extra_files = request.FILES.getlist("extra_images")
        cover_file = request.FILES.get("image")

        if form.is_valid():
            with transaction.atomic():
                product = form.save(commit=False)
                product.store = store

                if cover_file:
                    uploaded_url = upload_to_imgbb(cover_file)
                    if uploaded_url:
                        product.image_url = uploaded_url
                    if product.image:
                        product.image.delete(save=False)

                product.save()

                for f in extra_files:
                    try:
                        if f.content_type.startswith("image/"):
                            img_url = upload_to_imgbb(f)
                            if img_url:
                                StoreImage.objects.create(
                                    store=store, image_url=img_url, name=product.name, price=product.price
                                )
                        elif f.content_type.startswith("video/"):
                            StoreImage.objects.create(store=store, file=f, name=product.name, price=product.price)
                    except Exception as e:
                        print(f"Failed to process {f.name}: {e}")
                        continue

            messages.success(request, "Product saved successfully!")
            return redirect("manage_store", slug=slug)

    old_files = StoreImage.objects.filter(store=store, name=item.name) if edit_mode and item else []
    items = Item.objects.filter(store=store)

    return render(request, "app/manage_store.html", {
        "store": store,
        "form": form,
        "edit_mode": edit_mode,
        "edit_item": item,
        "old_images": old_files,
        "items": items,
    })


@login_required
def delete_item(request, slug, item_id):
    store = get_object_or_404(Store, slug=slug, owner=request.user)
    item = get_object_or_404(Item, id=item_id, store=store)

    StoreImage.objects.filter(store=store, name=item.name).delete()
    item.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect("manage_store", slug=slug)


@login_required
def delete_extra_image(request, slug, image_id):
    store = get_object_or_404(Store, slug=slug, owner=request.user)
    img = get_object_or_404(StoreImage, id=image_id, store=store)
    img.delete()
    messages.success(request, "Extra image deleted successfully!")
    return redirect("manage_store", slug=slug)


def product_detail(request, id):
    product = get_object_or_404(Item, id=id)
    extra_files = StoreImage.objects.filter(store=product.store, name=product.name)
    product_media = ProductMedia.objects.filter(product=product)

    media_files = []

    # Main cover image
    if product.image_url:
        media_files.append({'type': 'image', 'url': product.image_url})

    # Extra StoreImages
    for f in extra_files:
        try:
            if f.image_url:
                media_files.append({'type': 'image', 'url': f.image_url})
            elif f.file and hasattr(f.file, 'url') and not f.file.url.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv')):
                media_files.append({'type': 'image', 'url': f.file.url})
        except Exception:
            continue

    # ProductMedia (YouTube + files)
    for m in product_media:
        if m.youtube_id:
            media_files.append({'type': 'youtube', 'id': m.youtube_id})
        elif m.is_video_file():
            media_files.append({'type': 'video', 'url': m.file.url})
        elif m.file:
            media_files.append({'type': 'image', 'url': m.file.url})

    context = {
        'product': product,
        'media_files': media_files,
    }
    return render(request, 'store/product_detail.html', context)


# -------------------------
# Like Item API
# -------------------------
def like_item(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

    if not request.user.is_authenticated:
        return JsonResponse({'redirect': '/register/'})

    liked_instance, created = ItemLike.objects.get_or_create(item=item, user=request.user)
    if not created:
        liked_instance.delete()
        liked_count = item.likes.count()
        liked_state = False
    else:
        liked_count = item.likes.count()
        liked_state = True

    return JsonResponse({
        'liked': liked_state,
        'likes': liked_count
    })


# -------------------------
# Add Product (ImgBB example)
# -------------------------
IMGBB_API_KEY = "c346e6e29bbc0340846deb957f6d510a"

def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES['image']

            url = "https://api.imgbb.com/1/upload"
            payload = {"key": IMGBB_API_KEY}
            files = {"image": image_file.read()}  # send binary

            response = requests.post(url, data=payload, files={"image": image_file})
            result = response.json()
            if "data" in result:
                image_url = result["data"]["url"]
                print("Uploaded URL:", image_url)
                return redirect("viewstore")
    else:
        form = ProductForm()

    return render(request, "add_product.html", {"form": form})
