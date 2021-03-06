from datetime import datetime
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView
from saleor.site.models import SiteSettings

User = get_user_model()
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class CustomJWTSerializer(JSONWebTokenSerializer):
    def validate(self, attrs):
        # email comes as the code
        username = attrs.get('email')
        password = attrs.get('password')
        # check the working period first
        time_now = datetime.now().time()
        try:
            opening_time = SiteSettings.objects.all().first().opening_time
            closing_time = SiteSettings.objects.all().first().closing_time

            if opening_time < time_now and time_now < closing_time:
                print time_now
            else:
                raise serializers.ValidationError(_('Unauthorized User Login.'))
        except Exception as e:
            print e
            raise serializers.ValidationError(_('Unauthorized User Login.'))

        if username and password:
            username = username.lower()
            if '@' in username:
                kwargs = {'email': username}
            else:
                kwargs = {'code': username}
            try:
                us = get_user_model().objects.get(**kwargs)
            except ObjectDoesNotExist as e:
                msg = _('Invalid User Credentials.')
                raise serializers.ValidationError(msg)

            user = authenticate(username=us.email, password=us.rest_code)

            if user:
                if not user.is_active:
                    msg = _('Unauthorized User Login.')
                    raise serializers.ValidationError(msg)
                
                if not user.has_perm('sales.make_sale') and not user.has_perm('sales.make_invoice'):
                    msg = _('Unauthorized User Login.')
                    raise serializers.ValidationError(msg)

                payload = jwt_payload_handler(user)

                return {
                    'token': jwt_encode_handler(payload),
                    'user': user,
                    'permissions': user.get_all_permissions(),
                }
            else:
                msg = _('Invalid User Credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)


class ObtainJSONWebToken(JSONWebTokenAPIView):
    """
    API View that receives a POST with a user's username and password.

    Returns a JSON Web Token that can be used for authenticated requests.
    """
    # serializer_class = JSONWebTokenSerializer
    serializer_class = CustomJWTSerializer
