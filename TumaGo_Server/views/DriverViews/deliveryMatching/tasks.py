import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TumaGo.settings")
django.setup()

import time
from decimal import Decimal
import dramatiq
from dramatiq.middleware import Retries
from dramatiq.errors import Retry
from ....models import TripRequest, CustomUser
from ....serializers.userSerializer.authserializers import UserSerializer

def convert_to_decimal(obj):
    if isinstance(obj, list):
        return [convert_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


@dramatiq.actor(max_retries=4, retry_when=lambda retries, e: True)
def retry_trip_matching(trip_id, user_id, delivery_data, countdown_seconds=10):

    print("Loaded retry_trip_matching with retry_when taking 2 args")

    try:
        # Convert delivery_data floats back to Decimal
        delivery_data = convert_to_decimal(delivery_data)

        # Fetch the trip
        trip = TripRequest.objects.get(id=trip_id)

        # Stop if already accepted
        if trip.accepted:
            print("Trip accepted! Task complete.")
            return

        # Wait countdown period, checking if trip gets accepted
        for _ in range(countdown_seconds):
            trip.refresh_from_db()
            if trip.accepted:
                print("Trip accepted during countdown. Task complete.")
                return
            time.sleep(1)

        # Fetch user and serialize requester data freshly
        user = CustomUser.objects.get(id=user_id)
        requester_data = UserSerializer(user).data

        from ..deliveryMatching.delivery import TripData, no_driver_found
        # Retry driver matching logic with Decimal delivery_data
        print("Retrying TripData matching...")
        TripData(requester_data, delivery_data, trip_id)

        raise Retry()  # raise Retry to re-queue task immediately
    
    except Retry:
        raise

    except TripRequest.DoesNotExist:
        print("Trip not found. Aborting.")
        return None

    except CustomUser.DoesNotExist:
        print("User not found. Aborting.")
        return None

    except Exception as e:
        # Check for max retry exhaustion
        retries = retry_trip_matching.options["retries"]
        if retries >= 3:  
            print("Max retries reached. Notifying user no drivers were found.")
            try:
                user = CustomUser.objects.get(id=user_id)
                no_driver_found(user)
            except Exception as notify_error:
                print(f"Failed to notify user: {notify_error}")
        raise Retry()
