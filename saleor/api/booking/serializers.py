# booking rest api serializers

from rest_framework import serializers
from django.utils.formats import localize
from django.contrib.auth import get_user_model
from saleor.booking.models import Book as Table
from saleor.booking.models import Payment
User = get_user_model()


class BookingListSerializer(serializers.ModelSerializer):
    price_amount = serializers.SerializerMethodField()
    room_name = serializers.SerializerMethodField()
    date_in = serializers.SerializerMethodField()
    date_out = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    booking_edit = serializers.HyperlinkedIdentityField(view_name='dashboard:booking-edit')
    booking_delete = serializers.HyperlinkedIdentityField(view_name='dashboard:booking-delete')
    booking_detail = serializers.HyperlinkedIdentityField(view_name='dashboard:booking-detail')

    class Meta:
        model = Table
        fields = (
                  'id',
                  'invoice_number',
                  'price_type',
                  'days',
                  'child',
                  'adult',
                  'date_in',
                  'date_out',
                  'active',
                  'customer_name',
                  'room_name',
                  'user',
                  'price_amount',
                  'created',
                  'booking_edit',
                  'booking_delete',
                  'booking_detail'
                 )

    def get_price_amount(self, obj):
        return obj.price.gross

    def get_room_name(self, obj):
        return obj.room.name

    def get_customer_name(self, obj):
        return obj.customer.name

    def get_date_in(self, obj):
        return localize(obj.check_in)

    def get_date_out(self, obj):
        return localize(obj.check_out)


class PaymentListSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ('id',
                  'invoice_number',
                  'book',
                  'amount',
                  'payment_option',
                  'date',
                  'customer_name',
                  'description',
                  'created'
                 )

    def get_amount(self, obj):
        try:
            return obj.amount_paid.gross
        except Exception as e:
            return 0

    def get_customer_name(self, obj):
        try:
            return obj.customer.name
        except Exception as e:
            print e
            return ''

