# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    replaces = [('registration', '0001_initial'), ('registration', '0002_auto_20160304_1723')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('company', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_last_updated', models.DateTimeField()),
                ('reservation_duration', models.DurationField()),
                ('revision', models.PositiveIntegerField(default=1)),
                ('active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=65, verbose_name='Name')),
                ('description', models.CharField(max_length=255, verbose_name='Description')),
                ('order', models.PositiveIntegerField(verbose_name='Display order')),
                ('render_type', models.IntegerField(verbose_name='Render type', choices=[(1, 'Radio button'), (2, 'Quantity boxes')])),
            ],
        ),
        migrations.CreateModel(
            name='DiscountBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255, verbose_name='Description')),
            ],
        ),
        migrations.CreateModel(
            name='DiscountForCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('percentage', models.DecimalField(max_digits=4, decimal_places=1, blank=True)),
                ('quantity', models.PositiveIntegerField()),
                ('category', models.ForeignKey(to='registration.Category')),
            ],
        ),
        migrations.CreateModel(
            name='DiscountForProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('percentage', models.DecimalField(null=True, max_digits=4, decimal_places=1)),
                ('price', models.DecimalField(null=True, max_digits=8, decimal_places=2)),
                ('quantity', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='DiscountItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField()),
                ('cart', models.ForeignKey(to='registration.Cart')),
            ],
        ),
        migrations.CreateModel(
            name='EnablingConditionBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255)),
                ('mandatory', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cart_revision', models.IntegerField(null=True)),
                ('void', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('value', models.DecimalField(max_digits=8, decimal_places=2)),
                ('cart', models.ForeignKey(to='registration.Cart', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255)),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.DecimalField(max_digits=8, decimal_places=2)),
                ('invoice', models.ForeignKey(to='registration.Invoice')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(default=django.utils.timezone.now)),
                ('reference', models.CharField(max_length=64)),
                ('amount', models.DecimalField(max_digits=8, decimal_places=2)),
                ('invoice', models.ForeignKey(to='registration.Invoice')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=65, verbose_name='Name')),
                ('description', models.CharField(max_length=255, verbose_name='Description')),
                ('price', models.DecimalField(verbose_name='Price', max_digits=8, decimal_places=2)),
                ('limit_per_user', models.PositiveIntegerField(verbose_name='Limit per user', blank=True)),
                ('reservation_duration', models.DurationField(default=datetime.timedelta(0, 3600), verbose_name='Reservation duration')),
                ('order', models.PositiveIntegerField(verbose_name='Display order')),
                ('category', models.ForeignKey(verbose_name='Product category', to='registration.Category')),
            ],
        ),
        migrations.CreateModel(
            name='ProductItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField()),
                ('cart', models.ForeignKey(to='registration.Cart')),
                ('product', models.ForeignKey(to='registration.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('completed_registration', models.BooleanField(default=False)),
                ('highest_complete_category', models.IntegerField(default=0)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('recipient', models.CharField(max_length=64, verbose_name='Recipient')),
                ('code', models.CharField(unique=True, max_length=16, verbose_name='Voucher code')),
                ('limit', models.PositiveIntegerField(verbose_name='Voucher use limit')),
            ],
        ),
        migrations.CreateModel(
            name='CategoryEnablingCondition',
            fields=[
                ('enablingconditionbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.EnablingConditionBase')),
                ('enabling_category', models.ForeignKey(to='registration.Category')),
            ],
            bases=('registration.enablingconditionbase',),
        ),
        migrations.CreateModel(
            name='IncludedProductDiscount',
            fields=[
                ('discountbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.DiscountBase')),
                ('enabling_products', models.ManyToManyField(to=b'registration.Product', verbose_name='Including product')),
            ],
            options={
                'verbose_name': 'Product inclusion',
            },
            bases=('registration.discountbase',),
        ),
        migrations.CreateModel(
            name='ProductEnablingCondition',
            fields=[
                ('enablingconditionbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.EnablingConditionBase')),
                ('enabling_products', models.ManyToManyField(to=b'registration.Product')),
            ],
            bases=('registration.enablingconditionbase',),
        ),
        migrations.CreateModel(
            name='TimeOrStockLimitDiscount',
            fields=[
                ('discountbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.DiscountBase')),
                ('start_time', models.DateTimeField(null=True, verbose_name='Start time', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name='End time', blank=True)),
                ('limit', models.PositiveIntegerField(null=True, verbose_name='Limit', blank=True)),
            ],
            options={
                'verbose_name': 'Promotional discount',
            },
            bases=('registration.discountbase',),
        ),
        migrations.CreateModel(
            name='TimeOrStockLimitEnablingCondition',
            fields=[
                ('enablingconditionbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.EnablingConditionBase')),
                ('start_time', models.DateTimeField(null=True, verbose_name='Start time')),
                ('end_time', models.DateTimeField(null=True, verbose_name='End time')),
                ('limit', models.PositiveIntegerField(null=True, verbose_name='Limit')),
            ],
            bases=('registration.enablingconditionbase',),
        ),
        migrations.CreateModel(
            name='VoucherDiscount',
            fields=[
                ('discountbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.DiscountBase')),
                ('voucher', models.OneToOneField(verbose_name='Voucher', to='registration.Voucher')),
            ],
            bases=('registration.discountbase',),
        ),
        migrations.CreateModel(
            name='VoucherEnablingCondition',
            fields=[
                ('enablingconditionbase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='registration.EnablingConditionBase')),
                ('voucher', models.OneToOneField(to='registration.Voucher')),
            ],
            bases=('registration.enablingconditionbase',),
        ),
        migrations.AddField(
            model_name='enablingconditionbase',
            name='categories',
            field=models.ManyToManyField(to=b'registration.Category', blank=True),
        ),
        migrations.AddField(
            model_name='enablingconditionbase',
            name='products',
            field=models.ManyToManyField(to=b'registration.Product', blank=True),
        ),
        migrations.AddField(
            model_name='discountitem',
            name='discount',
            field=models.ForeignKey(to='registration.DiscountBase'),
        ),
        migrations.AddField(
            model_name='discountitem',
            name='product',
            field=models.ForeignKey(to='registration.Product'),
        ),
        migrations.AddField(
            model_name='discountforproduct',
            name='discount',
            field=models.ForeignKey(to='registration.DiscountBase'),
        ),
        migrations.AddField(
            model_name='discountforproduct',
            name='product',
            field=models.ForeignKey(to='registration.Product'),
        ),
        migrations.AddField(
            model_name='discountforcategory',
            name='discount',
            field=models.ForeignKey(to='registration.DiscountBase'),
        ),
        migrations.AddField(
            model_name='cart',
            name='vouchers',
            field=models.ManyToManyField(to=b'registration.Voucher', blank=True),
        ),
        migrations.AddField(
            model_name='badge',
            name='profile',
            field=models.OneToOneField(to='registration.Profile'),
        ),
        migrations.AlterField(
            model_name='discountforcategory',
            name='percentage',
            field=models.DecimalField(max_digits=4, decimal_places=1),
        ),
        migrations.AlterField(
            model_name='discountforproduct',
            name='percentage',
            field=models.DecimalField(null=True, max_digits=4, decimal_places=1, blank=True),
        ),
        migrations.AlterField(
            model_name='discountforproduct',
            name='price',
            field=models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True),
        ),
    ]
