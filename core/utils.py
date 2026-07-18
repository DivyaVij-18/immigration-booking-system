from datetime import date, datetime, timedelta

from .models import Slot


def generate_slots_for_schedule(schedule, days=30):
    today = date.today()

    for i in range(days):
        current_date = today + timedelta(days=i)

        if current_date.weekday() != schedule.day_of_week:
            continue

        if schedule.is_closed:
            continue

        current_time = datetime.combine(
            current_date,
            schedule.start_time,
        )

        end_time = datetime.combine(
            current_date,
            schedule.end_time,
        )

        while current_time < end_time:

            slot_time = current_time.time()

            if (
                schedule.lunch_start
                and schedule.lunch_end
                and schedule.lunch_start <= slot_time < schedule.lunch_end
            ):
                current_time += timedelta(
                    minutes=schedule.slot_duration
                )
                continue

            Slot.objects.get_or_create(
                office=schedule.office,
                date=current_date,
                time=slot_time,
                defaults={
                    "capacity": schedule.capacity,
                    "available": True,
                },
            )

            current_time += timedelta(
                minutes=schedule.slot_duration
            )