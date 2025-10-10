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
import tempfile
from django.http import HttpResponse
import logging
from utils.validators import validate_file_size
logger = logging.getLogger(__name__)
from .models import (
    Store, StoreImage, Item, ItemView, EmailOTP, ProductMedia, ItemLike, Comment
)
from .forms import (
    StoreForm, StoreImageForm, ProductForm, CommentForm
)
from .utils import upload_to_imgbb, upload_to_youtube
from utils.email_service import send_email
from .models import Notification
from django.conf import settings
from rapidfuzz import process

from django.urls import reverse
from django.templatetags.static import static
from django.db.models import Q
import re

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
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'store': store,
        'unread_count': unread_count
    }
    return render(request, "profile.html", context)


def problem_solving(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "problem_solving.html", {'store': store})


def money(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "money.html", {'store': store})

# def notifications(request):
#     store = None
#     if request.user.is_authenticated:
#         store = Store.objects.filter(owner=request.user).first()
#     return render(request, "notifications.html", {'store': store})

def create_tutorial(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "create_tutorial.html", {'store': store})


def share_tutorial(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "share_tutorial.html", {'store': store})


def faqs(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "faq.html", {'store': store})


def contact(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "contact.html", {'store': store})


def privacy(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "privacy_policy.html", {'store': store})


def security_settings(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, 'security_settings.html', {'store': store})


@login_required
def account_information(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    user = request.user
    context = {
        'user': user,
        'store': store
    }
    return render(request, 'account_information.html', context)


# -------------------------
# Registration / OTP
# -------------------------
# -------------------------
# Registration / OTP
# -------------------------
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import random
from .util import send_otp_email   # ✅ use the Brevo API sender
from .forms import UserRegistrationForm

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                form.add_error("email", "Email already registered.")  # attach error to form
            else:
                # Generate OTP
                otp = random.randint(100000, 999999)

                # Store temporarily in session
                request.session["otp"] = str(otp)
                request.session["email"] = email
                request.session["username"] = username
                request.session["password"] = make_password(password)

                # Send OTP via Brevo API
                send_otp_email(email, otp)

                messages.info(request, "An OTP has been sent to your email.")
                return redirect("verify_otp")
        # If form is invalid, it will automatically go to render at the end and show errors
    else:
        form = UserRegistrationForm()

    return render(request, "register.html", {"form": form})

def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")

        if not session_otp:
            return render(request, "verify_otp.html", {"error": "Session expired. Please register again."})

        if entered_otp == session_otp:
            # Create user
            user = User.objects.create(
                username=request.session["username"],
                email=request.session["email"],
                password=request.session["password"],  # already hashed
            )
            user.save()

            # Clear session data after success
            request.session.flush()

            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
        else:
            return render(request, "verify_otp.html", {"error": "Invalid OTP"})

    return render(request, "verify_otp.html")




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
        
        # ---- Validate brand logo size ----
        logo_file = request.FILES.get('brand_logo')
        if logo_file:
            try:
                validate_file_size(logo_file, 32)  # <-- limit 32MB
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'store/create_store.html', {'form': form})

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
                    'key': settings.IMGBB_API_KEY,
                    'image': base64.b64encode(logo_file.read()).decode('utf-8')
                }
                response = requests.post(url, data=payload, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get('success'):
                    store.brand_logo = data['data']['url']
                else:
                    messages.warning(
                        request,
                        f"Logo upload failed: {data.get('error', 'Unknown error')}. Default logo will be used."
                    )
            except requests.exceptions.RequestException as e:
                messages.warning(
                    request,
                    f"Logo upload failed: {str(e)}. Default logo will be used."
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"Unexpected error during logo upload: {str(e)}. Default logo will be used."
                )

        # Save store even if logo upload fails
        store.save()
        messages.success(request, "Store saved successfully!")
        return redirect(store.get_absolute_url())

    return render(request, 'store/create_store.html', {'form': form})



# def view_store(request, slug):
#     store = get_object_or_404(Store, slug=slug)
#     items = Item.objects.filter(store=store)

#     # -------------------------------
#     # Search logic
#     # -------------------------------
#     query = request.GET.get("q")
#     if query:
#         items = items.filter(
#             Q(name__icontains=query) | Q(description__icontains=query)
#         )

#     full_url = request.build_absolute_uri()
#     whatsapp_link = f"https://wa.me/{store.whatsapp_number}"

#     # -------------------------------
#     # Session / unique views tracking
#     # -------------------------------
#     session_key = request.session.session_key
#     if not session_key:
#         request.session.create()
#         session_key = request.session.session_key

#     store_viewed_key = f"viewed_store_{store.id}"
#     if not request.session.get(store_viewed_key) and request.user != store.owner:
#         store.total_views += 1
#         store.save()
#         viewer_name = request.user.username if request.user.is_authenticated else "Someone"
#         Notification.objects.create(
#             user=store.owner,
#             message=f"{viewer_name} just viewed your store!",
#             link=request.build_absolute_uri()
#         )

#         request.session[store_viewed_key] = True

#     for item in items:
#         view_filter = Q(session_key=session_key)
#         if request.user.is_authenticated:
#             view_filter |= Q(user=request.user)

#         if not ItemView.objects.filter(item=item).filter(view_filter).exists():
#             item.views += 1
#             item.save()
#             ItemView.objects.create(
#                 item=item,
#                 user=request.user if request.user.is_authenticated else None,
#                 session_key=session_key
#             )

#     # -------------------------------
#     # Helper: get item cover image
#     # -------------------------------
#     def get_cover_url(item):
#         if item.image_url:
#             return item.image_url
#         if item.image:
#             try:
#                 return item.image.url
#             except Exception:
#                 pass
#         extra = StoreImage.objects.filter(store=store, name=item.name).first()
#         if extra:
#             if extra.image_url:
#                 return extra.image_url
#             if extra.file:
#                 try:
#                     return extra.file.url
#                 except Exception:
#                     pass
#         pm = ProductMedia.objects.filter(product=item).first()
#         if pm:
#             if pm.file:
#                 return pm.file.url
#             if pm.youtube_id:
#                 return f"https://img.youtube.com/vi/{pm.youtube_id}/hqdefault.jpg"
#         return static('images/no-image.png')

#     # -------------------------------
#     # Build items meta
#     # -------------------------------
#     items_meta = []
#     for item in items:
#         product_path = reverse('product_detail', kwargs={'id': item.id})
#         absolute_product_url = request.build_absolute_uri(product_path)
#         items_meta.append({
#             'item': item,
#             'cover_url': get_cover_url(item),
#             'product_url': absolute_product_url,
#             'likes_count': item.likes.count() if hasattr(item, 'likes') else 0,
#             'user_liked': request.user.is_authenticated and item.likes.filter(id=request.user.id).exists(),
#         })

#     gallery_images = store.images.filter(item__isnull=True)
#     user_has_store = request.user.is_authenticated and Store.objects.filter(owner=request.user).exists()

#     return render(request, 'store/view_store.html', {
#         'store': store,
#         'items_meta': items_meta,
#         'full_url': full_url,
#         'whatsapp_link': whatsapp_link,
#         'gallery_images': gallery_images,
#         'user_has_store': user_has_store,
#     })
def view_store(request, slug):
    store = get_object_or_404(Store, slug=slug)
    items = Item.objects.filter(store=store)

    # -------------------------------
    # Search logic
    # -------------------------------
    query = request.GET.get("q")
    if query:
        # ✅ grab all product names in current queryset (so we don’t search whole DB if items already filtered by store, etc.)
        all_names = list(items.values_list("name", flat=True))

        if all_names:
            # ✅ fuzzy match with threshold
            matches = process.extract(query, all_names, limit=15, score_cutoff=60)
            matched_names = [m[0] for m in matches]

            # ✅ filter items by those matches
            items = items.filter(name__in=matched_names)

        # ✅ fallback if no fuzzy match found
        if not items.exists():
            items = items.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )


    full_url = request.build_absolute_uri()
    whatsapp_link = f"https://wa.me/{store.whatsapp_number}"

    # -------------------------------
    # Session / unique views tracking
    # -------------------------------
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    store_viewed_key = f"viewed_store_{store.id}"
    if not request.session.get(store_viewed_key) and request.user != store.owner:
        store.total_views += 1
        store.save()
        viewer_name = request.user.username if request.user.is_authenticated else "Someone"
        Notification.objects.create(
            user=store.owner,
            message=f"{viewer_name} just viewed your store!",
            link=request.build_absolute_uri()
        )

        request.session[store_viewed_key] = True

    for item in items:
        view_filter = Q(session_key=session_key)
        if request.user.is_authenticated:
            view_filter |= Q(user=request.user)

        if not ItemView.objects.filter(item=item).filter(view_filter).exists():
            item.views += 1
            item.save()
            ItemView.objects.create(
                item=item,
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key
            )

    # -------------------------------
    # Helper: get item cover image
    # -------------------------------
    def get_cover_url(item):
        if item.image_url:
            return item.image_url
        if item.image:
            try:
                return item.image.url
            except Exception:
                pass
        extra = StoreImage.objects.filter(store=store, name=item.name).first()
        if extra:
            if extra.image_url:
                return extra.image_url
            if extra.file:
                try:
                    return extra.file.url
                except Exception:
                    pass
        pm = ProductMedia.objects.filter(product=item).first()
        if pm:
            if pm.file:
                return pm.file.url
            if pm.youtube_id:
                return f"https://img.youtube.com/vi/{pm.youtube_id}/hqdefault.jpg"
        return static('images/no-image.png')

    # -------------------------------
    # Build items meta
    # -------------------------------
    items_meta = []
    for item in items:
        product_path = reverse('product_detail', kwargs={'slug': item.slug})  # ✅ use slug instead of id
        absolute_product_url = request.build_absolute_uri(product_path)
        items_meta.append({
            'item': item,
            'cover_url': get_cover_url(item),
            'product_url': absolute_product_url,
            'likes_count': item.likes.count() if hasattr(item, 'likes') else 0,
            'user_liked': request.user.is_authenticated and item.likes.filter(id=request.user.id).exists(),
        })

    gallery_images = store.images.filter(item__isnull=True)
    user_has_store = request.user.is_authenticated and Store.objects.filter(owner=request.user).exists()

    # -------------------------------
    # Determine OG image for sharing
    # -------------------------------
    if items_meta:
        og_image = request.build_absolute_uri(items_meta[0]['cover_url'])
    elif store.brand_logo:
        og_image = request.build_absolute_uri(store.brand_logo.url)
    else:
        og_image = request.build_absolute_uri(static('images/logo.png'))

    return render(request, 'store/view_store.html', {
        'store': store,
        'items_meta': items_meta,
        'full_url': full_url,
        'whatsapp_link': whatsapp_link,
        'gallery_images': gallery_images,
        'user_has_store': user_has_store,
        'og_image': og_image,  # <-- added this
    })

# -------------------------
# Product Management (Images handled here, Videos handled via frontend → YouTube)
# -------------------------
import tempfile
import os
from decimal import Decimal

@login_required
def manage_store(request, slug, item_id=None):
    try:
        store = get_object_or_404(Store, slug=slug, owner=request.user)

        if item_id:
            item = get_object_or_404(Item, id=item_id, store=store)
            form = ProductForm(request.POST or None, request.FILES or None, instance=item)
            edit_mode = True
        else:
            item = None
            form = ProductForm(request.POST or None, request.FILES or None)
            edit_mode = False

        extra_files = request.FILES.getlist("extra_images")
        cover_file = request.FILES.get("image")

        product = None  # Ensure product exists before use

        if request.method == "POST":
            try:
                if cover_file:
                    validate_file_size(cover_file, 32)
                for f in extra_files:
                    if f.content_type.startswith("image/"):
                        validate_file_size(f, 32)
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, "app/manage_store.html", {
                    "store": store,
                    "form": form,
                    "edit_mode": edit_mode,
                    "edit_item": item,
                    "items": Item.objects.filter(store=store),
                })

            if form.is_valid():
                with transaction.atomic():
                    product = form.save(commit=False)
                    product.store = store

                    # ---- Price (clean digits and convert to Decimal with .00) ----
                    raw_price = request.POST.get("price", "")
                    clean_price = re.sub(r"[^\d.]", "", raw_price)
                    if not clean_price:
                        clean_price = "0.00"
                    elif "." not in clean_price:
                        clean_price += ".00"
                    product.price = Decimal(clean_price)

                    # ---- Currency ----
                    product.currency = request.POST.get("currency", "₦")

                    # ---- Cover Image ----
                    if cover_file:
                        try:
                            uploaded_url = upload_to_imgbb(cover_file)
                            if uploaded_url:
                                product.image_url = uploaded_url
                            if product.image:
                                product.image.delete(save=False)
                        except Exception as e:
                            messages.warning(request, f"Cover image upload failed: {e}")
                            logger.warning(f"Cover image upload failed: {e}")

                    product.save()
            else:
                print("Form errors:", form.errors)
                messages.error(request, form.errors)

            # ✅ Only process files if product exists
            if product:
                # ---- Extra Images ----
                for f in extra_files:
                    if f.content_type.startswith("image/"):
                        try:
                            img_url = upload_to_imgbb(f)
                            if img_url:
                                StoreImage.objects.create(
                                    store=store,
                                    item=product,
                                    image_url=img_url,
                                    name=product.name,
                                    price=product.price
                                )
                        except Exception as e:
                            messages.warning(request, f"Failed to process {getattr(f, 'name', 'file')}: {e}")
                            logger.warning(f"Failed to process {getattr(f, 'name', 'file')}: {e}")
                            continue

                # ---- Video Uploads ----
                video_files = [f for f in extra_files if f.content_type.startswith("video/")]

                for video in video_files:
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.name)[1]) as tmp_file:
                            for chunk in video.chunks():
                                tmp_file.write(chunk)
                            tmp_file_path = tmp_file.name

                        response = upload_to_youtube(
                            tmp_file_path,
                            title=product.name,
                            description=product.description or ""
                        )

                        os.remove(tmp_file_path)

                        youtube_id = response.get("id")
                        youtube_url = f"https://www.youtube.com/watch?v={youtube_id}" if youtube_id else None

                        ProductMedia.objects.create(
                            product=product,
                            youtube_id=youtube_id,
                            youtube_url=youtube_url,
                            label=product.name,
                            description=product.description or ""
                        )

                    except Exception as e:
                        messages.warning(request, f"Failed to upload video {getattr(video, 'name', '')}: {e}")
                        logger.warning(f"Failed to upload video {getattr(video, 'name', '')}: {e}")
                        continue

            messages.success(request, "Product saved successfully!")
            return redirect("manage_store", slug=slug)

        # ---- Edit Form Old Files ----
        if edit_mode and item:
            old_files = list(StoreImage.objects.filter(item=item))
            old_files += list(ProductMedia.objects.filter(product=item))
        else:
            old_files = []

        items = Item.objects.filter(store=store)

        return render(request, "app/manage_store.html", {
            "store": store,
            "form": form,
            "edit_mode": edit_mode,
            "edit_item": item,
            "old_images": old_files,
            "items": items,
        })

    except (ConnectionResetError, OSError) as e:
        logger.error(f"Network error in manage_store: {e}")
        return HttpResponse(
            "<h2>Connection lost</h2><p>Your network seems unstable. Please try again.</p>",
            status=400
        )


@login_required
def delete_item(request, slug, item_id):
    store = get_object_or_404(Store, slug=slug, owner=request.user)
    item = get_object_or_404(Item, id=item_id, store=store)

    StoreImage.objects.filter(store=store, name=item.name).delete()
    ProductMedia.objects.filter(product=item).delete()
    item.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect("manage_store", slug=slug)


@login_required
def delete_extra_image(request, slug, image_id):
    store = get_object_or_404(Store, slug=slug, owner=request.user)
    img = get_object_or_404(StoreImage, id=image_id, store=store)
    img.delete()
    messages.success(request, "Extra image deleted successfully!")
    return redirect(request.META.get("HTTP_REFERER", "manage_store"), slug=slug)


@login_required
def delete_extra_video(request, slug, video_id):
    store = get_object_or_404(Store, slug=slug, owner=request.user)
    video = get_object_or_404(ProductMedia, id=video_id, product__store=store)
    video.delete()
    messages.success(request, "Video deleted successfully!")
    return redirect(request.META.get("HTTP_REFERER", "manage_store"), slug=slug)

def product_detail(request, slug):
    product = get_object_or_404(Item, slug=slug)
    extra_files = StoreImage.objects.filter(store=product.store, name=product.name)
    product_media = ProductMedia.objects.filter(product=product)
    store = product.store
    images, videos, youtube_videos = [], [], []

    # Handle comments
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            comment.user = request.user
            comment.save()

            # ✅ Create notification for store owner (avoid self-notification)
            if request.user != store.owner:
                Notification.objects.create(
                    user=store.owner,
                    message=f"{request.user.username} commented on your product: {product.name}",
                    link=request.build_absolute_uri(product.get_absolute_url())
                )

            messages.success(request, "Your comment has been posted!")
            return redirect("product_detail", slug=product.slug)
    else:
        form = CommentForm()

    comments = product.comments.all().order_by("-created_at")  # newest first

    # StoreImage extras
    for f in extra_files:
        try:
            if f.image_url:
                images.append(f)
            elif f.file:
                fname = f.file.name.lower()
                if fname.endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv')):
                    videos.append(f)
                else:
                    images.append(f)
        except Exception:
            continue

    # ProductMedia (files + youtube)
    for m in product_media:
        try:
            if m.youtube_id or m.youtube_url:
                youtube_videos.append(m)
            elif m.is_video_file() and m.file:
                videos.append(m)
            elif m.file:
                images.append(m)
        except Exception:
            continue

    context = {
        'product': product,
        'images': images,
        'videos': videos,
        'youtube_videos': youtube_videos,
        'store': store,
        'form': form,
        'comments': comments,
    }
    return render(request, 'store/product_detail.html', context)




# -------------------------
# Like Item API
# -------------------------
@login_required
def like_item(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

    # Toggle like
    liked_instance, created = ItemLike.objects.get_or_create(item=item, user=request.user)
    if not created:
        liked_instance.delete()
        liked_state = False
    else:
        liked_state = True

        # ✅ Create notification if liked
        if request.user != item.store.owner:  # don't notify yourself
            Notification.objects.create(
                user=item.store.owner,
                message=f"{request.user.username} liked your product: {item.name}",
                link=request.build_absolute_uri(item.get_absolute_url())
            )

    likes_count = item.likes.count() if hasattr(item, 'likes') else 0

    return JsonResponse({
        'liked': liked_state,
        'likes': likes_count
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
from .models import Report

def report_store(request, slug):
    store = get_object_or_404(Store, slug=slug)

    if request.method == "POST":
        reason_choice = request.POST.get("reason_choice", "")
        reason_text = request.POST.get("reason_text", "")
        reason = reason_choice
        if reason_text:
            reason += f" - {reason_text}"

        Report.objects.create(
            store=store,
            reported_by=request.user if request.user.is_authenticated else None,
            reason=reason
        )
        return render(request, "report_success.html", {"store": store})

    return render(request, "report_form.html", {"store": store})
@login_required
def delete_account(request):
    if request.method == "POST":
        # Check if user confirmed deletion
        if "confirm" in request.POST:
            user = request.user
            try:
                with transaction.atomic():
                    # Delete related objects here if needed
                    user.delete()
                messages.success(request, "Your account and all data have been deleted.")
            except Exception as e:
                messages.error(request, f"Error deleting account: {e}")
            
            logout(request)
            return redirect("home")
        else:
            # User canceled deletion
            messages.info(request, "Account deletion canceled.")
            return redirect("profile")

    # GET request: show confirmation page
    return render(request, "confirm_delete_account.html")
# notifications/views.py
@login_required
def notifications_view(request):
    store = Store.objects.filter(owner=request.user).first()
    notifications = request.user.notifications.order_by("-created_at")

    # ✅ Mark all unread as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, "notifications.html", {
        "store": store,
        "notifications": notifications
    })
from django.http import JsonResponse
from .utils import get_youtube_access_token

@login_required
def youtube_token(request):
    """
    API endpoint to fetch a fresh YouTube access token for direct uploads.
    """
    try:
        token = get_youtube_access_token()
        return JsonResponse({"access_token": token})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
def csrf_failure(request, reason=""):
    # Redirect user to login page whenever CSRF fails
    return redirect('login') 
from django.templatetags.static import static
from django.conf import settings
from urllib.parse import urljoin

def _get_store_logo_url(request, store):
    """
    Return a usable absolute URL for the store's logo:
    - if brand_logo is an ImageField -> use .url
    - if brand_logo is a string URL -> use it directly
    - elif brand_logo_url -> use that
    - else -> default static image
    """
    # 1) brand_logo as ImageField
    if getattr(store, "brand_logo", None):
        # If it's an ImageFieldFile object it will have .url
        try:
            url = store.brand_logo.url
            # make absolute
            if url.startswith("http"):
                return url
            return request.build_absolute_uri(url)
        except Exception:
            # brand_logo might be a plain string URL stored by your imgbb logic
            try:
                if isinstance(store.brand_logo, str) and store.brand_logo.startswith("http"):
                    return store.brand_logo
            except Exception:
                pass

    # 2) explicit brand_logo_url field (external)
    if getattr(store, "brand_logo_url", None):
        if store.brand_logo_url.startswith("http"):
            return store.brand_logo_url
        return request.build_absolute_uri(store.brand_logo_url)

    # 3) fallback static image
    return request.build_absolute_uri(static("images/logo.png"))


def store_search(request):
    query = request.GET.get("q", "").strip()
    qs = Store.objects.filter(brand_name__icontains=query) if query else Store.objects.none()

    # Convert queryset into list and attach computed logo_url
    stores = []
    for s in qs:
        # attach a safe property the template can use
        s.logo_url = _get_store_logo_url(request, s)
        stores.append(s)

    return render(request, "store_search.html", {"stores": stores, "query": query})
from django.shortcuts import render
from django.db.models import Q
from .models import Store, Item


def store_search(request):
    query = request.GET.get("q", "")
    stores = []
    if query:
        all_names = list(Store.objects.values_list("brand_name", flat=True))

        if all_names:
            # Only keep matches with score >= 60
            matches = process.extract(query, all_names, limit=10, score_cutoff=60)

            # Extract names only
            matched_names = [m[0] for m in matches]

            # Query only those stores
            stores = Store.objects.filter(brand_name__in=matched_names)

        # fallback to icontains if fuzzy gave nothing
        if not stores.exists():
            stores = Store.objects.filter(
                Q(brand_name__icontains=query) | Q(Bio__icontains=query)
            )

    return render(request, "store_search.html", {
        "query": query,
        "stores": stores
    })


def product_search(request):
    query = request.GET.get("q", "")
    results = []
    if query:
        # ✅ grab all product names
        all_names = list(Item.objects.values_list("name", flat=True))

        if all_names:
            # ✅ fuzzy match with score threshold
            matches = process.extract(query, all_names, limit=15, score_cutoff=60)

            # ✅ get just the matched names
            matched_names = [m[0] for m in matches]

            # ✅ query DB for those items (and pull related store in one go)
            results = Item.objects.filter(name__in=matched_names).select_related("store")

        # ✅ fallback if no fuzzy result
        if not results:
            results = Item.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).select_related("store")

    return render(request, "search/product_results.html", {
        "query": query,
        "results": results
    })
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def record_order(request, store_id):
    if request.method == "POST":
        try:
            store = Store.objects.get(id=store_id)
            store.total_orders += 1
            store.save()
            return JsonResponse({"success": True, "total_orders": store.total_orders})
        except Store.DoesNotExist:
            return JsonResponse({"success": False, "error": "Store not found"}, status=404)
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
def marketplace_view(request):
    query = request.GET.get("q", "").strip()

    # ✅ Get all active products
    products = Item.objects.select_related("store").order_by("-created_at")

    # ✅ If search query exists, filter across multiple fields
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(store__brand_name__icontains=query)
        ).distinct()

    # ✅ AJAX response for live search
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        data = []
        for p in products[:12]:  # limit for speed
            data.append({
                "id": p.id,
                "name": p.name,
                "price": f"{p.price} {p.currency}",
                "image": p.image.url if p.image else "/static/images/placeholder.png",
                "store_name": p.store.brand_name if p.store else "Unknown Store",
                "product_url": p.get_absolute_url(),
                "store_url": p.store.get_absolute_url() if p.store else "#",
            })
        return JsonResponse({"results": data})

    # ✅ Normal render for full marketplace
    return render(request, "marketplace.html", {
        "results": products,
        "query": query,
    })