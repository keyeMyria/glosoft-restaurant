from __future__ import unicode_literals

from decimal import Decimal
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import pgettext_lazy
from django.utils.timezone import now
from django.core.validators import MinValueValidator, RegexValidator
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)
from saleor.counter.models import Counter
from saleor.product.models import Stock
from saleor.counter_transfer_report.models import Transfer as Report


class TransferManager(BaseUserManager):
    def all_items_filter(self, start_date=None, end_date=None):
        query = self.all()
        if start_date and end_date is not None:
            query = query.filter(
                models.Q(date__gte=start_date) &
                models.Q(date__lte=end_date)
            )
        else:
            if start_date is not None:
                query = query.filter(date__gte=start_date)
            if end_date is not None:
                query = query.filter(date__lte=end_date)
        return query

    def all_item_closed(self, instance):
        return True

    def instance_quantities(self, instance):
        return 0


class CounterTransfer(models.Model):
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE, blank=True, null=True,
                                verbose_name=pgettext_lazy("CounterTransfer field", 'counter'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='counter_transfer_users',
        verbose_name=pgettext_lazy('Sales field', 'user'))
    action = models.IntegerField(
        pgettext_lazy('Stock item field', 'action'),
        validators=[MinValueValidator(0)], default=Decimal(1))
    name = models.CharField(
        pgettext_lazy('CounterTransfer field', 'name'), null=True, blank=True, max_length=128)
    description = models.TextField(
        verbose_name=pgettext_lazy('CounterTransfer field', 'description'), blank=True, null=True)
    updated_at = models.DateTimeField(
        pgettext_lazy('CounterTransfer field', 'updated at'), auto_now=True, null=True)
    date = models.DateField(pgettext_lazy('CounterTransfer field', 'date'),
                            default=now)
    created = models.DateTimeField(pgettext_lazy('CounterTransfer field', 'created'),
                                   default=now, editable=False)

    objects = TransferManager()

    class Meta:
        app_label = 'countertransfer'
        verbose_name = pgettext_lazy('CounterTransfer model', 'CounterTransfer')
        verbose_name_plural = pgettext_lazy('CounterTransfers model', 'CounterTransfers')

    def __str__(self):
        return str(self.id)

    def all_items_closed(self):
        query = self.counter_transfer_items.filter(closed=False)
        if query.exists():
            return False
        return True

    def on_post_save(self):
        print "%s.on_post_save()" % self
        print self.counter
        print self.date
        Report.objects.create_report(self.date, self.counter, user=self.user)
        print '(*)-}'*120

    def on_post_delete(self):
        print "%s.on_post_save()" % self
        print '(-----*---)-}'*120


class TransferItemManager(BaseUserManager):
    def carry_forward_quantity(self, stock):
        query = self.get_queryset().filter(stock=stock)
        query = query.filter(closed=True)
        total_qty = 0
        for item in query:
            total_qty = int(total_qty) + int(item.qty)
        return total_qty

    def decrease_stock(self, instance, quantity):
        instance.sold = models.F('sold') + quantity
        instance.qty = models.F('qty') - quantity
        instance.expected_qty = instance.qty
        instance.save(update_fields=['sold', 'qty', 'expected_qty'])

    def increase_stock(self, instance, quantity):
        instance.qty = models.F('qty') + quantity
        instance.sold = models.F('sold') - quantity
        instance.expected_qty = instance.qty
        instance.save(update_fields=['qty', 'sold', 'expected_qty'])

    def instance_quantities(self, instance, filter_type='transfer', counter=None):
        if filter_type == 'transfer':
            query = self.get_queryset().filter(transfer=instance)
        else:
            query = self.get_queryset().filter(stock=instance)
        if counter:
            query = query.filter(counter=counter)
        qty = query.aggregate(models.Sum('qty'))['qty__sum']
        return qty

    def instance_worth(self, instance, filter_type='transfer'):
        if filter_type == 'transfer':
            query = self.get_queryset().filter(transfer=instance)
        else:
            query = self.get_queryset().filter(stock=instance)
        total = 0
        for i in query:
            total += Decimal(i.qty) * Decimal(i.stock.cost_price.gross)
        return total


class CounterTransferItems(models.Model):
    transfer = models.ForeignKey(
        CounterTransfer, on_delete=models.CASCADE, related_name='counter_transfer_items',
        verbose_name=pgettext_lazy("CounterTransfer field", 'counter'))
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE, related_name="item_counter", blank=True, null=True,
                                verbose_name=pgettext_lazy("CounterTransfer field", 'counter'))
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, blank=True, null=True,
                              verbose_name=pgettext_lazy("CounterTransfer field", 'stock'))
    quantity = models.IntegerField(
        pgettext_lazy('Stock item field', 'quantity'),
        validators=[MinValueValidator(0)], default=Decimal(1))
    sku = models.CharField(max_length=60, blank=True, null=True,
                           verbose_name=pgettext_lazy('CounterTransfer field', 'sku'))
    product_category = models.CharField(max_length=60, blank=True, null=True,
                                        verbose_name=pgettext_lazy('CounterTransfer field', 'category'))
    price = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal(0),
                                verbose_name=pgettext_lazy('CounterTransfer field', 'price'))
    unit_price = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal(0),
                                     verbose_name=pgettext_lazy('CounterTransfer field', 'unit price'))

    tax = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal(0),
                              verbose_name=pgettext_lazy('CounterTransfer field', 'tax'))
    discount = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal(0),
                                   verbose_name=pgettext_lazy('CounterTransfer field', 'discount'))
    qty = models.PositiveIntegerField(default=1,
                                      verbose_name=pgettext_lazy('CounterTransfer field', 'quantity'))
    transferred_qty = models.PositiveIntegerField(default=1,
                                                  verbose_name=pgettext_lazy('CounterTransfer field', 'transferred_qty'))
    deficit = models.IntegerField(default=0,
                                          verbose_name=pgettext_lazy('CounterTransfer field', 'deficit'))
    expected_qty = models.PositiveIntegerField(default=1,
                                               verbose_name=pgettext_lazy('CounterTransfer field', 'expected_qty'))

    sold = models.PositiveIntegerField(default=0,
                                       verbose_name=pgettext_lazy('CounterTransfer field', 'sold'))

    productName = models.CharField(max_length=100, blank=True, null=True,
                                   verbose_name=pgettext_lazy('CounterTransfer field', 'product name'))
    description = models.TextField(
        verbose_name=pgettext_lazy('CounterTransfer field', 'description'), blank=True, null=True)
    updated_at = models.DateTimeField(
        pgettext_lazy('CounterTransfer field', 'updated at'), auto_now=True, null=True)
    created = models.DateTimeField(pgettext_lazy('CounterTransfer field', 'created'),
                                   default=now, editable=False)
    closed = models.BooleanField(default=False)
    objects = TransferItemManager()

    class Meta:
        app_label = 'countertransfer'
        verbose_name = pgettext_lazy('CounterTransfer model', 'CounterTransfer')
        verbose_name_plural = pgettext_lazy('CounterTransfers model', 'CounterTransfers')

    def __str__(self):
        return str(self.sku) + ' ' + str(self.qty)


@receiver(signals.post_save)
def search_on_post_save(sender, instance, **kwargs):
    if issubclass(sender, CounterTransfer):
         instance.on_post_save()


@receiver(signals.post_delete)
def search_on_post_delete(sender, instance, **kwargs):
    if issubclass(sender, CounterTransfer):
         instance.on_post_delete()


