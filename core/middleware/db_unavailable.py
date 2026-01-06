from django.shortcuts import render
from django.db.utils import OperationalError as DBOperationalError
import logging

logger = logging.getLogger(__name__)


class DBUnavailableMiddleware:
    """Catch database OperationalError and return a friendly 503 page.

    This prevents leaking internal DB errors to users and allows the site to
    continue serving non-DB pages while giving a clear message for DB-backed
    features.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except DBOperationalError as exc:
            logger.exception("Database unavailable during request")
            # Render a simple 503 page without exposing exception details
            return render(request, "pages/db_unavailable.html", status=503)

        except Exception:
            # Re-raise other exceptions so they are handled by normal handlers
            raise
