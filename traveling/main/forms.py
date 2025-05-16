import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import UserProfile, Comment, Car, CarModel, CarBrand
from django.forms.widgets import DateInput, RadioSelect

class UserProfileForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    phone_number = forms.CharField(max_length=20, required=False)
    email = forms.EmailField()
    about_me = forms.CharField(widget=forms.Textarea, required=False)
    avatar = forms.ImageField(required=False)


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Старый пароль'
        })
        self.fields['new_password1'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        })
        self.fields['new_password2'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль'
        })

        self.fields['old_password'].label = ''
        self.fields['new_password1'].label = ''
        self.fields['new_password2'].label = ''
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())


class UserRegistrationForm(forms.Form):
    name = forms.CharField(max_length=100, label='Имя и фамилия')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(max_length=15, label='Номер телефона')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.split()) != 2:
            raise forms.ValidationError('Введите имя и фамилию.')
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже зарегистрирован.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Проверка формата номера телефона
        phone_regex = re.compile(r'^\+?\d{9,15}$')
        if not phone_regex.match(phone):
            raise forms.ValidationError('Введите корректный номер телефона.')
        # Проверка уникальности номера телефона
        if UserProfile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('Этот номер телефона уже зарегистрирован.')
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('Пароль должен содержать как минимум 8 символов.')
        return password

class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


from django import forms

class TripForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Получаем список автомобилей пользователя
            user_cars = Car.objects.filter(owner=user.userprofile)
            
            # Создаем список выбора для автомобилей
            car_choices = [(car.id, f"{car.brand} {car.model} - {car.license_plate}") for car in user_cars]
            
            # Если у пользователя только один автомобиль, выбираем его по умолчанию
            initial_car = car_choices[0][0] if len(car_choices) == 1 else None
            
            # Добавляем поле выбора автомобиля
            self.fields['car_name'] = forms.ChoiceField(
                label='Автомобиль',
                choices=car_choices,
                initial=initial_car,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        else:
            self.fields['car_name'] = forms.CharField(label='Название машины', max_length=100)

    departure_city = forms.CharField(
        label='Город отправления',
        max_length=100,
        widget=forms.TextInput(attrs={'id': 'departure', 'list': 'departure-list'})
    )
    destination_city = forms.CharField(
        label='Город прибытия',
        max_length=100,
        widget=forms.TextInput(attrs={'id': 'arrival', 'list': 'arrival-list'})
    )
    departure_time = forms.DateTimeField(
        label='Время отправления',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    arrival_time = forms.DateTimeField(
        label='Время прибытия',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    max_passengers = forms.IntegerField(
        label='Количество пассажиров',
        min_value=1,
        max_value=4
    )
    price = forms.DecimalField(
        label='Стоимость поездки',
        max_digits=10,
        decimal_places=0,
        min_value=50,
        max_value=15000,
    )
    comment = forms.CharField(
        label='Комментарий',
        widget=forms.Textarea(attrs={'placeholder': 'Введите комментарий', 'maxlength': 500}),
        required=False
    )

    # Скрытые поля для координат и адресов
    route_distance = forms.FloatField(required=False, widget=forms.HiddenInput())
    departure_address = forms.CharField(required=False, widget=forms.HiddenInput())
    departure_lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    departure_lon = forms.FloatField(required=False, widget=forms.HiddenInput())
    destination_address = forms.CharField(required=False, widget=forms.HiddenInput())
    destination_lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    destination_lon = forms.FloatField(required=False, widget=forms.HiddenInput())
    def clean(self):
        cleaned_data = super().clean()

        departure_time = cleaned_data.get("departure_time")
        arrival_time = cleaned_data.get("arrival_time")
        departure_city = cleaned_data.get("departure_city")
        destination_city = cleaned_data.get("destination_city")

        if departure_time is None or arrival_time is None:
            raise forms.ValidationError("Время отправления и время прибытия должны быть заполнены.")

        if departure_time < timezone.now():
            raise forms.ValidationError("Время отправления не может быть в прошлом.")

        # Проверка, что дата и время отправления раньше даты и времени прибытия
        if departure_time >= arrival_time:
            raise forms.ValidationError("Дата и время отправления должны быть раньше даты и времени прибытия.")

        # Проверка, что города отправления и прибытия не совпадают
        if departure_city == destination_city:
            raise forms.ValidationError("Город отправления и город прибытия не могут совпадать.")

        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [ 'text']
        widgets = {

            'text': forms.Textarea(attrs={'placeholder': 'Введите ваш комментарий'}),
        }

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['brand', 'model', 'color', 'license_plate', 'image']
        labels = {
            'brand': 'Марка автомобиля',
            'model': 'Модель автомобиля',
            'color': 'Цвет автомобиля',
            'license_plate': 'Государственный номер',
            'image': 'Фото автомобиля'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['model'].queryset = CarModel.objects.none()
        
        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['model'].queryset = CarModel.objects.filter(brand_id=brand_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.brand:
            self.fields['model'].queryset = CarModel.objects.filter(brand=self.instance.brand)
        
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
                
    def clean_license_plate(self):
        license_plate = self.cleaned_data.get('license_plate')
        if license_plate:
            # Регулярное выражение для проверки российских номеров
            # Формат: А000АА000 или А000АА00
            pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$'
            if not re.match(pattern, license_plate.upper()):
                raise forms.ValidationError(
                    'Неверный формат номера. Примеры: А123БВ77, О789МК750'
                )
            
            # Проверка на уникальность номера
            if Car.objects.filter(license_plate=license_plate.upper()).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError(
                    'Автомобиль с таким номером уже зарегистрирован в системе'
                )
                
        return license_plate.upper() if license_plate else license_plate
    
    def clean_brand(self):
        brand_id = self.cleaned_data.get('brand')
        if brand_id:
            try:
                # Если brand_id это число, получаем объект CarBrand
                if isinstance(brand_id, (int, str)):
                    brand = CarBrand.objects.get(id=brand_id)
                    return brand
                # Если brand_id это уже объект CarBrand, возвращаем его
                elif isinstance(brand_id, CarBrand):
                    return brand_id
            except CarBrand.DoesNotExist:
                raise forms.ValidationError('Выберите марку автомобиля из списка')
        raise forms.ValidationError('Выберите марку автомобиля из списка')
        
    def clean_model(self):
        model_id = self.cleaned_data.get('model')
        brand = self.cleaned_data.get('brand')
        
        if brand and model_id:
            try:
                # Если model_id это число или строка, получаем объект CarModel
                if isinstance(model_id, (int, str)):
                    model = CarModel.objects.get(id=model_id, brand=brand)
                    return model
                # Если model_id это уже объект CarModel, возвращаем его
                elif isinstance(model_id, CarModel):
                    return model_id
            except CarModel.DoesNotExist:
                raise forms.ValidationError('Выберите модель автомобиля из списка')
        raise forms.ValidationError('Выберите модель автомобиля из списка')