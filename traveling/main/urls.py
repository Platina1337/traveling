from django.urls import path
from .views import (
    MainView, ProfileUserView, ProfileView, CatalogView,
    get_trip_details, get_trip_details_profile, register,
    activate_account, add_comment, login_view, city_suggestions,
    logout_view, add_trip, calculate_route, remove_passenger,
    add_passenger, handle_passenger_request, delete_trip,
    leave_trip, start_trip, end_trip, change_password,
    resend_verification, delete_car, edit_car, get_car_models,
    get_car_details, trip_details, get_all_trips_statuses,
    check_car_active_trips
)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', MainView.as_view(), name='main'),
    path('get_trip_details/<int:trip_id>/', get_trip_details, name='get_trip_details'),
    path('get_trip_details_profile/<int:trip_id>/', get_trip_details_profile, name='get_trip_details_profile'),
    path('register/', register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', activate_account, name='activate_account'),
    path('profile_user/', ProfileUserView.as_view(), name='profile_user'),
    path('add_comment/', add_comment, name='add_comment'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('login/', login_view, name='login'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('city_suggestions/', city_suggestions, name='city_suggestions'),
    path('logout/', logout_view, name='logout'),
    path('add_trip/', add_trip, name='add_trip'),
    path('calculate_route/', calculate_route, name='calculate_route'),
    path('remove_passenger/', remove_passenger, name='remove_passenger'),
    path('add_passenger/<int:trip_id>/', add_passenger, name='add_passenger'),
    path('handle_passenger_request/<int:notification_id>/<str:action>/', handle_passenger_request, name='handle_passenger_request'),
    path('remove_passenger/<int:trip_id>/', remove_passenger, name='remove_passenger'),
    path('delete_trip/<int:trip_id>/', delete_trip, name='delete_trip'),
    path('leave_trip/<int:trip_id>/', leave_trip, name='leave_trip'),
    path('start_trip/<int:trip_id>/', start_trip, name='start_trip'),
    path('end_trip/<int:trip_id>/', end_trip, name='end_trip'),
    path('change_password/', change_password, name='change_password'),
    path('resend_verification/', resend_verification, name='resend_verification'),
    path('delete_car/<int:car_id>/', delete_car, name='delete_car'),
    path('edit_car/<int:car_id>/', edit_car, name='edit_car'),
    path('get_car_models/', get_car_models, name='get_car_models'),
    path('get_car_details/<int:car_id>/', get_car_details, name='get_car_details'),
    path('trip_details/<int:trip_id>/', trip_details, name='trip_details'),
    path('get_all_trips_statuses/', get_all_trips_statuses, name='get_all_trips_statuses'),
    path('check_car_active_trips/<int:car_id>/', check_car_active_trips, name='check_car_active_trips'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)