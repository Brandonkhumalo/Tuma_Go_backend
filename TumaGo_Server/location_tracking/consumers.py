import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class LocationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.scope['user'] = await self.get_user_from_token()
        print(f"Query string: {self.scope['query_string']}")
        print(f"User: {self.scope['user']}, Authenticated: {self.scope['user'].is_authenticated}")

        if self.scope['user'] and self.scope['user'].is_authenticated:
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            user = self.scope['user']

            if user and latitude and longitude:
                await self.save_location(user, latitude, longitude)
                print(print(f"{latitude} {longitude}"))
        except Exception as e:
            print("Error processing message:", e)

    @database_sync_to_async
    def save_location(self, user, lat, lng):
        from ..models import DriverLocations  # deferred import
        DriverLocations.objects.create(driver=user, latitude=str(lat), longitude=str(lng))
        print(f"Saving location for {user.email}: ({lat}, {lng})")

    @database_sync_to_async
    def get_user_from_token(self):
        from urllib.parse import parse_qs
        from django.contrib.auth.models import AnonymousUser
        from jwt import decode, InvalidTokenError, ExpiredSignatureError
        from django.conf import settings
        from django.contrib.auth import get_user_model
        from datetime import datetime

        User = get_user_model()

        try:
            query_string = self.scope['query_string'].decode()
            query_params = parse_qs(query_string)
            token = query_params.get("token", [None])[0]

            if not token:
                return AnonymousUser()

        # Decode and validate token
            payload = decode(token, key=settings.SECRET_KEY, algorithms=["HS256"])

        # Token expiry check
            if "exp" not in payload or int(datetime.utcnow().timestamp()) > payload["exp"]:
                raise ExpiredSignatureError("Token expired")

            if payload.get("type") != "access_token":
                raise InvalidTokenError("Invalid token type")

            user_id = payload.get("id")
            if not user_id:
                return AnonymousUser()

            return User.objects.get(id=user_id)

        except (InvalidTokenError, ExpiredSignatureError, User.DoesNotExist, Exception) as e:
            print(f"WebSocket Token Error: {e}")
        return AnonymousUser()