# myapp/context_processors.py
from django.conf import settings


def admin_url(request):
    return {"django_admin_url": settings.ADMIN_URL}
