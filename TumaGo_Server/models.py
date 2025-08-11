from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from django.utils import timezone
from calendar import monthrange
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER = 'user'
    DRIVER = 'driver'

    ROLE_CHOICES = [
        (USER, 'User'),
        (DRIVER, 'Driver'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER, null=False)

    email = models.EmailField(unique=True, null=False)
    verifiedEmail = models.BooleanField(default=False)
    username = None  # Optional if using email login
    fcm_token = models.CharField(max_length=255, blank=True, null=True)

    remember = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=13, null=False)
    name = models.CharField(max_length=100, null=False)
    surname = models.CharField(max_length=50, null=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5, null=False, blank=False)
    rating_count = models.PositiveIntegerField(default=0)

    identity_number = models.CharField(max_length=20, null=True, blank=True)
    streetAdress = models.CharField(max_length=20, null=False)
    addressLine = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=20, null=False)
    province = models.CharField(max_length=20, null=False)
    postalCode = models.CharField(max_length=20, null=False)

    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    identity_picture = models.ImageField(upload_to='id_pictures/', null=True, blank=True)
    identity = models.BooleanField(default=False)
    license_picture = models.ImageField(upload_to='License/', null=True, blank=True) 
    license = models.BooleanField(default=False)

    driver_online = models.BooleanField(default=False)
    driver_available = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname', 'phone_number']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"
    
class BlacklistedToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted at {self.blacklisted_at}"
    
class TermsAndConditions(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='terms_and_conditions')
    terms_and_conditions = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)

class DriverLocations(models.Model):
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driver_locations')
    latitude = models.CharField(max_length=50, null=True, blank=True)
    longitude = models.CharField(max_length=50, null=True, blank=True)
    
class DriverFinances(models.Model):
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driver_finances')
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    month_start = models.DateField(null=True, blank=True)
    month_end = models.DateField(null=True, blank=True)
    week_start = models.DateField(null=True, blank=True)
    week_end = models.DateField(null=True, blank=True)
    today = models.DateField(null=True, blank=True)
    total_trips = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        self.today = today

        # Increment total_trips by 1 on every save - careful with this logic!
        if self.pk:
            previous = DriverFinances.objects.get(pk=self.pk)
            self.total_trips = previous.total_trips + 1
        else:
            self.total_trips = 1

        # Calculate week_start (previous Sunday) and week_end (Saturday)
        days_since_sunday = (today.weekday() + 1) % 7
        self.week_start = today - timedelta(days=days_since_sunday)
        self.week_end = self.week_start + timedelta(days=6)

        # Calculate month_start (1st day) and month_end (last day)
        self.month_start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        self.month_end = today.replace(day=last_day)

        # Calculate profit automatically
        self.profit = self.earnings - self.charges

        super().save(*args, **kwargs)

class DriverVehicle(models.Model):
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driver_vehicles')
    delivery_vehicle = models.CharField(max_length=50, null=False, blank=False)
    car_name = models.CharField(max_length=50, null=False, blank=False)
    number_plate = models.CharField(max_length=50, null=False, blank=False)
    color = models.CharField(max_length=50, null=False, blank=False)
    vehicle_model = models.CharField(max_length=50, null=False, blank=False)

class Delivery(models.Model):
    delivery_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driver_deliveries')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_deliveries')
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=True, blank=True)
    waiting_time = models.DateTimeField(null=True, blank=True)
    origin_lat = models.FloatField(null=True, blank=True)
    origin_lng = models.FloatField(null=True, blank=True)
    destination_lat = models.FloatField(null=True, blank=True)
    destination_lng = models.FloatField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    vehicle = models.CharField(max_length=50, null=True, blank=True)
    fare = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False)
    payment_method = models.CharField(max_length=50, null=False, blank=False)
    successful = models.BooleanField(default=True) #True is successful, False is unsuccessful

class TripRequest(models.Model):
    requester = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    delivery_details = models.JSONField() 
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)