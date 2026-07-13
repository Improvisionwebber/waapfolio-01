def generate_whatsapp_message(order):

    return f"""
Hello,

I have successfully paid for an order on Waapfolio.

Order ID:
{order.order_id}

Amount:
₦{order.amount}

Verify payment:
https://waapfolio.com/order/verify/{order.verification_token}
"""