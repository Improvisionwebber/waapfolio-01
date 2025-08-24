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
from .utils import upload_to_imgbb, upload_video_to_youtube
import requests
import base64
import tempfile
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
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "problem_solving.html", {'store': store})


def money(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "money.html", {'store': store})

def notifications(request):
    store = None
    if request.user.is_authenticated:
        store = Store.objects.filter(owner=request.user).first()
    return render(request, "notifications.html", {'store': store})

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
                messages.error(request, "Email already registered.")
                return redirect("register")

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


from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.templatetags.static import static
from django.db.models import Q

from .models import Store, StoreImage, Item, ItemView, ProductMedia

def view_store(request, slug):
    store = get_object_or_404(Store, slug=slug)
    items = Item.objects.filter(store=store)
    full_url = request.build_absolute_uri()
    whatsapp_link = f"https://wa.me/{store.whatsapp_number}"

    # --- session / unique views tracking (your existing logic) ---
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
    # ------------------------------------------------------------

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

    items_meta = []
    for item in items:
        product_path = reverse('product_detail', kwargs={'id': item.id})
        absolute_product_url = request.build_absolute_uri(product_path)

        items_meta.append({
            'item': item,
            'cover_url': get_cover_url(item),
            'product_url': absolute_product_url,
            'likes_count': item.likes.count() if hasattr(item, 'likes') else 0,
        })

    gallery_images = store.images.filter(item__isnull=True)

    # ✅ Step 1 logic: does this user already have a store?
    user_has_store = False
    if request.user.is_authenticated:
        user_has_store = Store.objects.filter(owner=request.user).exists()

    return render(request, 'store/view_store.html', {
        'store': store,
        'items_meta': items_meta,
        'full_url': full_url,
        'whatsapp_link': whatsapp_link,
        'gallery_images': gallery_images,
        'user_has_store': user_has_store,   # ✅ Pass it to template
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

                # Handle cover image
                if cover_file:
                    uploaded_url = upload_to_imgbb(cover_file)
                    if uploaded_url:
                        product.image_url = uploaded_url
                    if product.image:
                        product.image.delete(save=False)

                product.save()

                # Handle extra files (images + videos)
                for f in extra_files:
                    try:
                        if f.content_type.startswith("image/"):
                            img_url = upload_to_imgbb(f)
                            if img_url:
                                StoreImage.objects.create(
                                    store=store, image_url=img_url, name=product.name, price=product.price
                                )
                        elif f.content_type.startswith("video/"):
                            # Save temporarily if needed
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                                for chunk in f.chunks():
                                    tmp.write(chunk)
                                tmp_path = tmp.name

                            # Upload to YouTube
                            video_id, video_url = upload_video_to_youtube(
                                file_path=tmp_path,
                                title=product.name,
                                description=product.description or ""
                            )

                            # Create ProductMedia entry
                            ProductMedia.objects.create(
                                product=product,
                                youtube_id=video_id,
                                youtube_url=video_url,
                                label=product.name,
                                description=product.description or ""
                            )
                    except Exception as e:
                        print(f"Failed to process {f.name}: {e}")
                        continue

            messages.success(request, "Product saved successfully!")
            return redirect("manage_store", slug=slug)

    if edit_mode and item:
        old_files = list(StoreImage.objects.filter(store=store, name=item.name))
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
    return redirect("manage_store", slug=slug)
@login_required
def delete_extra_video(request, slug, video_id):
    store = get_object_or_404(Store, slug=slug, owner=request.user)
    video = get_object_or_404(ProductMedia, id=video_id, product__store=store)
    video.delete()
    messages.success(request, "Video deleted successfully!")
    return redirect("manage_store", slug=slug)


def product_detail(request, id):
    product = get_object_or_404(Item, id=id)
    extra_files = StoreImage.objects.filter(store=product.store, name=product.name)
    product_media = ProductMedia.objects.filter(product=product)
    store = product.store
    images, videos, youtube_videos = [], [], []

    # StoreImage extras
    for f in extra_files:
        try:
            if f.image_url:
                images.append(f)
            elif f.file:
                fname = f.file.name.lower()
                if fname.endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv')):
                    videos.append(f)         # has file
                else:
                    images.append(f)         # file image
        except Exception:
            continue

    # ProductMedia (files + youtube)
    for m in product_media:
        try:
            if m.youtube_id or m.youtube_url:
                youtube_videos.append(m)     # show via iframe
            elif m.is_video_file() and m.file:
                videos.append(m)             # file video
            elif m.file:
                images.append(m)             # file image
        except Exception:
            continue

    context = {
        'product': product,
        'images': images,
        'videos': videos,
        'youtube_videos': youtube_videos,
        'store': store,
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