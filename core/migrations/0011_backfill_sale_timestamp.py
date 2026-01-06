# Data migration to backfill timestamp field from date field

from django.db import migrations
from django.utils import timezone


def backfill_timestamp(apps, schema_editor):
    """Backfill timestamp field using the date field values"""
    Sale = apps.get_model('core', 'Sale')
    for sale in Sale.objects.all():
        if sale.date and not sale.timestamp:
            # Convert date to datetime at midnight UTC, then to local timezone
            sale.timestamp = timezone.make_aware(
                timezone.datetime.combine(sale.date, timezone.datetime.min.time())
            )
            sale.save()


def reverse_backfill(apps, schema_editor):
    """Reverse - clear timestamp field"""
    Sale = apps.get_model('core', 'Sale')
    Sale.objects.all().update(timestamp=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_sale_timestamp'),
    ]

    operations = [
        migrations.RunPython(backfill_timestamp, reverse_backfill),
    ]
