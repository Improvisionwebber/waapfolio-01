from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from app.models import (
    Wallet,
    WalletTransaction,
    SellerTrust,
    AuditLog,
)


@transaction.atomic
def process_paid_order(order):

    wallet, created = Wallet.objects.get_or_create(
        user=order.seller
    )

    trust, created = SellerTrust.objects.get_or_create(
        user=order.seller
    )

    if trust.instant_withdrawal:

        wallet.available_balance += order.seller_amount

        order.status = "AVAILABLE_FOR_WITHDRAWAL"

        release_type = "instant"

    else:

        wallet.pending_balance += order.seller_amount

        order.status = "ON_HOLD"

        order.hold_until = (
            timezone.now() +
            timedelta(hours=72)
        )

        release_type = "hold"

    wallet.lifetime_earnings += order.seller_amount

    wallet.save()

    order.save()

    WalletTransaction.objects.create(

        wallet=wallet,

        transaction_type="sale",

        amount=order.seller_amount,

        description=f"Payment received for Order {order.order_id}",

        reference=order.paystack_reference,

    )

    AuditLog.objects.create(

        user=order.seller,

        action="Order Paid",

        object_type="Order",

        object_id=str(order.id),

        metadata={

            "order_id": order.order_id,

            "status": order.status,

            "amount": str(order.amount),

            "seller_amount": str(order.seller_amount),

            "release": release_type,

        }

    )

    return release_type


@transaction.atomic
def accept_order(order):

    if order.status != "PAID":
        raise Exception(
            "This order cannot be accepted."
        )

    order.status = "ACCEPTED"
    order.accepted_at = timezone.now()
    order.save()

    AuditLog.objects.create(

        user=order.seller,

        action="Order Accepted",

        object_type="Order",

        object_id=str(order.id),

        metadata={

            "order_id": order.order_id,

        }

    )

    trust = SellerTrust.objects.get(
        user=order.seller
    )

    if trust.instant_withdrawal:
        return "instant"

    return "hold"


@transaction.atomic
def release_held_funds(order):

    if order.status != "ON_HOLD":
        return

    wallet = Wallet.objects.get(
        user=order.seller
    )

    wallet.pending_balance -= order.seller_amount

    wallet.available_balance += order.seller_amount

    wallet.save()

    order.status = "AVAILABLE_FOR_WITHDRAWAL"

    order.save()

    WalletTransaction.objects.create(

        wallet=wallet,

        transaction_type="hold_release",

        amount=order.seller_amount,

        description=f"Hold released for Order {order.order_id}",

        reference=order.paystack_reference,

    )

    AuditLog.objects.create(

        user=order.seller,

        action="Funds Released",

        object_type="Order",

        object_id=str(order.id),

        metadata={

            "order_id": order.order_id,

        }

    )