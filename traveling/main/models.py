from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_date = models.DateField(blank=True, null=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100)
    about_me = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    is_active = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class CarBrand(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Car(models.Model):
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='cars')
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name='cars')
    color = models.CharField(max_length=255, blank=True, null=True)
    license_plate = models.CharField(max_length=20, blank=True, null=True, unique=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cars')

    def __str__(self):
        return f"{self.brand.name} {self.model.name} ({self.license_plate})"

class City(models.Model):
    name = models.CharField(max_length=255)


    def __str__(self):
        return f"{self.name}"

class Comment(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='received_comments')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='authored_comments')
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

class Trip(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    departure_city = models.ForeignKey(City, related_name='departure_city', on_delete=models.CASCADE)
    destination_city = models.ForeignKey(City, related_name='destination_city', on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name='trip_car', on_delete=models.CASCADE)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField(null=True, blank=True)
    arrival_time = models.TimeField()
    passengers = models.ManyToManyField(UserProfile, related_name='trip_passengers', blank=True)
    max_passengers = models.PositiveIntegerField(default=4)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.TextField(blank=True, null=True)
    pending_passengers = models.ManyToManyField(UserProfile, related_name='pending_trips', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def has_active_trip(self):
        return Trip.objects.filter(user=self, status__in=['planned', 'in_progress']).exists()

    def start_trip(self):
        """Начать поездку и сохранить время начала в UTC"""
        self.status = 'in_progress'
        self.start_time = timezone.now()
        self.save(update_fields=['status', 'start_time'])

    def end_trip(self):
        """Завершить поездку и сохранить время завершения в UTC"""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'end_time'])

    @property
    def duration(self):
        if self.arrival_date and self.arrival_time:
            departure_datetime = datetime.combine(self.departure_date, self.departure_time)
            arrival_datetime = datetime.combine(self.arrival_date, self.arrival_time)
            return arrival_datetime - departure_datetime
        return None

    @property
    def actual_duration(self):
        """Возвращает фактическую продолжительность поездки"""
        if self.start_time:
            if self.end_time:
                return self.end_time - self.start_time
            elif self.status == 'in_progress':
                return timezone.now() - self.start_time
        return None

    @property
    def actual_duration_hours(self):
        duration = self.actual_duration
        if duration:
            return duration.days * 24 + duration.seconds // 3600
        return None

    @property
    def actual_duration_minutes(self):
        duration = self.actual_duration
        if duration:
            return (duration.seconds // 60) % 60
        return None

    @property
    def actual_duration_seconds(self):
        duration = self.actual_duration
        if duration:
            return duration.seconds % 60
        return None

    @property
    def actual_duration_string(self):
        hours = self.actual_duration_hours
        minutes = self.actual_duration_minutes
        seconds = self.actual_duration_seconds
        if hours is not None and minutes is not None and seconds is not None:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None

    @property
    def is_full(self):
        return self.passengers.count() >= self.max_passengers

    def __str__(self):
        return f"Trip from {self.departure_city} to {self.destination_city} on {self.departure_date}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('request', 'Запрос на присоединение'),
        ('accept', 'Запрос принят'),
        ('decline', 'Запрос отклонен'),
        ('success', 'Успешное действие'),
        ('warning', 'Предупреждение'),
        ('info', 'Информационное сообщение'),
        ('start', 'Поездка началась'),
        ('end', 'Поездка завершена'),
        ('removed', 'Удаление из поездки'),
    ]

    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')

    def __str__(self):
        return f"Notification for {self.recipient}: {self.message}"

    def is_request(self):
        return self.notification_type == 'request'