import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(payment):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",

        line_items=[
            {
                "price_data": {
                    "currency": payment.currency.lower(),
                    "product_data": {
                        "name": "Immigration Consultation",
                    },
                    "unit_amount": int(payment.amount * 100),
                },
                "quantity": 1,
            }
        ],

        success_url="https://immigration-booking-system.onrender.com/payment-success/",
        cancel_url="https://immigration-booking-system.onrender.com/payment-cancel/",
    )

    return session