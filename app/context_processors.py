from django.utils import timezone
from datetime import timedelta
import pytz

def add_current_time(request):
    """
    Add the current time in GMT+8 timezone to the template context.
    """
    gmt8 = pytz.timezone('Asia/Manila')  # Set the timezone to GMT+8
    current_time = timezone.now().astimezone(gmt8)  # Convert current time to GMT+8
    return {'current_time': current_time}
