from django.urls import path, include   
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path("account/", include("django.contrib.auth.urls")),
    path(
        'account/password-reset/',
        auth_views.PasswordResetView.as_view(
            html_email_template_name='registration/password_reset_email.html'  # 👈 This line only
        ),
        name='password_reset',
    ),
    # -------------------------
    # Public Pages
    # -------------------------
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('problem-solving/', views.problem_solving, name='problem_solving'),
    path('money/', views.money, name='money'),
    path('create-tutorial/', views.create_tutorial, name='create_tutorial'),
    path('share-tutorial/', views.share_tutorial, name='share_tutorial'),
    path('faqs/', views.faqs, name='faqs'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path('security-settings/', views.security_settings, name='security_settings'),
    path('account-information/', views.account_information, name='account_information'),
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("account/login/", auth_views.LoginView.as_view(), name="login"),
    # -------------------------
    # Authentication / Registration
    # -------------------------
    path('register/', views.register, name='register'),
    path("search/products/", views.product_search, name="product_search"),
    path("youtube-token/", views.youtube_token, name="youtube-token"),
    # -------------------------
    # Store
    # -------------------------
    path('store/create/', views.create_store, name='create_store'),
    path('store/create/<int:id>/', views.create_store, name='edit_store'),
    path('store/<slug:slug>/', views.view_store, name='view_store'),
    path('store/manage/<slug:slug>/', views.manage_store, name='manage_store'),
    path('store/manage/<slug:slug>/<int:item_id>/', views.manage_store, name='edit_item'),
    path('store/delete-item/<slug:slug>/<int:item_id>/', views.delete_item, name='delete_item'),
    path('store/delete-extra-image/<slug:slug>/<int:image_id>/', views.delete_extra_image, name='delete_extra_image'),
    path("store/<slug:slug>/delete-video/<int:video_id>/", views.delete_extra_video, name="delete_extra_video"),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('like-item/<int:item_id>/', views.like_item, name='like_item'),
    path('add-product/', views.add_product, name='add_product'),
    path("report/<slug:slug>/", views.report_store, name="report_page"),
    path('delete-account/', views.delete_account, name='delete_account'),
    path("search/", views.store_search, name="store_search"),
    path('notifications/', views.notifications_view, name='notifications'),
    path("record-order/<int:store_id>/", views.record_order, name="record_order"),
    path("marketplace/", views.marketplace_view, name="marketplace"),
    ]
handler404 = 'app.views.custom_404'
handler500 = 'app.views.custom_500'
handler403 = 'app.views.custom_403'
handler400 = 'app.views.custom_400'


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)