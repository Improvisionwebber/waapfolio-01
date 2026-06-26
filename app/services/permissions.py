from functools import wraps
from django.http import JsonResponse

from ..models import Subscription


# =========================
# 1. CORE SUBSCRIPTION SAFE LAYER
# =========================

def get_subscription(user):
    """
    ALWAYS returns a Subscription object (never None)
    Prevents system breaking
    """
    sub, _ = Subscription.objects.get_or_create(user=user)
    return sub


def get_user_plan(user):
    """
    Returns: 'free' or 'premium'
    """
    sub = get_subscription(user)

    if not sub.is_active:
        return "free"

    return sub.plan


def is_premium(user):
    """
    True only if user has active premium plan
    """
    sub = get_subscription(user)
    return sub.plan == "premium" and sub.is_active


# =========================
# 2. PLAN LIMITS ENGINE
# =========================

def get_plan_limits(user):
    """
    Single source of truth for ALL business rules
    """

    plan = get_user_plan(user)

    if plan == "free":
        return {
            # limits
            "max_templates": 2,
            "max_stores": 1,

            # features
            "can_use_custom_domain": False,
            "can_use_subdomain": False,

            # money rules
            "commission_rate": 0.10,

            # UI access
            "can_access_premium_templates": False,
        }

    if plan == "premium":
        return {
            "max_templates": None,
            "max_stores": None,

            "can_use_custom_domain": True,
            "can_use_subdomain": True,

            "commission_rate": 0.05,

            "can_access_premium_templates": True,
        }

    # fallback safety
    return {
        "max_templates": 2,
        "max_stores": 1,
        "can_use_custom_domain": False,
        "can_use_subdomain": False,
        "commission_rate": 0.10,
        "can_access_premium_templates": False,
    }


# =========================
# 3. FEATURE HELPERS (CLEAN API)
# =========================

def can_use_custom_domain(user):
    return get_plan_limits(user)["can_use_custom_domain"]


def can_use_subdomain(user):
    return get_plan_limits(user)["can_use_subdomain"]


def get_commission_rate(user):
    return get_plan_limits(user)["commission_rate"]


def max_templates_allowed(user):
    return get_plan_limits(user)["max_templates"]


def max_stores_allowed(user):
    return get_plan_limits(user)["max_stores"]


# =========================
# 4. SAFETY CHECKS (USED IN VIEWS)
# =========================

def check_template_limit(user):
    limit = max_templates_allowed(user)
    if limit is None:
        return True
    current = user.stores.count()
    return current < limit


def check_store_limit(user, current_count):
    limit = max_stores_allowed(user)

    if limit is None:
        return True

    return current_count < limit


# =========================
# 5. DECORATORS (PROTECTION LAYER)
# =========================

def premium_required(view_func):
    """
    Blocks non-premium users
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_premium(request.user):
            return JsonResponse({
                "error": "Premium plan required",
                "upgrade": True
            }, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper


def feature_required(feature_check_func, error_message="Feature not allowed"):
    """
    Generic feature protection decorator
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not feature_check_func(request.user):
                return JsonResponse({
                    "error": error_message
                }, status=403)

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator