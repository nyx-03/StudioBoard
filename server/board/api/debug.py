import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def debug_log(fmt, *args):
    """Log seulement en DEBUG pour éviter de polluer en prod."""
    if settings.DEBUG:
        logger.debug(fmt, *args)