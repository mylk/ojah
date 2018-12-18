from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
import logging


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    logger_app = logging.getLogger('rss')
    logger_auth = logging.getLogger('admin_auth')

    remote_address_fields = [
        'HTTP_X_FORWARDED_FOR',
        'REMOTE_ADDR'
    ]

    try:
        remote_address_field = None
        for field in remote_address_fields:
            if field in request.META and request.META[field] != None:
                remote_address_field = field
                break

        logger_auth.warn('Login failed from %s', request.META.get(remote_address_field))
    except Exception as e:
        logger_app.error('Could not log authentication failure.')
