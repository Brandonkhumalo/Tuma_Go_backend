from ....models import DriverLocations, DriverVehicle
from firebase_admin import messaging
from TumaGo.firebase_init import initialize_firebase
import googlemaps
from django.conf import settings
gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

initialize_firebase()

def TripData(requester_data, delivery_data, trip_id):
    destination_lat = delivery_data['destination_lat']
    destination_lng = delivery_data['destination_lng']
    requester_lng = delivery_data['origin_lng']
    requester_lat = delivery_data['origin_lat']
    requested_vehicle_type = delivery_data['vehicle']
    cost = delivery_data['fare']

    requester_name = f"{requester_data['name']} {requester_data['surname']}"
    requester_coords = f"{delivery_data['origin_lat']},{delivery_data['origin_lng']}"

    driver_locations = DriverLocations.objects.select_related('driver').all()

    closest_driver = None
    shortest_distance = float('inf')
    closest_driver_coords = None

    for driver_loc in driver_locations:
        driver = driver_loc.driver

        # Get driver's delivery vehicle and check if it matches
        try:
            driver_vehicle = DriverVehicle.objects.get(driver=driver)
            if driver_vehicle.delivery_vehicle != requested_vehicle_type:
                continue  # Skip if vehicle type doesn't match
        except DriverVehicle.DoesNotExist:
            continue  # Skip if driver has no vehicle

        # Check driver availability directly
        if not driver.driver_available:
            continue

        if driver_loc.latitude and driver_loc.longitude:
            driver_coords = f"{driver_loc.latitude},{driver_loc.longitude}"

            try:
                result = gmaps.distance_matrix(
                    origins=[requester_coords],
                    destinations=[driver_coords],
                    mode='driving'
                )

                distance_info = result['rows'][0]['elements'][0]
                if distance_info['status'] == 'OK':
                    distance = distance_info['distance']['value']  # meters

                    if distance < shortest_distance:
                        shortest_distance = distance
                        closest_driver = driver
                        closest_driver_coords = {
                            "latitude": driver_loc.latitude,
                            "longitude": driver_loc.longitude
                        }

            except Exception as e:
                print(f"Error calculating distance for driver {driver.id}: {e}")

    if closest_driver:
        payload = {
            "driver_name": f"{closest_driver.name} {closest_driver.surname}",
            "email": closest_driver.email,
            "coordinates": closest_driver_coords,
            "distance_meters": shortest_distance,
            "requester_Name": requester_name,
            "destination_lat": destination_lat,
            "destination_lng": destination_lng,
            "requester_lng": requester_lng,
            "requester_lat": requester_lat,
            "cost": cost,
        }

        print("Driver found:", closest_driver.name)
        send_request_to_driver(closest_driver, payload, trip_id)
        return payload

    print("No valid drivers found.")
    return None
    
def send_request_to_driver(driver, request_payload, trip_id):
    if not driver.fcm_token:
        return False

    message = messaging.Message(
        token=driver.fcm_token,
        data={
            "type": "new_request",
            "requester_name": request_payload["requester_Name"],
            "destination_lat": str(request_payload["destination_lat"]),
            "destination_lng": str(request_payload["destination_lng"]),
            "requester_lng": str(request_payload["requester_lng"]),
            "requester_lat": str(request_payload["requester_lat"]),
            "distance_meters": str(request_payload["distance_meters"]),
            "cost": str(request_payload["cost"]),
            "trip_id": str(trip_id),
        },
        notification=messaging.Notification(
            title="New Delivery Request",
            body=f"{request_payload['requester_Name']} needs a ride nearby!",
        )
    )

    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        print(f"Error sending FCM message: {e}")
        return False
    
def driver_found(user, delivery_payload, delivery_id):
    if not user.fcm_token:
        return
    
    message = messaging.Message(
        token=user.fcm_token,
        data={
            "type": "driver_found",
            "driver_name": delivery_payload.get("driver", ""),
            "vehicle": str(delivery_payload["delivery_vehicle"]),
            "vehicle_name": str(delivery_payload["vehicle_name"]),
            "number_plate": str(delivery_payload["number_plate"]),
            "vehicle_model": str(delivery_payload["vehicle_model"]),
            "color": str(delivery_payload["color"]),
            "delivery_id": str(delivery_id),
            "rating": str(delivery_payload["rating"]),
            "total_ratings": str(delivery_payload["total_ratings"]),
        },
        notification=messaging.Notification(
            title="Driver Found",
            body=f"A driver has accepted your request!",
        )
    )

    try:
        response = messaging.send(message)
        print(f"Driver found notification sent successfully: {response}")
    except Exception as e:
        print(f"Failed to send FCM notification: {e}")
    
def no_driver_found(user):
    """
    Send an FCM notification to the user informing them that no drivers were found.
    """
    if not user.fcm_token:
        print("User has no FCM token. Cannot send notification.")
        return

    # Construct the message
    message = messaging.Message(
        notification=messaging.Notification(
            title="No Drivers Found",
            body="We couldn’t find an available driver at the moment. Please try again shortly."
        ),
        token=user.fcm_token,
        data={
            "type": "no_driver_found",
        }
    )

    try:
        response = messaging.send(message)
        print(f"FCM no driver found notification sent successfully: {response}")
    except Exception as e:
        print(f"Failed to send FCM notification: {e}")