from django.contrib import messages
print(">>> LOADED VIEWS.PY <<<")
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm, OTPForm, PaymentForm
from .models import Booking, Consultant, Office, Slot, Payment, WorkingSchedule
from .stripe_service import create_checkout_session
from datetime import date, timedelta, datetime
import calendar
from django.db.models import Sum


def home(request):
    consultants = Consultant.objects.all()
    return render(request, 'core/home.html', {'consultants': consultants})


def offices(request):
    offices_list = Office.objects.all()
    return render(request, 'core/offices.html', {'offices': offices_list})

def load_slots(request):
    office_id = request.GET.get("office")

    if not office_id:
        return JsonResponse([], safe=False)

    today = date.today()
    start_date = today + timedelta(days=1)
    # Load all working schedules once
    schedules = {
        schedule.day_of_week: schedule
        for schedule in WorkingSchedule.objects.filter(
            office_id=office_id,
            is_closed=False,
        )
    }

    grouped = {}

    for i in range(90):

        current_date = start_date + timedelta(days=i)
        schedule = schedules.get(current_date.weekday())

        if not schedule:
            continue

        current_time = datetime.combine(current_date, schedule.start_time)
        end_time = datetime.combine(current_date, schedule.end_time)

        date_key = current_date.strftime("%Y-%m-%d")

        grouped[date_key] = {
            "day": current_date.strftime("%A"),
            "date": current_date.strftime("%d %b %Y"),
            "iso_date": current_date.strftime("%Y-%m-%d"),
            "slots": []
        }
        
        while current_time < end_time:

            slot, created = Slot.objects.get_or_create(
                office_id=office_id,
                date=current_date,
                time=current_time.time(),
                defaults={
                    "capacity": schedule.capacity,
                    "available": True,
                },
            )

            if slot.remaining_slots > 0:
                grouped[date_key]["slots"].append({
                    "id": slot.id,
                    "time": current_time.strftime("%I:%M %p"),
                })

            current_time += timedelta(minutes=schedule.slot_duration)

    return JsonResponse(list(grouped.values()), safe=False)

@transaction.atomic
def book_consultation(request):
    initial_office = request.GET.get('office')

    if request.method == 'POST':
        print("===== ENTERED POST =====")
 
        form = BookingForm(request.POST)

        print("===== CREATED FORM =====")

        valid = form.is_valid()

        print("VALID =", valid)
        print("ERRORS =", form.errors)

        if not form.is_valid():
            print("FORM ERRORS:", form.errors)
            print("POST DATA:", request.POST)

        if form.is_valid():

            booking = form.save(commit=False)

            slot = (
                Slot.objects
                .select_for_update()
                .get(pk=booking.slot.pk)
            )

            if slot.remaining_slots <= 0:
                messages.error(
                    request,
                    "Sorry, this appointment slot has just become full."
                )
                return redirect("core:book")

            booking.payment_status = Booking.PAYMENT_PENDING
            booking.booking_status = Booking.BOOKING_PENDING

            booking.save()

            Payment.objects.create(
                booking=booking,
                amount=150.00,
                currency="AUD",
                provider="Stripe",
                status=Payment.STATUS_PENDING,
            )

            request.session["booking_pk"] = booking.pk

            messages.success(
                request,
                "Booking created. Please complete payment."
            )

            return redirect("core:payment")

    else:
        try:
            office_id = int(initial_office) if initial_office else None
        except (ValueError, TypeError):
            office_id = None

        form = BookingForm(initial_office=office_id)

    return render(
        request,
        "core/booking_form.html",
        {
            "form": form,
        },
    )


def payment(request):
    booking_pk = request.session.get('booking_pk')
    
    if not booking_pk:
        messages.warning(request, 'Please create a booking first.')
        return redirect('core:book')

    booking = get_object_or_404(Booking, pk=booking_pk)

    if request.method == 'POST':
        session = create_checkout_session(booking.payment)
        request.session["stripe_session_id"] = session.id
        return redirect(session.url)

    return render(request, 'core/payment.html', {
        'booking': booking,
    })

@transaction.atomic
def payment_success(request):
    booking_pk = request.session.get("booking_pk")

    if not booking_pk:
        messages.error(request, "Booking not found.")
        return redirect("core:home")

    booking = get_object_or_404(Booking, pk=booking_pk)

    # Lock the slot while we verify capacity
    slot = (
       Slot.objects
       .select_for_update()
       .get(pk=booking.slot.pk)
    )

    other_bookings = slot.bookings.filter(
        booking_status__in=[
            Booking.BOOKING_PENDING,
            Booking.BOOKING_CONFIRMED,
        ]
    ).exclude(pk=booking.pk).count()

    if other_bookings >= slot.capacity:
        messages.error(
            request,
            "Sorry, this appointment slot became unavailable."
        )
        return redirect("core:book")

    payment = booking.payment

    payment.status = Payment.STATUS_PAID
    payment.transaction_id = request.session.get(
        "stripe_session_id"
    )

    payment.save(update_fields=[
        "status",
        "transaction_id"
    ])

    booking.payment_status = Booking.PAYMENT_PAID
    booking.booking_status = Booking.BOOKING_CONFIRMED

    booking.save(update_fields=[
        "payment_status",
        "booking_status"
    ])

    request.session.pop("booking_pk", None)
    request.session.pop("stripe_session_id", None)

    return redirect(
        "core:confirmation",
        booking_id=booking.booking_id
    )

def payment_cancel(request):
    messages.warning(
        request,
        "Payment was cancelled."
    )

    return redirect("core:payment")


def otp_verify(request):
    booking_pk = request.session.get('booking_pk')
    if not booking_pk:
        messages.warning(request, 'Please create a booking first.')
        return redirect('core:book')

    booking = get_object_or_404(Booking, pk=booking_pk)

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp'] == '123456':

                payment = booking.payment
                payment.status = Payment.STATUS_PAID
                payment.transaction_id = f"DEMO-{booking.booking_id}"
                payment.save(update_fields=["status", "transaction_id"])
                
                booking.payment_status = Booking.PAYMENT_PAID
                booking.booking_status = Booking.BOOKING_CONFIRMED
                booking.save(update_fields=['payment_status', 'booking_status'])

                del request.session['booking_pk']
                messages.success(request, 'OTP verified successfully!')
                return redirect('core:confirmation', booking_id=booking.booking_id)
            messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPForm()

    return render(request, 'core/otp_verify.html', {
        'form': form,
        'booking': booking,
    })


def confirmation(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    return render(request, 'core/confirmation.html', {'booking': booking})


#The proper implementation is to store Stripe's real Checkout Session ID (or Payment Intent ID), which looks like:
def crm_dashboard(request):

    total_bookings = Booking.objects.count()
    total_payments = Payment.objects.filter(
        status=Payment.STATUS_PAID
    ).count()
    total_customers = Booking.objects.values("email").distinct().count()

    revenue = (
        Payment.objects.filter(status=Payment.STATUS_PAID)
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    recent_bookings = Booking.objects.order_by("-created_at")[:10]

    return render(request, "core/crm/dashboard.html", {
        "total_bookings": total_bookings,
        "total_payments": total_payments,
        "total_customers": total_customers,
        "revenue": revenue,
        "recent_bookings": recent_bookings,
    })

def crm_customers(request):

    customers = Booking.objects.select_related("office").order_by("-created_at")

    return render(
        request,
        "core/crm/customers.html",
        {
            "customers": customers
        }
    )

def crm_bookings(request):

    bookings = (
        Booking.objects
        .select_related("office", "slot")
        .order_by("-created_at")
    )

    return render(
        request,
        "core/crm/bookings.html",
        {
            "bookings": bookings
        }
    )

def crm_payments(request):

    payments = (
        Payment.objects
        .select_related("booking")
        .order_by("-created_at")
    )

    return render(
        request,
        "core/crm/payments.html",
        {
            "payments": payments
        }
    )


def crm_reports(request):

    total_bookings = Booking.objects.count()

    confirmed = Booking.objects.filter(
        booking_status=Booking.BOOKING_CONFIRMED
    ).count()

    pending = Booking.objects.filter(
        booking_status=Booking.BOOKING_PENDING
    ).count()

    revenue = (
        Payment.objects.filter(
            status=Payment.STATUS_PAID
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    offices = Office.objects.all()

    return render(
        request,
        "core/crm/reports.html",
        {
            "total_bookings": total_bookings,
            "confirmed": confirmed,
            "pending": pending,
            "revenue": revenue,
            "offices": offices,
        },
    )