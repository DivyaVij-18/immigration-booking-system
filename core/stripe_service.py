import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(payment):

    booking = payment.booking

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

        metadata={
            "booking_id": str(booking.pk),
        },

        success_url=(
            "https://immigration-booking-system.onrender.com/"
            "payment/success/?session_id={CHECKOUT_SESSION_ID}"
        ),

        cancel_url=(
            "https://immigration-booking-system.onrender.com/"
            "payment/cancel/"
        ),
    )

    return session