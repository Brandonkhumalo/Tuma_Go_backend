from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from ...serializers.driverSerializer.authSerializers import RegisterSerializer, VehicleSerializer, LicenseUploadSerializer, ResetPasswordSerializer
from ...token import JWTAuthentication
from ...models import CustomUser
from django.shortcuts import get_object_or_404

# Register Driver / User (Unified Registration)
@api_view(['POST'])
@permission_classes([AllowAny])
def driver_register(request):
    # Initialize the serializer with the incoming data
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()  # This will save the user as either 'driver' or 'user'
        payload = {
            "id": str(user.id)  # Add role info to payload (driver or user)
        }

        token = JWTAuthentication.generate_token(payload=payload)
        refresh_token = JWTAuthentication.generate_refresh_token(payload=payload)

        return Response({
            'accessToken': token,
            'refreshToken': refresh_token
        }, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    token = request.data.get("fcm_token")
    driver = request.user

    if token:
        driver.fcm_token = token
        driver.driver_online = True
        driver.driver_available = True
        driver.save()

        print(f"{driver.name} online")

        return Response({"message": "Token saved"}, status=200)
    return Response({"error": "Token missing"}, status=400)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def driver_vehicle(request):
    serializer = VehicleSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def upload_license(request):
    user = request.user
    serializer = LicenseUploadSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "License uploaded successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def driver_offline(request):
    driver = request.user
    driver.driver_available = False
    driver.driver_online = False
    driver.save()
    print(f"{driver.name} is offline")
    return Response({"status": "driver marked offline"}, status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        new_password = serializer.validated_data['newPassword']
        old_password = serializer.validated_data['oldPassword']

        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password has been updated successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)