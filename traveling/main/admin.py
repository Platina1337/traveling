from django.contrib import admin
from .models import *
# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserProfile._meta.fields]
admin.site.register(UserProfile, UserProfileAdmin)
class CityAdmin(admin.ModelAdmin):
    list_display = [field.name for field in City._meta.fields]
admin.site.register(City, CityAdmin)
class CarAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Car._meta.fields]
admin.site.register(Car, CarAdmin)
class TripAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Trip._meta.fields]
admin.site.register(Trip, TripAdmin)