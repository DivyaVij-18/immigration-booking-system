from django.db import models


class Office(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} ({self.city})"

class WorkingSchedule(models.Model):
    DAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    office = models.ForeignKey(
        Office,
        on_delete=models.CASCADE,
        related_name="schedules",
    )

    day_of_week = models.PositiveSmallIntegerField(choices=DAYS)

    start_time = models.TimeField()
    end_time = models.TimeField()

    lunch_start = models.TimeField(
        blank=True,
        null=True,
    )

    lunch_end = models.TimeField(
        blank=True,
        null=True,
    )

    slot_duration = models.PositiveIntegerField(
        default=30,
        help_text="Minutes",
    )

    capacity = models.PositiveIntegerField(default=1)

    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("office", "day_of_week")
        ordering = ["office", "day_of_week"]

    def __str__(self):
        return f"{self.office.name} - {self.get_day_of_week_display()}"


class Consultant(models.Model):
    name = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience")
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='consultants/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Slot(models.Model):
    office = models.ForeignKey(
        Office,
        on_delete=models.CASCADE,
        related_name='slots',
    )
    date = models.DateField()
    time = models.TimeField()

    capacity = models.PositiveIntegerField(default=4)
    available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']
        unique_together = ('office', 'date', 'time')

    @property
    def remaining_slots(self):

        booked = self.bookings.filter(
            booking_status__in=[
                Booking.BOOKING_PENDING,
                Booking.BOOKING_CONFIRMED,
            ]
        ).count()

        return max(self.capacity - booked, 0)

    def __str__(self):
        status = "Available" if self.available else "Booked"
        return f"{self.office.name} — {self.date} {self.time.strftime('%H:%M')} ({status})"


class Booking(models.Model):
    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_FAILED = 'failed'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_FAILED, 'Failed'),
    ]

    BOOKING_PENDING = 'pending'
    BOOKING_CONFIRMED = 'confirmed'
    BOOKING_CANCELLED = 'cancelled'
    BOOKING_STATUS_CHOICES = [
        (BOOKING_PENDING, 'Pending'),
        (BOOKING_CONFIRMED, 'Confirmed'),
        (BOOKING_CANCELLED, 'Cancelled'),
    ]

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    office = models.ForeignKey(
        Office,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    slot = models.ForeignKey(
        Slot,
        on_delete=models.PROTECT,
        related_name='bookings',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
    )
    booking_status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default=BOOKING_PENDING,
    )
    booking_id = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_id:
            last_booking = Booking.objects.order_by('-id').first()
            next_id = 1001 if not last_booking else 1001 + last_booking.id
            self.booking_id = f"IMM{next_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking #{self.pk} — {self.full_name}"

class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    currency = models.CharField(
        max_length=5,
        default="AUD"
    )

    provider = models.CharField(
        max_length=30,
        default="Stripe"
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking.booking_id} - {self.status}"