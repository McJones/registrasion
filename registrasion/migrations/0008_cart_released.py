# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0007_auto_20160326_2105'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='released',
            field=models.BooleanField(default=False),
        ),
    ]
