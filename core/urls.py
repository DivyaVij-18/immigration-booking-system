from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('offices/', views.offices, name='offices'),
    path("crm/", views.crm_dashboard, name="crm_dashboard"),
    path('book/', views.book_consultation, name='book'),
    path('api/slots/', views.load_slots, name='load_slots'),
    path('payment/', views.payment, name='payment'),
    path('otp/', views.otp_verify, name='otp_verify'),
    path(
        "payment/success/",
        views.payment_success,
        name="payment_success",
    ),
    path(
        "payment/cancel/",
        views.payment_cancel,
        name="payment_cancel",
    ),
    path('confirmation/<str:booking_id>/', views.confirmation, name='confirmation'),
    path(
    "crm/customers/",
    views.crm_customers,
    name="crm_customers",
    ),
    path(
    "crm/bookings/",
    views.crm_bookings,
    name="crm_bookings",
    ),
    path("crm/payments/", views.crm_payments, name="crm_payments"),
    path("crm/reports/", views.crm_reports, name="crm_reports"),
]