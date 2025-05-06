import os
import django
import sys

# Настраиваем Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/traveling')
os.environ['DJANGO_SETTINGS_MODULE'] = 'traveling.settings'
django.setup()

# Импортируем модели
from main.models import CarBrand, CarModel

# Создаем несколько марок и моделей
brands_and_models = {
    'BMW': ['X5', '3 Series', '5 Series', 'X1'],
    'Audi': ['A4', 'Q5', 'A6', 'Q7'],
    'Toyota': ['Camry', 'RAV4', 'Corolla', 'Land Cruiser'],
    'Mercedes-Benz': ['C-Class', 'E-Class', 'S-Class', 'GLC'],
    'Volkswagen': ['Golf', 'Passat', 'Tiguan', 'Polo'],
    'Lada': ['Vesta', 'Granta', 'XRAY', 'Niva']
}

for brand_name, models in brands_and_models.items():
    # Создаем или получаем бренд
    brand, created = CarBrand.objects.get_or_create(name=brand_name)
    if created:
        print(f"Создан бренд: {brand_name}")
    else:
        print(f"Найден существующий бренд: {brand_name}")
    
    # Создаем модели для этого бренда
    for model_name in models:
        model, created = CarModel.objects.get_or_create(brand=brand, name=model_name)
        if created:
            print(f"  Создана модель: {model_name}")
        else:
            print(f"  Найдена существующая модель: {model_name}")

print("Готово! Добавлены марки и модели автомобилей.") 