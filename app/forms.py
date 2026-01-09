from django import forms
from django.forms.widgets import ClearableFileInput
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from .models import Store, StoreImage, Item
# from utils.email_service import send_email  # make sure the import is correct

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Comment
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "id": "id_username"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "id_email"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "id": "id_password1"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "id": "id_password2"}),
        }

# Custom Clearable File Input
class CustomClearableFileInput(ClearableFileInput):
    pass

class StoreForm(forms.ModelForm):

    whatsapp_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'phone',
            'placeholder': 'e.g. +2347098865543'
        })
    )

    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Short description of your brand',
            'rows': 3
        })
    )

    about = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell people about your brand',
            'rows': 4
        })
    )

    mission = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your brand mission or vision',
            'rows': 3
        })
    )

    brand_story = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your brand story or history',
            'rows': 4
        })
    )

    founder_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Founder name (optional)'
        })
    )

    telegram_username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '@telegram_username'
        })
    )

    background_color = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-control form-control-color',
            'style': 'height: 50px; padding: 0;'
        })
    )

    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Business address (optional)'
        })
    )

    business_type = forms.ChoiceField(
        required=False,
        choices=Store.BUSINESS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Store
        fields = [
            'brand_name',
            'brand_logo',
            'bio',
            'about',
            'mission',
            'founder_name',
            'brand_story',
            'order_system',
            'whatsapp_number',
            'telegram_username',
            'facebook_link',
            'instagram_link',
            'tiktok_link',
            'address',
            'business_type',
            'background_color',
        ]

        widgets = {
            'brand_logo': CustomClearableFileInput(
                attrs={'class': 'form-control'}
            ),
            'facebook_link': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'Facebook page link'}
            ),
            'instagram_link': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'Instagram profile link'}
            ),
            'tiktok_link': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'TikTok profile link'}
            ),
            'order_system': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }




class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Write your comment..."
            })
        }


# Store Image Form
class StoreImageForm(forms.ModelForm):
    class Meta:
        model = StoreImage
        fields = ['image', 'price', 'name']
        widgets = {
            'image': ClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'id': 'price-input',
                    'placeholder': 'Enter price (Optional)',
                    'step': '0.01',   # allows decimals like 1000.50
                    'min': '0',       # no negative prices
                    'inputmode': 'decimal',  # mobile keyboard shows numbers
                }
            ),

            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
        }

import re
from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['image', 'price', 'name', 'description', 'order_system', 'facebook_link', 'tiktok_link', 'depop_link']
        widgets = {
            'image': CustomClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1000'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product details...'}),
            'order_system': forms.Select(attrs={'class': 'form-control'}),
            'facebook_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Facebook link'}),
            'tiktok_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'TikTok link'}),
            'depop_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Depop link'}),
        }
    def clean_price(self):
        raw_price = str(self.data.get("price", "")).strip()
        if not raw_price:
            return None  # <-- allow empty
        clean_price = re.sub(r"[^\d.]", "", raw_price)
        if not clean_price:
            return None  # optional: treat as empty
        return float(clean_price)




class ProductForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['image', 'price', 'description', 'name']
        widgets = {
            'image': CustomClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'id': 'price-input',
                    'placeholder': 'e.g. 1000'
                }
            ),
            'description': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'id': 'description-input',
                    'placeholder': 'e.g. Red Size 45 Colors available: Red, blue, etc. Chocolate, Milky. Delivery available in ....'
                }
            ),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_price(self):
        raw_price = str(self.data.get("price", "")).strip()
        if not raw_price:
            return None  # <-- allow empty
        clean_price = re.sub(r"[^\d.]", "", raw_price)
        if not clean_price:
            return None  # optional: treat as empty
        return float(clean_price)


# Custom Password Reset Form using Brevo
# class BrevoPasswordResetForm(PasswordResetForm):
#     def send_mail(
#         self,
#         subject_template_name,
#         email_template_name,
#         context,
#         from_email,
#         to_email,
#         html_email_template_name=None
#     ):
#         subject = render_to_string(subject_template_name, context).strip()
#         html_content = render_to_string(email_template_name, context)
#         send_email(to_email, subject, html_content)
