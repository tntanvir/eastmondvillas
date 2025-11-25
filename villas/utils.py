from django.utils import timezone
from .models import DailyAnalytics
from django.db import models

def update_daily_analytics(property, field):
    today = timezone.now().date()

    analytics, created = DailyAnalytics.objects.get_or_create(
        property=property,
        date=today
    )

    # increment field
    if field == "views":
        analytics.views += 1
    elif field == "bookings":
        analytics.bookings += 1
    elif field == "downloads":
        analytics.downloads += 1

    analytics.save()
    return analytics


def get_analytics_for_property(property, start_date, end_date):
    return DailyAnalytics.objects.filter(
        property=property,
        date__range=(start_date, end_date)
    ).order_by('date')

def get_total_analytics_for_property(property, start_date, end_date):
    analytics = DailyAnalytics.objects.filter(
        property=property,
        date__range=(start_date, end_date)
    )

    total_views = analytics.aggregate(total_views=models.Sum('views'))['total_views'] or 0
    total_bookings = analytics.aggregate(total_bookings=models.Sum('bookings'))['total_bookings'] or 0
    total_downloads = analytics.aggregate(total_downloads=models.Sum('downloads'))['total_downloads'] or 0

    return {
        'total_views': total_views,
        'total_bookings': total_bookings,
        'total_downloads': total_downloads,
    }

from .models import Booking

def validate_date_range(property, start_date, end_date):
    today = timezone.now().date()

    if start_date < today:
        return True

    has_overlap = Booking.objects.filter(
        property=property,
        status__in=['approved'],
        check_in__lte=end_date,
        check_out__gte=start_date
    ).exists()

    if has_overlap:
        return True 

    return False

from datetime import datetime

def is_valid_date(date):

    try:
        # datetime.strptime(date, "%Y-%m-%d")
        datetime.strptime(str(date), "%Y-%m-%d")
        return True
    except ValueError:
        return False