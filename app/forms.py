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
# Custom Clearable File Input
class CustomClearableFileInput(ClearableFileInput):
    pass


class StoreForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'phone',
            'placeholder': 'e.g. +2347098865543'
        })
    )

    Bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Welcome to my Store',
            'rows': 3
        })
    )

    social = forms.URLField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. tiktok, instagram or any social media link'
        })
    )

    # --- NEW FIELDS ---
    dob = forms.DateField(
        widget=forms.TextInput(
            attrs={'placeholder': 'DD/MM/YYYY'}
        )
    )

    class Meta:
        model = Store
        fields = '__all__'

    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Store Address'
        })
    )

    business_type = forms.ChoiceField(
        required=False,
        choices=Store.BUSINESS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Store
        fields = ['brand_name', 'brand_logo', 'whatsapp_number', 'Bio', 'social', 'dob', 'address', 'business_type']  # slug not included
        widgets = {
            'brand_logo': CustomClearableFileInput(attrs={'class': 'form-control'}),
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
                    'placeholder': 'e.g. 1000'
                }
            ),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
        }


# Item Form
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['image', 'price', 'name']
        widgets = {
            'image': CustomClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'id': 'price-input',
                    'placeholder': 'e.g. 1000'
                }
            ),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Product Form
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
