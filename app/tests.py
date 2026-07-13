from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from app.context_processors import cart
from app.models import Cart


class CartContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_cart_context_processor_uses_session_based_cart_for_authenticated_user(self):
        request = self.factory.get("/")
        request.user = self.user

        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(request)
        request.session.save()

        context = cart(request)

        self.assertIn("cart", context)
        self.assertIn("cart_count", context)
        self.assertEqual(context["cart_count"], 0)
        self.assertEqual(
            Cart.objects.filter(customer_session=request.session.session_key).count(),
            1,
        )
