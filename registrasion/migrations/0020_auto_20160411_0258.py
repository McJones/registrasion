# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-11 02:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0019_manualcreditnoterefund_squashed_0020_auto_20160411_0256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manualcreditnoterefund',
            name='creditnoterefund_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='registration.CreditNoteRefund'),
        ),
    ]
