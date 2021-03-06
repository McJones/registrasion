# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-06 12:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0011_auto_20160401_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='cart',
            name='released',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='cart',
            name='time_last_updated',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='order',
            field=models.PositiveIntegerField(db_index=True, verbose_name='Display order'),
        ),
        migrations.AlterField(
            model_name='product',
            name='order',
            field=models.PositiveIntegerField(db_index=True, verbose_name='Display order'),
        ),
        migrations.AlterField(
            model_name='productitem',
            name='quantity',
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterIndexTogether(
            name='cart',
            index_together=set([('active', 'released'), ('released', 'user'), ('active', 'user'), ('active', 'time_last_updated')]),
        ),
    ]
