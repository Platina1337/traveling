from rest_framework import serializers
from .models import Trip, City, Car, UserProfile, CarBrand, CarModel

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name']

class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrand
        fields = ['id', 'name']

class CarModelSerializer(serializers.ModelSerializer):
    brand = CarBrandSerializer()
    
    class Meta:
        model = CarModel
        fields = ['id', 'name', 'brand']

class CarSerializer(serializers.ModelSerializer):
    brand = CarBrandSerializer()
    model = CarModelSerializer()
    
    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'color', 'license_plate', 'image']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'avatar', 'phone_number', 'email']

class TripSerializer(serializers.ModelSerializer):
    departure_city = CitySerializer()
    destination_city = CitySerializer()
    car = CarSerializer()
    passengers = UserProfileSerializer(many=True)
    pending_passengers = UserProfileSerializer(many=True)
    user = UserProfileSerializer()
    start_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", required=False)

    class Meta:
        model = Trip
        fields = ['trip_id', 'user', 'departure_city', 'destination_city', 'car', 
                 'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
                 'passengers', 'max_passengers', 'price', 'comment', 'pending_passengers',
                 'status', 'start_time', 'end_time', 'trip_started', 'trip_ended'] 