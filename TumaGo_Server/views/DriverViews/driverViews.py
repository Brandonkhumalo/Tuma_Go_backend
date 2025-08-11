from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .pagination import DeliveryCursorPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ...serializers.driverSerializer.authSerializers import UserSerializer
from ...serializers.driverSerializer.rideSerializers import DeliverySerializer
from ...models import DriverFinances, DriverVehicle, TripRequest, Delivery, CustomUser
from .deliveryMatching.delivery import driver_found
import googlemaps
from django.conf import settings
from TumaGo.firebase_init import initialize_firebase
from datetime import date, timedelta
from django.db.models import Sum
from .deliveryMatching.tasks import retry_trip_matching
from decimal import Decimal
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)
initialize_firebase()

gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)  # or str(obj), depending on your preference
    else:
        return obj

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_driver_data(request):
    user = request.user
    driver_data = UserSerializer(user)
    if DriverVehicle.objects.filter(driver=user).exists():

        driver_vehicles = DriverVehicle.objects.filter(driver=user)

        if driver_vehicles.count() > 1:
            # Keep the first one, delete the rest
            first_vehicle = driver_vehicles.first()
            driver_vehicles.exclude(id=first_vehicle.id).delete()
            print("deleted")
        
        return Response(driver_data.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getDriver_Finances(request):
    user = request.user
    
    today = date.today()
    weekday = today.weekday()  # Monday=0, Sunday=6

# Shift so Sunday is the start of the week
# Convert weekday to have Sunday=0, Monday=1, ..., Saturday=6
    sunday_start_offset = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=sunday_start_offset)
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    # For month_end, we get the last day of the month
    import calendar
    last_day = calendar.monthrange(today.year, today.month)[1]
    month_end = today.replace(day=last_day)

    # Aggregations:
    # Filter by driver and date range for each period, then sum earnings, charges, profit and trips

    def aggregate_period(start_date, end_date):
        qs = DriverFinances.objects.filter(
            driver=user,
            month_start__lte=end_date,
            month_end__gte=start_date
        )
        return qs.aggregate(
            earnings=Sum('earnings') or 0,
            charges=Sum('charges') or 0,
            profit=Sum('profit') or 0,
            total_trips=Sum('total_trips') or 0,
        )

    # Today (exact today match)
    today_data = DriverFinances.objects.filter(driver=user, today=today).aggregate(
        earnings=Sum('earnings') or 0,
        charges=Sum('charges') or 0,
        profit=Sum('profit') or 0,
        total_trips=Sum('total_trips') or 0,
    )

    week_data = aggregate_period(week_start, week_end)
    month_data = aggregate_period(month_start, month_end)

    # All time totals (no date filter)
    all_time = DriverFinances.objects.filter(driver=user).aggregate(
        earnings=Sum('earnings') or 0,
        charges=Sum('charges') or 0,
        profit=Sum('profit') or 0,
        total_trips=Sum('total_trips') or 0,
    )

    return Response({
        "today": today_data,
        "week": week_data,
        "month": month_data,
        "all_time": all_time,
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def RequestDelivery(request):
    delivery_serializer = DeliverySerializer(data=request.data)
    if delivery_serializer.is_valid():
        user = request.user
        delivery_data = delivery_serializer.validated_data
        user_id = user.id

        # Convert Decimal to float recursively before saving
        delivery_data_clean = convert_decimal(delivery_data)

        # Save Trip to DB
        trip = TripRequest.objects.create(
            requester=user,
            delivery_details=delivery_data_clean,
        )

        # Launch background countdown task with trip ID
        try:
            retry_trip_matching.send(str(trip.id), str(user_id), delivery_data_clean, countdown_seconds=10)
        except Exception as e:
            logger.error(f"Failed to start background task: {e}")

        return Response({"Looking ": "Awaiting driver"}, status=status.HTTP_200_OK)
    else:
        return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AcceptTrip(request):

    print("Trip Accepted")

    trip_id = request.data.get("trip_id")
    driver_id = request.user.id
    Driver = get_object_or_404(CustomUser, id=driver_id)

    try:
        trip = TripRequest.objects.get(id=trip_id)
        trip.accepted = True
        trip.save()

        delivery_data = trip.delivery_details
        driver = request.user
        client = trip.requester

        origin_lng = delivery_data.get("origin_lng")
        origin_lat = delivery_data.get("origin_lat")
        destination_lat = delivery_data.get("destination_lat")
        destination_lng = delivery_data.get("destination_lng")
        vehicle = delivery_data.get("vehicle")
        fare = delivery_data.get("fare")
        payment_method = delivery_data.get("payment_method")

        delivery = Delivery.objects.create(
            driver=driver,
            client=client,
            start_time=timezone.now(),
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            vehicle=vehicle,
            fare=fare,
            payment_method=payment_method
        )

        # ✅ Get driver's vehicle
        driver_vehicle = DriverVehicle.objects.filter(driver=driver).first()
        if not driver_vehicle:
            print('error Driver vehicle not found')
            return Response({'error': 'Driver vehicle not found'}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Build delivery payload (driver details + vehicle)
        deliveryData = {
            "driver": f"{driver.name.capitalize()} {driver.surname.capitalize()}",
            "delivery_vehicle": driver_vehicle.delivery_vehicle,
            "vehicle_name": driver_vehicle.car_name,
            "number_plate": driver_vehicle.number_plate,
            "vehicle_model": driver_vehicle.vehicle_model,
            "color": driver_vehicle.color,
            "rating":driver.rating,
            "total_ratings":driver.rating_count,
        }

        driver_found(client, deliveryData, str(delivery.delivery_id))
        print("sent to client")

        # Ensure the user is a driver before updating availability
        if Driver.role == CustomUser.DRIVER:
            Driver.driver_available = False
            Driver.save()
            return Response({'message': 'Driver availability set to false', 
                             'delivery_id': str(delivery.delivery_id)},
                             status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'error': 'User is not a driver'}, status=status.HTTP_400_BAD_REQUEST)

    except TripRequest.DoesNotExist:
        print("Trip not found.")
        return Response({"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        import traceback
        print("Unhandled exception occurred:")
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def end_trip(request):
    delivery_id = request.data.get("delivery_id")
    rating_received = request.data.get("rating")
    delivery_cost = request.data.get("delivery_cost")
    driver = request.user

    Driver_id = request.user.id
    Driver = get_object_or_404(CustomUser, id=Driver_id)

    delivery = get_object_or_404(Delivery, delivery_id=delivery_id)
    client = delivery.client
    client_id = str(client.id)

    if not delivery_id or not client_id or rating_received is None:
        return Response({"error": "delivery_id is required"},
                        {"error": "rating is required"},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        driver_vehicle = delivery.vehicle
        rating = Decimal(str(rating))

        client = CustomUser.objects.get(id=client_id, role=CustomUser.USER)

        # Update the client's rating by adding
        if not hasattr(client, 'rating_count') or client.rating_count is None:
            client.rating_count = 1
            client.rating = rating_received
        else:
            total_rating = client.rating * client.rating_count
            client.rating_count += 1
            client.rating = (total_rating + rating_received) / client.rating_count
        client.save()
        
        # Update fields
        delivery.end_time = timezone.now()
        delivery.successful = True
        delivery.save()

        earnings = Decimal(delivery_cost)
        if driver_vehicle and driver_vehicle.lower() == "scooter":
            charges = 0.20
        elif driver_vehicle and driver_vehicle.lower() == "van":
            charges = 0.30
        elif driver_vehicle and driver_vehicle.lower() == "truck":
            charges = 0.50
        else:
            charges = 0.10

        finances = DriverFinances( earnings, charges, driver=driver)
        finances.save()

        if Driver.role == CustomUser.DRIVER:
            Driver.driver_available = True
            Driver.save()
            return Response({'message': 'Driver availability set to false'}, 
                            {"message": "Trip ended successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User is not a driver'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Delivery.DoesNotExist:
        return Response({"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deliveries(request):
    user = request.user

    # Get deliveries related to the user (as client or driver)
    deliveries = Delivery.objects.filter(
    Q(client=user) | Q(driver=user)).order_by('-start_time')  # Optional: latest first ..... must match ordering in pagination class

    # Paginate
    paginator = DeliveryCursorPagination()
    result_page = paginator.paginate_queryset(deliveries, request)
    serializer = DeliverySerializer(result_page, many=True)
    print(serializer.data)
    return paginator.get_paginated_response(serializer.data)