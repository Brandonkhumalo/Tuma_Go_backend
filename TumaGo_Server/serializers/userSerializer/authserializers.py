from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

# User Serializer for Regular User Data
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'phone_number', 'remember',
                  'name', 'surname', 'identity_number', 'profile_picture', 'identity_picture',
                  'streetAdress', 'addressLine', 'city', 'province', 'postalCode', 'rating', 'role', 'verifiedEmail']

# Signup Serializer for User Registration
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    

    class Meta:
        model = get_user_model()
        fields = ['phone_number', 'email', 'password']

    def create(self, validated_data):
        print("Validated signup data:", validated_data)

        user = get_user_model().objects.create_user(
            phone_number=validated_data.get('phone_number'),
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


# Serializer to Update User Info
class UserInfo(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['name', 'surname', 'identity_number',
                  'streetAdress', 'addressLine', 'city', 'province', 'postalCode']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# Login Serializer to Validate Credentials
class LoginSerializer(serializers.Serializer):  
    email = serializers.EmailField() 
    password = serializers.CharField(max_length=100, write_only=True)

    def validate(self, attrs):

        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required")

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        attrs['user'] = user
        return attrs