from django.db.models.signals import pre_save
from django.dispatch import receiver

from events.models import DSA


@receiver(pre_save, sender=DSA)
def generate_pdf_fields(sender, instance: DSA, **kwargs):
    for field in ("passport", "boarding_pass", "signature"):
        instance.generate_pdf(field)
