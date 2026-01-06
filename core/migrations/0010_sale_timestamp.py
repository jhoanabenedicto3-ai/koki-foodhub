# Generated migration for Sale.timestamp field

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_inventoryitem_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='timestamp',
            field=models.DateTimeField(default=timezone.now),
        ),
    ]
