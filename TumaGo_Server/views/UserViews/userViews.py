from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from ...serializers.userSerializer.authserializers import UserSerializer
from decimal import Decimal
from ...models import Delivery, CustomUser
from firebase_admin import messaging
from TumaGo.firebase_init import initialize_firebase
from django.shortcuts import get_object_or_404

initialize_firebase()

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def GetUserData(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([AllowAny])
def GetTripExpenses(request):
    try:
        distance = request.query_params.get("distance", None)

        if distance is None:
            return Response({"error": "Distance parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            distance = float(distance)
        except ValueError:
            return Response({"error": "Invalid distance value."}, status=status.HTTP_400_BAD_REQUEST)

        if distance <= 0:
            return Response({"error": "Distance must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)

        scooterPrice = round(Decimal(0.50 * distance) + Decimal(0.20), 2)
        vanPrice = round(Decimal(1.10 * distance) + Decimal(0.30), 2)
        truckPrice = round(Decimal(2.30 * distance) + Decimal(0.50), 2)

        fare = {
            "scooter": scooterPrice,
            "van": vanPrice,
            "truck": truckPrice
        }

        return Response(fare, status=status.HTTP_200_OK)

    except (TypeError, ValueError):
        return Response({"error": "Invalid distance or time parameters."}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_delivery(request):
    user = request.user
    delivery_id = request.query_params.get("delivery_id")

    if not delivery_id:
        return Response({"error": "delivery_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        delivery = Delivery.objects.get(delivery_id=delivery_id)
        delivery.successful = False
        delivery.save()

        driver = delivery.driver
        driver.driver_available = True
        driver.save()

        client = delivery.client
        client_name = client.name
        client_surname = client.surname

        update_driver_delivery_cancelled(driver, client_name, client_surname)

        return Response({"message": "Delivery cancelled."}, status=status.HTTP_200_OK)
    except Delivery.DoesNotExist:
        return Response({"error": "Delivery not found."}, status=status.HTTP_404_NOT_FOUND)
    
def update_driver_delivery_cancelled(driver, name, surname):
    if not driver.fcm_token:
        return 
    
    message = messaging.Message(
        token=driver.fcm_token,
        data={
            "type": "delivery_cancelled",
        },
        notification=messaging.Notification(
            title="Delivery Cancelled",
            body=f"by {name} {surname}",
        )
    )

    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        print(f"Error sending FCM message: {e}")
        return False
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_driver(request):
    delivery_id = request.data.get("delivery_id")
    rating_received = request.data.get("rating")

    delivery = get_object_or_404(Delivery, delivery_id=delivery_id)
    driver = delivery.driver
    driver_id = str(driver.id)

    if not delivery_id or not driver_id or rating_received is None:
        return Response({"error": "delivery_id is required"},
                        {"error": "rating is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        rating = Decimal(str(rating))

        driver = CustomUser.objects.get(id=driver_id, role=CustomUser.USER)

        # Update the driver's rating by adding
        if not hasattr(driver, 'rating_count') or driver.rating_count is None:
            driver.rating_count = 1
            driver.rating = rating_received
        else:
            total_rating = driver.rating * driver.rating_count
            driver.rating_count += 1
            driver.rating = (total_rating + rating_received) / driver.rating_count
        driver.save()

    except Delivery.DoesNotExist:
        return Response({"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)