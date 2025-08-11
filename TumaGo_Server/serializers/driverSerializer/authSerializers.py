from rest_framework import serializers
from django.contrib.auth import get_user_model
from ...models import DriverVehicle, CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'phone_number', 'name', 'surname', 'identity_number', 'profile_picture',
                  'streetAdress', 'addressLine', 'city', 'province', 'postalCode', 'rating', 'role', 'verifiedEmail', 'license']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['name', 'surname', 'email', 'phone_number', 'password',
                  'streetAdress', 'addressLine', 'city', 'province', 'postalCode', 'verifiedEmail']

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', get_user_model().DRIVER)

        user = get_user_model()(
            email=validated_data['email'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            phone_number=validated_data['phone_number'],
            streetAdress=validated_data['streetAdress'],
            addressLine=validated_data['addressLine'],
            city=validated_data['city'],
            province=validated_data['province'],
            postalCode=validated_data['postalCode'],
            verifiedEmail=validated_data['verifiedEmail'],
            role=role
        )

        user.set_password(password)  # ✅ This hashes the password
        user.save()
        return user
    
class ResetPasswordSerializer(serializers.Serializer):
    oldPassword = serializers.CharField(required=True)
    newPassword = serializers.CharField(required=True)
    confirmPassword = serializers.CharField(required=True)

    def validate(self, data):
        if data['newPassword'] != data['confirmPassword']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverVehicle
        fields = ['delivery_vehicle', 'car_name', 'number_plate', 'color', 'vehicle_model']

    def create(self, validated_data):
        user = self.context['request'].user  # Get the user from context
        return DriverVehicle.objects.create(driver=user, **validated_data)
    
class LicenseUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['license_picture', 'license']  # include license so we can update it ourselves

        # Make license read-only so it's not expected from the frontend
        extra_kwargs = {
            'license': {'read_only': True}
        }

    def update(self, instance, validated_data):
        # Automatically set license = True when an image is uploaded
        if 'license_picture' in validated_data:
            validated_data['license'] = True
        return super().update(instance, validated_data)