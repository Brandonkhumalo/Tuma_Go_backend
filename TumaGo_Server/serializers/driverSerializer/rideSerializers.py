from rest_framework import serializers
from ...models import Delivery

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['origin_lat', 'origin_lng', 'destination_lat', 'destination_lng', 'vehicle', 'fare',
                  'payment_method', 'delivery_id', 'date' ]