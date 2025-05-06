import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traveling.settings')
django.setup()

from main.models import CarBrand, CarModel

def add_car_data():
    # Словарь с марками и моделями автомобилей
    car_data = {
        'Audi': ['A1', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'Q3', 'Q5', 'Q7', 'Q8', 'e-tron'],
        'BMW': ['1 Series', '2 Series', '3 Series', '4 Series', '5 Series', '6 Series', '7 Series', 'X1', 'X3', 'X5', 'X6', 'X7'],
        'Mercedes-Benz': ['A-Class', 'B-Class', 'C-Class', 'E-Class', 'S-Class', 'GLA', 'GLC', 'GLE', 'GLS'],
        'Volkswagen': ['Polo', 'Golf', 'Passat', 'Tiguan', 'Touareg', 'T-Roc', 'ID.3', 'ID.4'],
        'Toyota': ['Yaris', 'Corolla', 'Camry', 'RAV4', 'Highlander', 'Land Cruiser', 'Prius', 'C-HR'],
        'Honda': ['Civic', 'Accord', 'CR-V', 'HR-V', 'Jazz', 'Pilot'],
        'Ford': ['Fiesta', 'Focus', 'Mondeo', 'Kuga', 'Edge', 'Explorer', 'Mustang'],
        'Hyundai': ['i20', 'i30', 'Elantra', 'Tucson', 'Santa Fe', 'Kona', 'IONIQ'],
        'Kia': ['Rio', 'Ceed', 'Sportage', 'Sorento', 'Stinger', 'Picanto', 'Niro'],
        'Lada': ['Vesta', 'Granta', 'XRAY', 'Niva', 'Largus'],
    }
    
    total_brands = 0
    total_models = 0
    
    for brand_name, models in car_data.items():
        brand, created = CarBrand.objects.get_or_create(name=brand_name)
        if created:
            total_brands += 1
            print(f'Created brand: {brand_name}')
        
        for model_name in models:
            model, created = CarModel.objects.get_or_create(brand=brand, name=model_name)
            if created:
                total_models += 1
    
    print(f'Successfully added {total_brands} brands and {total_models} models to the database')

if __name__ == '__main__':
    add_car_data() 