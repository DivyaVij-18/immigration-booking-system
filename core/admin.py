from django.contrib import admin

from .models import Booking, Consultant, Office, Slot, Payment

from .models import WorkingSchedule

from .utils import generate_slots_for_schedule


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'latitude', 'longitude')
    search_fields = ('name', 'city', 'address', 'phone')
    list_filter = ('city',)
    ordering = ('city', 'name')


@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'qualification', 'experience')
    search_fields = ('name', 'specialization', 'qualification')
    list_filter = ('specialization', 'experience')
    ordering = ('name',)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = (
        "office",
        "date",
        "time",
        "capacity",
        "remaining_slots",
        "is_available",
    )

    search_fields = (
        "office__name",
        "office__city",
    )

    list_filter = (
        "office",
        "date",
    )

    ordering = (
        "date",
        "time",
    )

    date_hierarchy = "date"

    @admin.display(boolean=True, description="Available")
    def is_available(self, obj):
        return obj.remaining_slots > 0

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_id',
        'full_name',
        'email',
        'phone',
        'office',
        'slot',
        'payment_status',
        'booking_status',
        'created_at',
    )
    search_fields = ('full_name', 'email', 'phone', 'office__name')
    list_filter = ('payment_status', 'booking_status', 'office', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "amount",
        "provider",
        "status",
        "created_at",
    )

    search_fields = (
        "booking__booking_id",
        "transaction_id",
    )

    list_filter = (
        "status",
        "provider",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

@admin.register(WorkingSchedule)
class WorkingScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "office",
        "day_of_week",
        "start_time",
        "end_time",
        "slot_duration",
        "capacity",
        "is_closed",
    )

    list_filter = (
        "office",
        "day_of_week",
        "is_closed",
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        generate_slots_for_schedule(obj)
    
