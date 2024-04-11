from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django_rq import job


@job
def reset_password(email):
    form = PasswordResetForm({"email": email})
    form.full_clean()
    form.save(
        domain_override=settings.MAIN_HOST,
        use_https=settings.HAS_HTTPS,
    )
