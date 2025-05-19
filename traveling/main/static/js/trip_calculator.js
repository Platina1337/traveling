document.addEventListener('DOMContentLoaded', function() {
    // Удаляем поле route_duration, если оно существует
    const routeDurationField = document.querySelector('input[name="route_duration"]');
    if (routeDurationField) {
        routeDurationField.remove();
    }

    const departureCity = document.getElementById('departure');
    const destinationCity = document.getElementById('arrival');
    const durationText = document.getElementById('duration-text');
    const tripDuration = document.getElementById('trip-duration');
    const fillTimeBtn = document.getElementById('fill-time-btn');
    const departureTimeInput = document.getElementById('id_departure_time');
    const arrivalTimeInput = document.getElementById('id_arrival_time');
    const form = document.querySelector('form');
    
    let currentDuration = null;

    async function checkCityExists(city) {
        try {
            const response = await fetch(`/city_suggestions?q=${encodeURIComponent(city)}`);
            const data = await response.json();
            return data.length > 0;
        } catch (error) {
            console.error('Error checking city:', error);
            return false;
        }
    }

    async function calculateDuration() {
        
        const destinationAddress = document.getElementById('destinationAddressDisplay');
        const departureAddress = document.getElementById('departureAddressDisplay');
        const from = departureCity.value.trim();
        const to = destinationCity.value.trim();
        const departureTime = departureTimeInput.value;
        
        if (!from || !to) {
            durationText.textContent = 'Выберите города отправления и прибытия';
            fillTimeBtn.disabled = true;
            currentDuration = null;
            return;
        }

        if (from === to) {
            durationText.textContent = 'Города отправления и прибытия не могут совпадать';
            fillTimeBtn.disabled = true;
            currentDuration = null;
            return;
        }

        if (!departureTime) {
            durationText.textContent = 'Выберите время отправления';
            fillTimeBtn.disabled = true;
            currentDuration = null;
            return;
        }

        // Проверяем существование городов
        const [fromExists, toExists] = await Promise.all([
            checkCityExists(from),
            checkCityExists(to)
        ]);

        if (!fromExists) {
            durationText.textContent = `Город отправления "${from}" не найден`;
            fillTimeBtn.disabled = true;
            currentDuration = null;
            return;
        }

        if (!toExists) {
            durationText.textContent = `Город прибытия "${to}" не найден`;
            fillTimeBtn.disabled = true;
            currentDuration = null;
            return;
        }

        try {
            console.log('Sending request with params:', { from, to });
            const response = await fetch(`/calculate_route/?start=${encodeURIComponent(from)}&end=${encodeURIComponent(to)}`);
            const data = await response.json();

            console.log('Received response:', data);

            if (!response.ok) {
                console.error('API Error:', data);
                durationText.textContent = data.error || 'Ошибка при расчете времени в пути';
                fillTimeBtn.disabled = true;
                currentDuration = null;
                return;
            }

            if (!data.distance || !data.duration) {
                console.error('Invalid API response:', data);
                durationText.textContent = 'Получен некорректный ответ от сервера';
                fillTimeBtn.disabled = true;
                currentDuration = null;
                return;
            }

            const distance = data.distance;
            const duration = data.duration;
            currentDuration = duration;
            
            const hours = Math.floor(duration / 3600);
            const minutes = Math.floor((duration % 3600) / 60);
            
            durationText.textContent = `Расчетное время в пути: ${hours} ч ${minutes} м`;
            fillTimeBtn.disabled = false;

            // Сохраняем данные маршрута в скрытых полях формы
            const form = document.querySelector('form');
            
            // Создаем или обновляем скрытое поле для расстояния
            let routeDistanceField = form.querySelector('input[name="route_distance"]');
            
            if (!routeDistanceField) {
                routeDistanceField = document.createElement('input');
                routeDistanceField.type = 'hidden';
                routeDistanceField.name = 'route_distance';
                form.appendChild(routeDistanceField);
            }
            
            routeDistanceField.value = distance;

            console.log('Saved route data:', { distance });

            // Сохраняем координаты точек маршрута
            const fields = {
                'departure_address': departureAddress.textContent || from,
                'departure_lat': data.start_lat,
                'departure_lon': data.start_lon,
                'destination_address': destinationAddress.textContent || to,
                'destination_lat': data.end_lat,
                'destination_lon': data.end_lon
            };

            console.log('Route point data:', fields);

            for (const [name, value] of Object.entries(fields)) {
                let field = form.querySelector(`input[name="${name}"]`);
                if (!field) {
                    field = document.createElement('input');
                    field.type = 'hidden';
                    field.name = name;
                    form.appendChild(field);
                    console.log(`Created new field: ${name}`);
                }
                field.value = value;
                console.log(`Set ${name} to:`, value);
            }

            // Проверяем, что все поля созданы и заполнены
            const allFields = ['departure_address', 'departure_lat', 'departure_lon', 
                             'destination_address', 'destination_lat', 'destination_lon',
                             'route_distance'];
            
            console.log('Checking all fields:');
            const missingFields = allFields.filter(fieldName => {
                const field = form.querySelector(`input[name="${fieldName}"]`);
                const hasValue = field && field.value;
                console.log(`Field ${fieldName}:`, field ? field.value : 'not found');
                return !hasValue;
            });

            if (missingFields.length > 0) {
                console.error('Missing fields:', missingFields);
            }

            // Автоматически заполняем время прибытия
            fillArrivalTime();

            // Добавляем логирование перед отправкой формы
            form.addEventListener('submit', function(e) {
                console.log('Form submission - checking fields:');
                allFields.forEach(fieldName => {
                    const field = form.querySelector(`input[name="${fieldName}"]`);
                    console.log(`${fieldName}:`, field ? field.value : 'not found');
                });
            });
        } catch (error) {
            console.error('Error calculating duration:', error);
            durationText.textContent = 'Ошибка при расчете времени в пути';
            fillTimeBtn.disabled = true;
            currentDuration = null;
        }
    }

    function updateFillTimeButton() {
        fillTimeBtn.disabled = !currentDuration || !departureTimeInput.value;
    }

    function fillArrivalTime() {
        if (!currentDuration || !departureTimeInput.value) return;
        
        const departureDate = new Date(departureTimeInput.value);
        const arrivalDate = new Date(departureDate.getTime() + currentDuration * 1000);
        
        arrivalTimeInput.value = arrivalDate.toISOString().slice(0, 16);
    }

    // Добавляем обработчики событий
    departureCity.addEventListener('change', function() {
        if (destinationCity.value && departureTimeInput.value) {
            calculateDuration();
        } else {
            durationText.textContent = 'Выберите город прибытия и время отправления';
            fillTimeBtn.disabled = true;
        }
    });

    destinationCity.addEventListener('change', function() {
        if (departureCity.value && departureTimeInput.value) {
            calculateDuration();
        } else {
            durationText.textContent = 'Выберите город отправления и время отправления';
            fillTimeBtn.disabled = true;
        }
    });

    departureTimeInput.addEventListener('change', function() {
        if (departureCity.value && destinationCity.value) {
            calculateDuration();
        } else {
            durationText.textContent = 'Выберите города отправления и прибытия';
            fillTimeBtn.disabled = true;
        }
    });

    fillTimeBtn.addEventListener('click', fillArrivalTime);

    // Добавляем обработчик отправки формы
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Предотвращаем стандартную отправку формы
        
        // Собираем все данные формы
        const formData = new FormData(form);
        
        // Отправляем данные для логирования
        try {
            const logResponse = await fetch('/log_form_data/', {
                method: 'POST',
                body: formData
            });
            
            if (!logResponse.ok) {
                console.error('Error logging form data');
            }
        } catch (error) {
            console.error('Error sending form data for logging:', error);
        }
        
        // Продолжаем отправку формы
        form.submit();
    });

    // Проверяем начальное состояние
    if (departureCity.value && destinationCity.value && departureTimeInput.value) {
        calculateDuration();
    } else {
        durationText.textContent = 'Выберите города отправления и прибытия, а также время отправления';
        fillTimeBtn.disabled = true;
    }
}); 