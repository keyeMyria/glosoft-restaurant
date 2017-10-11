from rest_framework.serializers import (
                HyperlinkedIdentityField,
                ValidationError,
                JSONField
                )
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ...orders.models import (
            Orders,
            OrderedItem,
            )
from ...sale.models import (
            Terminal,
            PaymentOption)
from ...product.models import (
            Stock,
            )
from decimal import Decimal
from ...customer.models import Customer


User = get_user_model()


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedItem
        fields = (
                'id',
                #'order',
                'sku',
                'quantity',
                'unit_cost',
                'total_cost',
                'product_name',
                'product_category',
                'tax',
                'discount'
                 )


class ListOrderSerializer(serializers.ModelSerializer):
    ordered_items = ItemSerializer(many=True)
    update_url = HyperlinkedIdentityField(view_name='order-api:update-order')

    class Meta:
        model = Orders
        fields = ('id',
                  'user',
                  'invoice_number',
                  'table',
                  'sale_point',
                  'total_net',
                  'sub_total',
                  'balance',
                  'terminal',
                  'amount_paid',
                  'update_url',
                  'ordered_items',
                  'customer',
                  'mobile',
                  'customer_name',
                  'payment_data',
                  'status',
                  'total_tax',
                  'discount_amount'
                  )


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = ItemSerializer(many=True)
    payment_data = JSONField()

    class Meta:
        model = Orders
        fields = ('id',
                  'user',
                  'invoice_number',
                  'table',
                  'sale_point',
                  'total_net',
                  'sub_total',
                  'balance',
                  'terminal',
                  'amount_paid',
                  'ordered_items',
                  'payment_data',
                  'status',
                  'total_tax',
                  'discount_amount'
                  )

    def validate_total_net(self, value):
        data = self.get_initial()
        try:
            Decimal(data.get('total_net'))
        except Exception as e:
            raise ValidationError('Total Net should be a decimal/integer')
        return value

    def validate_total_tax(self, value):
        data = self.get_initial()
        try:
            total_net = Decimal(data.get('total_net'))
            total_tax = Decimal(data.get('total_tax'))
            if total_tax >= total_net:
                raise ValidationError('Total tax cannot be more than total net')
        except Exception as e:
            raise ValidationError('Total Net should be a decimal/integer')
        return value

    def validate_discount_amount(self, value):
        data = self.get_initial()
        try:
            discount = Decimal(data.get('discount_amount'))
        except Exception as e:
            raise ValidationError('Discount should be a decimal/integer *' + str(discount) + '*')
        return value

    def validate_status(self, value):
        data = self.get_initial()
        status = str(data.get('status'))
        if status == 'fully-paid' or status == 'payment-pending':
            return value
        else:
            raise ValidationError('Enter correct Status. Expecting either fully-paid/payment-pending')

    def validate_terminal(self, value):
        data = self.get_initial()
        terminal_id = int(data.get('terminal'))
        try:
            Terminal.objects.get(pk=terminal_id)
        except Exception as e:
            raise ValidationError('Terminal specified does not exist')
        return value

    def create(self, validated_data):
        # add sold amount to drawer
        try:
            total_net = Decimal(validated_data.get('total_net'))
        except:
            total_net = Decimal(0)
        try:
            total_tax = Decimal(validated_data.get('total_tax'))
        except Exception as e:
            total_tax = Decimal(0)
        terminal = validated_data.get('terminal')
        terminal.amount += Decimal(total_net)
        terminal.save()

        order = Orders()

        try:
            ordered_items_data = validated_data.pop('ordered_items')
        except:
            raise ValidationError('Ordered items field should not be empty')
        status = validated_data.get('status')
        # make a sale
        order.user = validated_data.get('user')
        order.invoice_number = validated_data.get('invoice_number')
        order.total_net = validated_data.get('total_net')
        order.sub_total = validated_data.get('sub_total')
        order.balance = validated_data.get('balance')
        order.terminal = validated_data.get('terminal')
        order.table = validated_data.get('table')
        order.sale_point = validated_data.get('sale_point')
        order.amount_paid = validated_data.get('amount_paid')
        order.status = status
        order.payment_data = validated_data.get('payment_data')
        order.total_tax = total_tax
        order.mobile = validated_data.get('mobile')
        order.discount_amount = validated_data.get('discount_amount')

        order.save()
        # add payment options

        for ordered_item_data in ordered_items_data:
            OrderedItem.objects.create(orders=order, **ordered_item_data)
            try:
                stock = Stock.objects.get(variant__sku=ordered_item_data['sku'])
                if stock:
                    Stock.objects.decrease_stock(stock, ordered_item_data['quantity'])
                else:
                    print 'stock not found'
            except Exception as e:
                print 'Error reducing stock!'

        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    ordered_items = ItemSerializer(many=True)

    class Meta:
        model = Orders
        fields = ('id',
                  'invoice_number',
                  'total_net',
                  'sub_total',
                  'balance',
                  'terminal',
                  'amount_paid',
                  'status',
                  'total_tax',
                  'discount_amount',
                  'debt',
                  'ordered_items',
                  )

    def validate_status(self, value):
        data = self.get_initial()
        status = str(data.get('status'))
        if status == 'fully-paid' or status == 'payment-pending':
            status = status
            amount_paid = Decimal(data.get('amount_paid'))
            sale = Orders.objects.get(invoice_number=str(data.get('invoice_number')))
            if status == 'fully-paid' and sale.balance > amount_paid:
                print 'balance ' + str(sale.balance)
                print 'amount ' + str(amount_paid)
                raise ValidationError("Status error. Amount paid is less than balance.")
            else:
                return value
        else:
            raise ValidationError('Enter correct Status. Expecting either fully-paid/payment-pending')

    def validate_total_net(self, value):
        data = self.get_initial()
        try:
            Decimal(data.get('total_net'))
            return value
        except Exception as e:
            raise ValidationError('Total Net should be a decimal/integer')

    def validate_debt(self, value):
        data = self.get_initial()
        try:
            Decimal(data.get('debt'))
        except Exception as e:
            raise ValidationError('Debt should be a decimal/integer')
        return value

    def validate_amount_paid(self, value):
        data = self.get_initial()
        try:
            Decimal(data.get('amount_paid'))
        except Exception as e:
            raise ValidationError('Amount paid should be a decimal/integer')
        return value

    def validate_terminal(self, value):
        data = self.get_initial()
        # try:
        terminal = Terminal.objects.filter(pk=int(data.get('terminal')))
        if terminal.exists():
            return value
        else:
            raise ValidationError('Terminal specified does not exist')
            # except:
            #     raise ValidationError('Terminal specified does not exist')

    def update(self, instance, validated_data):
        terminal = validated_data.get('terminal', instance.terminal.id)
        terminal.amount += Decimal(validated_data.get('amount_paid', instance.amount_paid))
        terminal.save()
        instance.debt = instance.debt - validated_data.get('amount_paid', instance.amount_paid)
        instance.amount_paid = instance.amount_paid + validated_data.get('amount_paid', instance.amount_paid)
        if instance.amount_paid >= instance.total_net:
            instance.status = 'fully-paid'
        else:
            instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance