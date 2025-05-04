from datetime import datetime, timedelta

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Min, Max
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

from .tasks import send_sms_task
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware
from django.views import View
from django.views.generic import DetailView, CreateView, ListView, TemplateView
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from .models import UserProfile, Trip, City, Car, Notification, Comment
from .forms import LoginForm, UserRegistrationForm, UserLoginForm, TripForm, UserProfileForm, CustomPasswordChangeForm, \
    CommentForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings


class MainView(View):
    template_name = 'main/main.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class ProfileUserView(View):
    template_name = 'main/enemy_profile.html'

    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')
        user_profile = get_object_or_404(UserProfile, id=user_id)

        current_user = request.user
        current_user_profile = get_object_or_404(UserProfile, user=current_user)

        # Проверяем, есть ли у текущего пользователя завершенные поездки с данным профилем
        trips = Trip.objects.filter(passengers=current_user_profile, status='completed', user=user_profile)
        trip_count = trips.count()

        # Если есть завершенные поездки, отображаем форму комментария
        if trips.exists():
            form = CommentForm()
        else:
            form = None

        comments = Comment.objects.filter(user_profile=user_profile)

        context = {
            'user_profile': user_profile,
            'comments': comments,
            'form': form,
            'trip_count': trip_count,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')
        user_profile = get_object_or_404(UserProfile, id=user_id)
        current_user = request.user
        current_user_profile = get_object_or_404(UserProfile, user=current_user)

        # Проверяем, есть ли у текущего пользователя завершенные поездки с данным профилем
        trips = Trip.objects.filter(passengers=current_user_profile, status='completed', user=user_profile)

        if trips.exists():
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.user_profile = user_profile
                comment.author = current_user.profile  # Предполагается, что у пользователя есть профиль
                comment.save()

        return redirect(request.path_info)

@require_POST
def add_comment(request, user_profile_id):
    user_profile = get_object_or_404(UserProfile, id=user_profile_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.user_profile = user_profile
        comment.save()

    return redirect('profile_user', user_profile_id=user_profile_id)
class AddTravelView(View):
    template_name = 'main/add_travel.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


def send_verification_email(user, request):
    """Отправляет письмо для верификации пользователя"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Формируем URL для верификации
    verification_url = request.build_absolute_uri(
        reverse('main:activate_account', kwargs={'uidb64': uid, 'token': token})
    )
    
    # Формируем сообщение для email
    email_message = f"""
    Здравствуйте, {user.first_name}!

    Спасибо за регистрацию на нашем сайте. Для активации вашего аккаунта, пожалуйста, перейдите по следующей ссылке:

    {verification_url}

    Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

    С уважением,
    Команда Название
    """
    
    # Отправляем email (в консоль для тестирования)
    print("\n=== Email Message ===")
    print(f"To: {user.email}")
    print(f"Subject: Подтверждение регистрации")
    print(f"Message:\n{email_message}")
    print("===================\n")
    
    return True

@require_POST
def resend_verification(request):
    """Обработчик для повторной отправки письма верификации"""
    email = request.POST.get('email')
    try:
        user = User.objects.get(email=email)
        # Проверяем только is_active в UserProfile, так как это наш основной индикатор активации
        try:
            profile = UserProfile.objects.get(user=user)
            if not profile.is_active:
                if send_verification_email(user, request):
                    return JsonResponse({
                        'success': True,
                        'message': 'Письмо с подтверждением отправлено на ваш email.'
                    })
            return JsonResponse({
                'success': False,
                'message': 'Аккаунт уже активирован.'
            })
        except UserProfile.DoesNotExist:
            # Если профиль не существует, создаем его и отправляем письмо
            profile = UserProfile.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                is_active=False
            )
            if send_verification_email(user, request):
                return JsonResponse({
                    'success': True,
                    'message': 'Письмо с подтверждением отправлено на ваш email.'
                })
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Пользователь с таким email не найден.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Произошла ошибка: {str(e)}'
        })

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Проверяем активность пользователя
                if not user.is_active:
                    messages.error(request, 'Пожалуйста, активируйте ваш аккаунт через email.')
                    # Добавляем в контекст информацию о возможности повторной отправки
                    return render(request, 'main/login.html', {
                        'form': form,
                        'show_resend': True,
                        'email': email
                    })
                
                # Проверяем наличие и активность профиля
                try:
                    profile = UserProfile.objects.get(user=user)
                    if not profile.is_active:
                        messages.error(request, 'Пожалуйста, активируйте ваш аккаунт через email.')
                        return render(request, 'main/login.html', {
                            'form': form,
                            'show_resend': True,
                            'email': email
                        })
                except UserProfile.DoesNotExist:
                    # Если профиль не существует, создаем его
                    profile = UserProfile.objects.create(
                        user=user,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        is_active=user.is_active
                    )
                
                login(request, user)
                return redirect('main:main')
            else:
                form.add_error(None, 'Неверная почта или пароль')
    else:
        form = LoginForm()
    return render(request, 'main/login.html', {'form': form})

import logging



@require_POST
def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user.userprofile)
    trip.delete()
    return JsonResponse({'success': True})

@require_POST
def leave_trip(request, trip_id):
    profile = get_object_or_404(UserProfile, user=request.user)
    trip = get_object_or_404(Trip, id=trip_id)
    trip.passengers.remove(profile)
    return JsonResponse({'success': True})

def logout_view(request):
    logout(request)
    return redirect('main:login')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Важно для сохранения сессии
            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'main/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            try:
                change_password_form = CustomPasswordChangeForm(user=user)
                profile = get_object_or_404(UserProfile, user=user)
                trips = Trip.objects.filter(user=profile).exclude(status='completed').order_by('-status')
                joined_trips = Trip.objects.filter(passengers=profile).exclude(user=profile).exclude(status='completed').order_by('-status')

                all_trips = []

                def calculate_duration(departure_date, departure_time, arrival_date, arrival_time):
                    departure_datetime = make_aware(datetime.combine(departure_date, departure_time))
                    arrival_datetime = make_aware(datetime.combine(arrival_date, arrival_time))
                    duration = arrival_datetime - departure_datetime
                    duration_hours = duration.days * 24 + duration.seconds // 3600
                    duration_minutes = (duration.seconds % 3600) // 60
                    return duration_hours, duration_minutes

                for trip in trips:
                    if trip.departure_date and trip.departure_time and trip.arrival_date and trip.arrival_time:
                        duration_hours, duration_minutes = calculate_duration(
                            trip.departure_date, trip.departure_time, trip.arrival_date, trip.arrival_time
                        )
                        trip_info = {
                            'trip': trip,
                            'duration_hours': duration_hours,
                            'duration_minutes': duration_minutes,
                            'user_trip': True
                        }
                        all_trips.append(trip_info)

                for trip in joined_trips:
                    if trip.departure_date and trip.departure_time and trip.arrival_date and trip.arrival_time:
                        duration_hours, duration_minutes = calculate_duration(
                            trip.departure_date, trip.departure_time, trip.arrival_date, trip.arrival_time
                        )
                        trip_info = {
                            'trip': trip,
                            'duration_hours': duration_hours,
                            'duration_minutes': duration_minutes,
                            'user_trip': False
                        }
                        all_trips.append(trip_info)

                paginator = Paginator(all_trips, 3)
                page = self.request.GET.get('page', 1)

                try:
                    paginated_trips = paginator.page(page)
                except PageNotAnInteger:
                    paginated_trips = paginator.page(1)
                except EmptyPage:
                    paginated_trips = paginator.page(paginator.num_pages)

                form = UserProfileForm(initial={
                    'first_name': profile.first_name,
                    'last_name': profile.last_name,
                    'phone_number': profile.phone_number,
                    'email': profile.email,
                    'about_me': profile.about_me,
                })
                notifications = Notification.objects.filter(recipient=profile)
                context['profile'] = profile
                context['paginated_trips'] = paginated_trips
                context['form'] = form
                context['change_password_form'] = change_password_form
                context['notifications'] = notifications

            except ValueError as e:
                logging.error(f"Error in ProfileView: {e}")
                context['profile'] = None
                context['paginated_trips'] = []
                context['notifications'] = []

        return context

    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(UserProfile, user=request.user)
        form = UserProfileForm(request.POST, request.FILES)

        if form.is_valid():
            profile.first_name = form.cleaned_data['first_name']
            profile.last_name = form.cleaned_data['last_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.email = form.cleaned_data['email']
            profile.about_me = form.cleaned_data['about_me']
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            profile.save()
            messages.success(request, 'Ваш профиль был обновлен.')
        else:
            messages.error(request, 'Произошла ошибка при обновлении вашего профиля.')

        return redirect('main:profile')


logger = logging.getLogger(__name__)


def start_trip(request, trip_id):
    if request.method == 'POST':
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user == trip.user.user:
            active_trip = Trip.objects.filter(user=trip.user, status='in_progress').exists()
            if active_trip:
                logger.warning(f"User {request.user.id} attempted to start trip {trip_id} but already has an active trip.")
                return JsonResponse({'success': False, 'message': 'У вас уже есть активная поездка'})

            trip.started_at = timezone.now()
            trip.status = 'in_progress'
            trip.save()
            logger.info(f"Trip {trip_id} started by user {request.user.id}.")

            for passenger in trip.passengers.all():
                Notification.objects.create(
                    recipient=passenger,
                    sender=request.user.userprofile,
                    trip=trip,
                    message=f"Поездка {trip.departure_city.name} -> {trip.destination_city.name} началась"
                )
            return JsonResponse({'success': True})
        else:
            logger.warning(f"User {request.user.id} attempted to start trip {trip_id} but is not the driver.")
            return JsonResponse({'success': False, 'message': 'Вы не являетесь водителем этой поездки'})
    return JsonResponse({'success': False, 'message': 'Неверный метод'})

def end_trip(request, trip_id):
    if request.method == 'POST':
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user == trip.user.user:
            if trip.status != 'in_progress':
                logger.warning(f"User {request.user.id} attempted to end trip {trip_id} which is not in progress.")
                return JsonResponse({'success': False, 'message': 'Поездка еще не началась'})

            trip.status = 'completed'
            trip.save()
            logger.info(f"Trip {trip_id} completed by user {request.user.id}.")

            for passenger in trip.passengers.all():
                Notification.objects.create(
                    recipient=passenger,
                    sender=request.user.userprofile,
                    trip=trip,
                    message=f"Поездка {trip.departure_city.name} -> {trip.destination_city.name} завершена"
                )
            return JsonResponse({'success': True})
        else:
            logger.warning(f"User {request.user.id} attempted to end trip {trip_id} but is not the driver.")
            return JsonResponse({'success': False, 'message': 'Вы не являетесь водителем этой поездки'})
    return JsonResponse({'success': False, 'message': 'Неверный метод'})


from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.db.models import Min, Max
from datetime import datetime

class CatalogView(ListView):
    model = Trip
    template_name = 'main/catalog.html'
    context_object_name = 'trips'

    def get_queryset(self):
        queryset = super().get_queryset()
        departure_city = self.request.GET.get('departure_city')
        destination_city = self.request.GET.get('destination_city')
        date = self.request.GET.get('date')
        passengers = self.request.GET.get('passengers')
        price_min = self.request.GET.get('price_min', 0)
        price_max = self.request.GET.get('price_max', 15000)

        if self.request.user.is_authenticated:
            current_user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.exclude(user=current_user_profile)

        if departure_city:
            queryset = queryset.filter(departure_city__name=departure_city)
        if destination_city:
            queryset = queryset.filter(destination_city__name=destination_city)
        if date:
            queryset = queryset.filter(departure_date=date)
        if passengers:
            queryset = queryset.filter(max_passengers=passengers)
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def calculate_duration(departure_date, departure_time, arrival_date, arrival_time):
            departure_datetime = make_aware(datetime.combine(departure_date, departure_time))
            arrival_datetime = make_aware(datetime.combine(arrival_date, arrival_time))
            duration = arrival_datetime - departure_datetime
            duration_hours = duration.days * 24 + duration.seconds // 3600
            duration_minutes = (duration.seconds % 3600) // 60
            return duration_hours, duration_minutes

        trips = context['trips']
        trips_with_duration = []
        for trip in trips:
            if trip.departure_date and trip.departure_time and trip.arrival_date and trip.arrival_time:
                duration_hours, duration_minutes = calculate_duration(
                    trip.departure_date, trip.departure_time, trip.arrival_date, trip.arrival_time
                )
                trip_info = {
                    'trip': trip,
                    'duration_hours': duration_hours,
                    'duration_minutes': duration_minutes,
                }
                trips_with_duration.append(trip_info)

        min_price = Trip.objects.all().aggregate(Min('price'))['price__min'] or 0
        max_price = Trip.objects.all().aggregate(Max('price'))['price__max'] or 15000

        context['cities'] = City.objects.all()
        context['selected_departure_city'] = self.request.GET.get('departure_city', '')
        context['selected_destination_city'] = self.request.GET.get('destination_city', '')
        context['selected_date'] = self.request.GET.get('date', '')
        context['selected_passengers'] = self.request.GET.get('passengers', '')
        context['selected_price_min'] = self.request.GET.get('price_min', min_price)
        context['selected_price_max'] = self.request.GET.get('price_max', max_price)
        context['min_price'] = min_price
        context['max_price'] = max_price
        context['trips_with_duration'] = trips_with_duration

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            trips = context['trips_with_duration']
            trips_data = [
                {
                    'id': trip['trip'].id,
                    'car_image_url': trip['trip'].car.image.url if trip['trip'].car.image else static('img/defolt.png'),
                    'car_brand': trip['trip'].car.brand,
                    'car_model': trip['trip'].car.model,
                    'departure_time': trip['trip'].departure_time.strftime('%H:%M'),
                    'arrival_time': trip['trip'].arrival_time.strftime('%H:%M'),
                    'duration_hours': trip['duration_hours'],
                    'duration_minutes': trip['duration_minutes'],
                    'price': trip['trip'].price,
                }
                for trip in trips
            ]
            return JsonResponse({'trips': trips_data}, safe=False)
        else:
            return super().render_to_response(context, **response_kwargs)



logger = logging.getLogger(__name__)

def get_trip_details(request, trip_id):
    try:
        trip = get_object_or_404(Trip, id=trip_id)
        driver = trip.user

        trip_data = {
            'driver_id': driver.id,  # Добавляем driver_id
            'driver_name': driver.first_name,
            'driver_surname': driver.last_name,
            'driver_description': trip.comment if trip.comment else '',
            'driver_photo_url': driver.avatar.url if driver.avatar else '',
            'driver_rating': driver.rating if hasattr(driver, 'rating') else '',
            'departure_address': trip.departure_city.name,
            'departure_date': trip.departure_date.strftime('%Y-%m-%d'),
            'departure_time': trip.departure_time.strftime('%H:%M'),
            'passengers': trip.max_passengers,
            'destination_address': trip.destination_city.name,
            'arrival_date': trip.departure_date.strftime('%Y-%m-%d'),
            'arrival_time': trip.arrival_time.strftime('%H:%M'),
            'price': str(trip.price),  # Преобразуем Decimal в строку для JSON
            'comment': trip.comment,
        }
        return JsonResponse(trip_data)
    except Trip.DoesNotExist:
        return JsonResponse({'error': 'Trip not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)

def get_trip_details_profile(request, trip_id):
    try:
        trip = get_object_or_404(Trip, id=trip_id)
        driver = trip.user

        trip_data = {
            'driver_id': driver.id,  # Добавляем driver_id
            'driver_name': driver.first_name,
            'driver_surname': driver.last_name,
            'driver_description': trip.comment if trip.comment else '',
            'driver_photo': driver.avatar.url if driver.avatar else '',
            'departure_address': trip.departure_city.name,
            'departure_date': trip.departure_date.strftime('%Y-%m-%d'),
            'departure_time': trip.departure_time.strftime('%H:%M'),
            'destination_address': trip.destination_city.name,
            'arrival_date': trip.departure_date.strftime('%Y-%m-%d'),
            'arrival_time': trip.arrival_time.strftime('%H:%M'),
            'price': str(trip.price),
            'comment': trip.comment,
            'seats_taken': trip.passengers.count(),
            'total_seats': trip.max_passengers,
            'passengers': [{'id': p.id, 'name': p.first_name} for p in trip.passengers.all()],
            'status': trip.status  # Добавляем статус поездки
        }
        return JsonResponse(trip_data)
    except Trip.DoesNotExist:
        return JsonResponse({'error': 'Trip not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def remove_passenger(request):
    if request.method == 'POST':
        print('POST request received')

        trip_id = request.POST.get('trip_id')
        passenger_id = request.POST.get('passenger_id')

        print(f'trip_id: {trip_id}')
        print(f'passenger_id: {passenger_id}')

        if not trip_id or not passenger_id:
            return JsonResponse({'success': False, 'message': 'Missing trip_id or passenger_id'}, status=400)

        try:
            trip = Trip.objects.get(id=trip_id)
            passenger = UserProfile.objects.get(id=passenger_id)
            print(trip_id, passenger_id)
            if trip.passengers.filter(id=passenger_id).exists():
                trip.passengers.remove(passenger)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'Passenger not found in this trip'}, status=404)
        except Trip.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Trip not found'}, status=404)
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Passenger not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


def city_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []
    if query:
        suggestions = list(City.objects.filter(name__icontains=query)[:5].values('name'))
    return JsonResponse(suggestions, safe=False)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']

            # Разделяем имя на имя и фамилию
            name_parts = name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            # Создаем пользователя
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Создаем профиль пользователя с теми же данными
            profile = UserProfile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                is_active=False
            )

            # Генерируем токен для верификации
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Формируем URL для верификации
            verification_url = request.build_absolute_uri(
                reverse('main:activate_account', kwargs={'uidb64': uid, 'token': token})
            )

            # Формируем сообщение для email
            email_message = f"""
            Здравствуйте, {first_name}!

            Спасибо за регистрацию на нашем сайте. Для активации вашего аккаунта, пожалуйста, перейдите по следующей ссылке:

            {verification_url}

            Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

            С уважением,
            Команда Название
            """

            # Отправляем email (в консоль для тестирования)
            print("\n=== Email Message ===")
            print(f"To: {email}")
            print(f"Subject: Подтверждение регистрации")
            print(f"Message:\n{email_message}")
            print("===================\n")

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = UserRegistrationForm()
    return render(request, 'main/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        # Декодируем uid
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        profile = UserProfile.objects.get(user=user)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist, UserProfile.DoesNotExist):
        user = None
        profile = None

    if user is not None and default_token_generator.check_token(user, token):
        # Активируем и пользователя, и профиль
        user.is_active = True
        user.save()
        
        if profile:
            profile.is_active = True
            profile.save()
            
        messages.success(request, 'Ваш аккаунт успешно активирован! Теперь вы можете войти в систему.')
    else:
        messages.error(request, 'Недействительная ссылка для активации аккаунта.')
    
    return redirect('main:login')

def is_passenger_profile_complete(profile):
    """
    Проверяет, заполнены ли все обязательные поля профиля пассажира
    (кроме автомобиля, так как пассажиру он не нужен)
    """
    required_fields = [
        profile.first_name,
        profile.last_name,
        profile.phone_number,
        profile.email
    ]
    
    # Проверяем, что все поля заполнены
    return all(required_fields)

@csrf_exempt
def add_passenger(request, trip_id):
    if request.method == 'POST':
        try:
            trip = get_object_or_404(Trip, id=trip_id)
            user_profile = get_object_or_404(UserProfile, user=request.user)
            
            # Проверяем заполненность профиля пассажира
            if not is_passenger_profile_complete(user_profile):
                return JsonResponse({
                    'success': False, 
                    'error': 'Для присоединения к поездке необходимо заполнить профиль. Пожалуйста, перейдите в раздел "Профиль" и заполните все обязательные поля.'
                })
            
            if user_profile not in trip.passengers.all() and user_profile not in trip.pending_passengers.all() and trip.user != request.user:
                if not trip.is_full:
                    trip.pending_passengers.add(user_profile)
                    Notification.objects.create(
                        recipient=trip.user,
                        sender=user_profile,
                        trip=trip,
                        message=f"{user_profile.user.username} хочет присоединиться к вашей поездке."
                    )
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Trip is full'})
            return JsonResponse({'success': False, 'error': 'Cannot add passenger'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def remove_passenger(request, trip_id):
    if request.method == 'POST':
        try:
            trip = get_object_or_404(Trip, id=trip_id)
            user_profile = get_object_or_404(UserProfile, user=request.user)
            if user_profile in trip.passengers.all():
                trip.passengers.remove(user_profile)
                Notification.objects.create(
                    recipient=trip.user,
                    sender=user_profile,
                    trip=trip,
                    message=f"{user_profile.user.username} покинул вашу поездку."
                )
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'error': 'Cannot remove passenger'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
def logout_view(request):
    logout(request)
    return redirect('main:login')

@csrf_exempt
def handle_passenger_request(request, notification_id, action):
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id)
            trip = notification.trip
            user_profile = notification.sender

            if action == 'accept':
                if user_profile not in trip.passengers.all():
                    trip.passengers.add(user_profile)
                    trip.pending_passengers.remove(user_profile)
                    Notification.objects.create(
                        recipient=user_profile,
                        sender=notification.recipient,
                        trip=trip,
                        message=f"Ваш запрос на присоединение к поездке был одобрен."
                    )
                notification.read = True
                notification.save()
            elif action == 'decline':
                trip.pending_passengers.remove(user_profile)
                Notification.objects.create(
                    recipient=user_profile,
                    sender=notification.recipient,
                    trip=trip,
                    message=f"Ваш запрос на присоединение к поездке был отклонен."
                )
                notification.read = True
                notification.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# YANDEX_API_KEY = '67353677-78f4-4a38-b735-85c35af03f47'

# def get_coordinates(city_name):
#     geocode_url = 'https://geocode-maps.yandex.ru/1.x/'
#     params = {
#         'apikey': YANDEX_API_KEY,
#         'geocode': city_name,
#         'format': 'json'
#     }
#     response = requests.get(geocode_url, params=params)
#     data = response.json()
#
#     if response.status_code == 200 and 'response' in data:
#         point = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
#         longitude, latitude = point.split()
#         return latitude, longitude
#     else:
#         raise Exception(f'Не удалось получить координаты для города: {city_name}')
#
# def get_travel_time(start_city, end_city):
#     start_lat, start_lon = get_coordinates(start_city)
#     end_lat, end_lon = get_coordinates(end_city)
#
#     url = 'https://api.routing.yandex.net/v2/route'
#     params = {
#         'apikey': YANDEX_API_KEY,
#         'lang': 'ru_RU',
#         'mode': 'driving',
#         'waypoints': f'{start_lat},{start_lon}|{end_lat},{end_lon}'
#     }
#     response = requests.get(url, params=params)
#     data = response.json()
#
#     print(f'Request URL: {response.url}')  # Отладочная информация: URL запроса
#     print(f'Status Code: {response.status_code}')  # Отладочная информация: статус код
#     print(f'Response Data: {data}')  # Отладочная информация: данные ответа
#
#     if response.status_code == 200 and 'routes' in data:
#         duration = data['routes'][0]['legs'][0]['duration']['value']  # Время в пути в секундах
#         return duration
#     else:
#         raise Exception('Не удалось получить данные о маршруте')




def add_trip(request):
    errors = []
    user_profile = UserProfile.objects.get(user=request.user)
    user_trips = Trip.objects.filter(user=user_profile)
    
    # Проверяем заполненность профиля
    profile_complete = True
    missing_fields = []
    
    # Проверяем основные поля
    if not user_profile.first_name:
        missing_fields.append('имя')
    if not user_profile.last_name:
        missing_fields.append('фамилия')
    if not user_profile.phone_number:
        missing_fields.append('номер телефона')
    if not user_profile.email:
        missing_fields.append('email')
        
    # Проверяем наличие автомобиля
    try:
        car = Car.objects.get(owner=user_profile)
        if not car.brand:
            missing_fields.append('марка автомобиля')
    except Car.DoesNotExist:
        missing_fields.append('автомобиль')
        
    if missing_fields:
        profile_complete = False
        # Формируем сообщение с перечислением отсутствующих полей
        fields_text = ', '.join(missing_fields)
        messages.warning(request, f'Для создания поездки необходимо заполнить следующие поля в профиле: {fields_text}. Пожалуйста, перейдите в раздел "Профиль" и заполните все обязательные поля.')

    if request.method == 'POST':
        if not profile_complete:
            return redirect('main:profile')
            
        form = TripForm(request.POST, request.FILES)
        if form.is_valid():
            car_image = form.cleaned_data['car_image']
            car_brand = form.cleaned_data['car_name']
            departure_city_name = form.cleaned_data['departure_city']
            arrival_datetime = form.cleaned_data['arrival_time']
            destination_city_name = form.cleaned_data['destination_city']
            departure_datetime = form.cleaned_data['departure_time']
            max_passengers = form.cleaned_data['max_passengers']
            price = form.cleaned_data['price']
            comment = form.cleaned_data['comment']

            departure_date = departure_datetime.date()
            departure_time = departure_datetime.time()
            arrival_date = arrival_datetime.date()
            arrival_time = arrival_datetime.time()

            try:
                car = Car.objects.get(brand=car_brand, owner=user_profile)
                if car_image:
                    car.image = car_image
                    car.save()
            except Car.DoesNotExist:
                car = Car.objects.create(
                    image=car_image,
                    brand=car_brand,
                    owner=user_profile
                )

            user_profile.car = car
            user_profile.save()

            try:
                departure_city = City.objects.get(name=departure_city_name)
            except City.DoesNotExist:
                form.add_error('departure_city', 'Такого города в списке нет.')
                errors.append('Такого города в списке нет.')

            try:
                destination_city = City.objects.get(name=destination_city_name)
            except City.DoesNotExist:
                form.add_error('destination_city', 'Такого города в списке нет.')
                errors.append('Такого города в списке нет.')

            if not errors:
                try:
                    Trip.objects.create(
                        user=user_profile,
                        departure_city=departure_city,
                        destination_city=destination_city,
                        departure_date=departure_date,
                        departure_time=departure_time,
                        arrival_date=arrival_date,
                        arrival_time=arrival_time,
                        max_passengers=max_passengers,
                        price=price,
                        comment=comment,
                        car=car
                    )
                    return redirect('main:profile')
                except Exception as e:
                    form.add_error(None, str(e))
                    errors.append(str(e))
    else:
        form = TripForm()

    current_datetime = timezone.now().isoformat()
    return render(request, 'main/add_travel.html', {
        'form': form, 
        'errors': errors, 
        'trips': user_trips, 
        'current_datetime': current_datetime,
        'profile_complete': profile_complete
    })

def is_profile_complete(profile):
    """
    Проверяет, заполнены ли все обязательные поля профиля
    """
    required_fields = [
        profile.first_name,
        profile.last_name,
        profile.phone_number,
        profile.email
    ]
    
    # Проверяем, что все поля заполнены
    if not all(required_fields):
        return False
        
    # Проверяем наличие автомобиля
    try:
        car = Car.objects.get(owner=profile)
        if not car.brand:
            return False
    except Car.DoesNotExist:
        return False
        
    return True

def calculate_route(request):
    if request.method == 'GET':
        start = request.GET.get('start')
        end = request.GET.get('end')
        
        if not start or not end:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)
            
        # Словарь с расстояниями между основными городами (в километрах)
        DISTANCES = {
            # Центральный федеральный округ
            ('Москва', 'Тверь'): 167,
            ('Москва', 'Ярославль'): 265,
            ('Москва', 'Воронеж'): 515,
            ('Москва', 'Тула'): 183,
            ('Москва', 'Рязань'): 196,
            ('Москва', 'Калуга'): 188,
            ('Москва', 'Смоленск'): 419,
            ('Москва', 'Брянск'): 379,
            ('Москва', 'Владимир'): 190,
            ('Москва', 'Иваново'): 275,
            ('Москва', 'Кострома'): 340,
            ('Москва', 'Липецк'): 450,
            ('Москва', 'Орел'): 368,
            ('Москва', 'Курск'): 530,
            ('Москва', 'Белгород'): 680,
            
            # Северо-Западный федеральный округ
            ('Москва', 'Санкт-Петербург'): 705,
            ('Санкт-Петербург', 'Тверь'): 480,
            ('Санкт-Петербург', 'Ярославль'): 440,
            ('Санкт-Петербург', 'Великий Новгород'): 180,
            ('Санкт-Петербург', 'Псков'): 290,
            ('Санкт-Петербург', 'Петрозаводск'): 430,
            ('Санкт-Петербург', 'Мурманск'): 1350,
            ('Санкт-Петербург', 'Архангельск'): 1140,
            ('Санкт-Петербург', 'Вологда'): 700,
            
            # Приволжский федеральный округ
            ('Москва', 'Нижний Новгород'): 400,
            ('Москва', 'Казань'): 815,
            ('Москва', 'Самара'): 1050,
            ('Москва', 'Саратов'): 850,
            ('Москва', 'Ульяновск'): 890,
            ('Москва', 'Пенза'): 625,
            ('Москва', 'Ижевск'): 1120,
            ('Москва', 'Пермь'): 1380,
            ('Москва', 'Уфа'): 1350,
            ('Москва', 'Оренбург'): 1450,
            ('Москва', 'Йошкар-Ола'): 860,
            ('Москва', 'Чебоксары'): 650,
            
            # Южный федеральный округ
            ('Москва', 'Ростов-на-Дону'): 1070,
            ('Москва', 'Краснодар'): 1350,
            ('Москва', 'Сочи'): 1620,
            ('Москва', 'Волгоград'): 970,
            ('Москва', 'Астрахань'): 1410,
            ('Москва', 'Ставрополь'): 1450,
            ('Москва', 'Махачкала'): 1850,
            ('Москва', 'Грозный'): 2000,
            ('Москва', 'Владикавказ'): 1950,
            
            # Уральский федеральный округ
            ('Москва', 'Екатеринбург'): 1420,
            ('Москва', 'Челябинск'): 1820,
            ('Москва', 'Тюмень'): 2140,
            ('Москва', 'Курган'): 2000,
            ('Москва', 'Ханты-Мансийск'): 2800,
            
            # Сибирский федеральный округ
            ('Москва', 'Новосибирск'): 3350,
            ('Москва', 'Омск'): 2700,
            ('Москва', 'Томск'): 3600,
            ('Москва', 'Красноярск'): 4200,
            ('Москва', 'Иркутск'): 5200,
            ('Москва', 'Кемерово'): 3600,
            ('Москва', 'Барнаул'): 3400,
            
            # Дальневосточный федеральный округ
            ('Москва', 'Владивосток'): 9100,
            ('Москва', 'Хабаровск'): 8500,
            ('Москва', 'Благовещенск'): 8000,
            ('Москва', 'Петропавловск-Камчатский'): 12000,
            ('Москва', 'Магадан'): 11000,
            ('Москва', 'Южно-Сахалинск'): 10500,
            
            # Дополнительные маршруты между крупными городами
            ('Санкт-Петербург', 'Нижний Новгород'): 1100,
            ('Санкт-Петербург', 'Казань'): 1500,
            ('Санкт-Петербург', 'Воронеж'): 1200,
            ('Санкт-Петербург', 'Ростов-на-Дону'): 1750,
            ('Санкт-Петербург', 'Краснодар'): 2000,
            ('Санкт-Петербург', 'Сочи'): 2300,
            ('Санкт-Петербург', 'Волгоград'): 1650,
            ('Санкт-Петербург', 'Самара'): 1700,
            ('Санкт-Петербург', 'Екатеринбург'): 2100,
            ('Санкт-Петербург', 'Новосибирск'): 3800,
            ('Санкт-Петербург', 'Калининград'): 1200,
            
            # Популярные маршруты между соседними городами
            ('Тверь', 'Ярославль'): 260,
            ('Тверь', 'Великий Новгород'): 320,
            ('Тверь', 'Ржев'): 120,
            ('Тверь', 'Вышний Волочек'): 120,
            ('Ярославль', 'Кострома'): 85,
            ('Ярославль', 'Рыбинск'): 80,
            ('Воронеж', 'Липецк'): 120,
            ('Воронеж', 'Курск'): 220,
            ('Тула', 'Калуга'): 120,
            ('Тула', 'Орел'): 180,
            ('Рязань', 'Тамбов'): 300,
            ('Рязань', 'Пенза'): 450,
            ('Калуга', 'Брянск'): 200,
            ('Смоленск', 'Брянск'): 250,
            ('Владимир', 'Иваново'): 120,
            ('Владимир', 'Муром'): 130,
            ('Иваново', 'Кострома'): 100,
            ('Иваново', 'Шуя'): 30,
            ('Кострома', 'Галич'): 120,
            ('Кострома', 'Буй'): 100,
        }
        
        # Проверяем оба варианта порядка городов
        distance = None
        if (start, end) in DISTANCES:
            distance = DISTANCES[(start, end)]
        elif (end, start) in DISTANCES:
            distance = DISTANCES[(end, start)]
            
        if distance is not None:
            # Предполагаем среднюю скорость 60 км/ч
            duration = distance * 60  # время в минутах
            return JsonResponse({
                'distance': distance * 1000,  # переводим в метры
                'duration': duration * 60     # переводим в секунды
            })
        else:
            return JsonResponse({'error': 'Route not found'}, status=404)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)