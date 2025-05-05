from django.core.management.base import BaseCommand
from main.models import CarBrand, CarModel

class Command(BaseCommand):
    help = 'Populate the database with car brands and models'

    def handle(self, *args, **options):
        # Dictionary with car brands and their models
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
            'Nissan': ['Micra', 'Juke', 'Qashqai', 'X-Trail', 'Leaf', 'Patrol', '370Z'],
            'Mazda': ['2', '3', '6', 'CX-3', 'CX-5', 'CX-9', 'MX-5'],
            'Skoda': ['Fabia', 'Octavia', 'Superb', 'Kodiaq', 'Karoq', 'Scala'],
            'Renault': ['Clio', 'Megane', 'Captur', 'Kadjar', 'Koleos', 'Talisman', 'Zoe'],
            'Peugeot': ['208', '308', '508', '2008', '3008', '5008'],
            'Citroen': ['C3', 'C4', 'C5', 'Berlingo', 'C3 Aircross', 'C5 Aircross'],
            'SEAT': ['Ibiza', 'Leon', 'Ateca', 'Tarraco', 'Arona'],
            'Volvo': ['S60', 'S90', 'V60', 'V90', 'XC40', 'XC60', 'XC90'],
            'Jeep': ['Renegade', 'Compass', 'Wrangler', 'Cherokee', 'Grand Cherokee'],
            'Land Rover': ['Range Rover', 'Range Rover Sport', 'Range Rover Evoque', 'Discovery', 'Discovery Sport'],
            'Porsche': ['911', 'Cayenne', 'Panamera', 'Macan', 'Taycan'],
            'Ferrari': ['F8 Tributo', 'Roma', 'Portofino', 'SF90 Stradale'],
            'Lamborghini': ['Huracan', 'Aventador', 'Urus'],
            'Tesla': ['Model 3', 'Model S', 'Model X', 'Model Y', 'Cybertruck'],
            'Lexus': ['IS', 'ES', 'LS', 'UX', 'NX', 'RX', 'LX'],
            'Jaguar': ['XE', 'XF', 'F-Type', 'E-Pace', 'F-Pace', 'I-Pace'],
            'Fiat': ['500', 'Panda', 'Tipo', '500X', '500L'],
            'Opel': ['Corsa', 'Astra', 'Insignia', 'Crossland X', 'Grandland X'],
            'Suzuki': ['Swift', 'Vitara', 'S-Cross', 'Jimny', 'Ignis'],
            'Mini': ['Cooper', 'Countryman', 'Clubman', 'Convertible'],
            'Alfa Romeo': ['Giulia', 'Stelvio', 'Tonale'],
            'Lada': ['Vesta', 'Granta', 'XRAY', 'Niva', 'Largus'],
            'UAZ': ['Patriot', 'Hunter', 'Pickup', 'Буханка'],
            'ГАЗ': ['Соболь', 'ГАЗель', 'Волга', 'Сайбер'],
        }

        total_brands = 0
        total_models = 0
        
        for brand_name, models in car_data.items():
            brand, created = CarBrand.objects.get_or_create(name=brand_name)
            if created:
                total_brands += 1
                self.stdout.write(f'Created brand: {brand_name}')
            
            for model_name in models:
                model, created = CarModel.objects.get_or_create(brand=brand, name=model_name)
                if created:
                    total_models += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {total_brands} brands and {total_models} models to the database')) 