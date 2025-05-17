// кнопка навбара
document.querySelector('.navbar-toggle').addEventListener('click', function() {
    document.querySelector('.header-buttons').classList.toggle('active');
});

// свгшка
window.addEventListener('resize', function() {
    const largeSVG = document.querySelector('.svg-large');
    const smallSVG = document.querySelector('.svg-small');

    if (largeSVG && smallSVG) {
        if (window.innerWidth <= 420) {
            largeSVG.style.display = 'none';
            smallSVG.style.display = 'block';
        } else {
            largeSVG.style.display = 'block';
            smallSVG.style.display = 'none';
        }
    }
});

// Инициализация при загрузке страницы
window.dispatchEvent(new Event('resize'));

// Функция для открытия модального окна с данными
function openModalWithData(tripData) {
    console.log('Received trip data:', tripData); // Отладочный вывод
    
    const modal = document.getElementById('customModal');
    const modalContent = modal.querySelector('.custom-trip-modal-content');
    
    // Устанавливаем tripId для модального окна
    const tripId = tripData.id || tripData.trip_id;
    console.log('Setting trip ID:', tripId);
    
    if (!tripId) {
        console.error('No trip ID in data');
        return;
    }
    
    modalContent.setAttribute('data-trip-id', tripId);
    
    // Заполняем информацию о водителе
    const driverPhoto = document.getElementById('driver-photo');
    const driverName = document.getElementById('driver-name');
    const driverDescription = document.getElementById('driver-description');
    
    if (driverPhoto) {
        driverPhoto.src = tripData.driver_photo || '/static/img/default-avatar.png';
        driverPhoto.alt = `${tripData.driver_name} ${tripData.driver_surname}`;
    }
    
    if (driverName) {
        driverName.textContent = `${tripData.driver_name} ${tripData.driver_surname}`;
        driverName.href = `/profile_user/?user_id=${tripData.driver_id}`;
    }
    
    if (driverDescription) {
        driverDescription.textContent = tripData.driver_description || 'Нет описания';
    }
    
    // Заполняем информацию о маршруте
    document.getElementById('modal-departure-city').textContent = tripData.departure_address;
    document.getElementById('modal-departure-time').textContent = `${tripData.departure_date}, ${tripData.departure_time}`;
    document.getElementById('modal-destination-city').textContent = tripData.destination_address;
    document.getElementById('modal-arrival-time').textContent = `${tripData.arrival_date}, ${tripData.arrival_time}`;
    
    // Заполняем информацию о пассажирах
    document.getElementById('modal-passengers-count').textContent = tripData.passengers_count || 0;
    document.getElementById('modal-max-passengers').textContent = tripData.max_passengers || 0;
    
    // Заполняем список пассажиров
    const passengersList = document.getElementById('modal-passengers-list');
    if (passengersList) {
        passengersList.innerHTML = '';
        
        if (tripData.passengers && tripData.passengers.length > 0) {
            tripData.passengers.forEach(passenger => {
                const passengerItem = document.createElement('div');
                passengerItem.className = 'modal-passenger-item';
                passengerItem.innerHTML = `
                    <div class="passenger-info">
                        <div class="passenger-photo">
                            <img src="${passenger.photo_url || '/static/img/default-avatar.png'}" alt="Фото пассажира">
                        </div>
                        <div class="passenger-details">
                            <a href="/profile/?user_id=${passenger.id}" class="passenger-name">${passenger.first_name} ${passenger.last_name}</a>
                            <a href="/profile/?user_id=${passenger.id}" class="passenger-profile-link">Профиль</a>
                        </div>
                    </div>
                    ${tripData.is_driver ? `<button class="remove-passenger-btn" onclick="removePassenger(${tripId}, ${passenger.id})">Удалить</button>` : ''}
                `;
                passengersList.appendChild(passengerItem);
            });
        } else {
            passengersList.innerHTML = '<div class="modal-passenger-item">Нет пассажиров</div>';
        }
    }
    
    // Заполняем статус и цену
    const timeUntilElement = document.getElementById('modal-time-until');
    const priceElement = document.getElementById('modal-price');
    
    if (timeUntilElement) {
        timeUntilElement.textContent = tripData.time_until ? `До отправления: ${tripData.time_until}` : 'До отправления: не указано';
    }
    
    if (priceElement) {
        priceElement.textContent = `${tripData.price} ₽`;
    }
    
    // Показываем модальное окно
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
    
    // Добавляем обработчики для закрытия модального окна
    const closeBtn = modal.querySelector('.custom-trip-close-btn');
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        };
    }
    
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    };
}

// Функция для отображения точки на карте
function showMapPoint(type) {
    const mapModal = document.getElementById('mapModal');
    const customModal = document.getElementById('customModal');
    const title = document.getElementById('mapModalTitle');
    const modalContent = document.querySelector('.custom-trip-modal-content');
    
    if (!modalContent) {
        return;
    }
    
    const tripId = modalContent.getAttribute('data-trip-id');
    
    if (!tripId) {
        return;
    }
    
    // Закрываем модальное окно с деталями поездки
    customModal.style.display = 'none';
    
    title.textContent = type === 'departure' ? 'Точка отправления' : 'Точка прибытия';
    mapModal.style.display = 'block';
    
    // Добавляем класс show с небольшой задержкой для анимации
    setTimeout(() => {
        mapModal.classList.add('show');
    }, 10);

    // Получаем данные о точке маршрута через AJAX
    fetch(`/get_route_point/${tripId}/${type}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const address = data.address;
                document.getElementById('fullAddress').textContent = address;

                // Инициализируем карту
                ymaps.ready(function() {
                    // Создаем карту только если она еще не существует или не является валидным объектом карты
                    if (!window.map || !window.map.geoObjects) {
                        window.map = new ymaps.Map('map', {
                            center: [55.76, 37.64],
                            zoom: 10,
                            controls: ['zoomControl', 'fullscreenControl']
                        });
                    }

                    // Геокодируем адрес
                    ymaps.geocode(address, {
                        results: 1
                    }).then(function(res) {
                        const firstGeoObject = res.geoObjects.get(0);
                        const coords = firstGeoObject.geometry.getCoordinates();
                        
                        // Устанавливаем центр карты на найденные координаты
                        window.map.setCenter(coords, 15);
                        
                        // Удаляем предыдущую метку, если она есть
                        if (window.placemark) {
                            window.map.geoObjects.remove(window.placemark);
                        }
                        
                        // Создаем новую метку
                        window.placemark = new ymaps.Placemark(coords, {
                            balloonContent: address
                        }, {
                            preset: type === 'departure' ? 'islands#greenDotIcon' : 'islands#redDotIcon'
                        });
                        
                        // Добавляем метку на карту
                        window.map.geoObjects.add(window.placemark);
                        
                        // Открываем балун с адресом
                        window.placemark.balloon.open();
                    });
                });
            } else {
                alert('Не удалось получить данные о точке маршрута');
            }
        })
        .catch(error => {
            alert('Произошла ошибка при получении данных о точке маршрута');
        });
}

// Функция для закрытия модального окна карты
function closeMapModal() {
    const mapModal = document.getElementById('mapModal');
    const customModal = document.getElementById('customModal');
    
    // Убираем класс show для анимации исчезновения
    mapModal.classList.remove('show');
    
    // Ждем окончания анимации перед скрытием
    setTimeout(() => {
        mapModal.style.display = 'none';
        // Открываем обратно модальное окно с деталями поездки
        customModal.style.display = 'flex';
        document.body.classList.add('modal-open');
    }, 300);
}

// Добавляем обработчик для закрытия модального окна при клике вне его области
document.addEventListener('DOMContentLoaded', function() {
    const mapModal = document.getElementById('mapModal');
    if (mapModal) {
        mapModal.addEventListener('click', function(event) {
            if (event.target === mapModal) {
                closeMapModal();
            }
        });
    }
});

// Функция для удаления пассажира
function removePassenger(tripId, passengerId) {
    if (!confirm('Вы уверены, что хотите удалить этого пассажира?')) return;

    fetch(`/remove_passenger/${tripId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: passengerId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            console.error(data.error);
            alert('Произошла ошибка при удалении пассажира');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при удалении пассажира');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Модальное окно
    const modal = document.getElementById("customModal");
    const closeBtn = modal.querySelector(".custom-trip-close-btn");

    // Close the modal
    closeBtn.onclick = function() {
        modal.style.display = "none";
        document.body.classList.remove('modal-open');
    }

    // Close the modal when clicking outside of it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
            document.body.classList.remove('modal-open');
        }
    }

    // Фильтрация по цене
    const minCostSlider = document.getElementById('min-cost');
    const maxCostSlider = document.getElementById('max-cost');
    const minCostValue = document.getElementById('min-cost-value');
    const maxCostValue = document.getElementById('max-cost-value');
    const sliderTrack = document.querySelector('.slider-track');
    const maxGap = 50; // Minimum gap between sliders

    function updateSliderValues(event) {
        let minValue = parseInt(minCostSlider.value);
        let maxValue = parseInt(maxCostSlider.value);

        if (maxValue - minValue <= maxGap) {
            if (event.target === minCostSlider) {
                minCostSlider.value = maxValue - maxGap;
            } else {
                maxCostSlider.value = minValue + maxGap;
            }
        }

        minValue = parseInt(minCostSlider.value);
        maxValue = parseInt(maxCostSlider.value);

        minCostValue.value = minValue;
        maxCostValue.value = maxValue;
        fillSlider();
        filterTrips();
    }

    function updateInputValues(event) {
        let minValue = parseInt(minCostValue.value);
        let maxValue = parseInt(maxCostValue.value);

        if (maxValue - minValue <= maxGap) {
            if (event.target === minCostValue) {
                minCostValue.value = maxValue - maxGap;
            } else {
                maxCostValue.value = minValue + maxGap;
            }
        }

        minValue = parseInt(minCostValue.value);
        maxValue = parseInt(maxCostValue.value);

        minCostSlider.value = minValue;
        maxCostSlider.value = maxValue;
        fillSlider();
        filterTrips();
    }

    function fillSlider() {
        const minValue = minCostSlider.value;
        const maxValue = maxCostSlider.value;
        const percentage1 = (minValue / minCostSlider.max) * 100;
        const percentage2 = (maxValue / maxCostSlider.max) * 100;
        sliderTrack.style.background = `linear-gradient(to right, var(--color-lightblue2) ${percentage1}%, var(--color-lightblue) ${percentage1}%, var(--color-lightblue) ${percentage2}%, var(--color-lightblue2) ${percentage2}%)`;
    }

    function filterTrips() {
        const minValue = parseInt(minCostSlider.value);
        const maxValue = parseInt(maxCostSlider.value);

        document.querySelectorAll('.trip').forEach(trip => {
            const price = parseInt(trip.getAttribute('data-price'));
            if (price >= minValue && price <= maxValue) {
                trip.style.display = '';
            } else {
                trip.style.display = 'none';
            }
        });
    }

    minCostSlider.addEventListener('input', updateSliderValues);
    maxCostSlider.addEventListener('input', updateSliderValues);
    minCostValue.addEventListener('input', updateInputValues);
    maxCostValue.addEventListener('input', updateInputValues);

    // Инициализация слайдера
    fillSlider();
    filterTrips();

    // Обработка кнопок
    document.querySelectorAll('.details-button').forEach(button => {
        button.addEventListener('click', function() {
            const tripId = this.getAttribute('data-trip-id');
            console.log('Details button clicked, tripId:', tripId);
            
            if (!tripId) {
                console.error('Trip ID not found on button');
                return;
            }
            
            fetch(`/get_trip_details/${tripId}/`)
                .then(response => {
                    console.log('Trip details response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Received trip details:', data);
                    if (!data.id && !data.trip_id) {
                        console.error('No trip ID in response data');
                        return;
                    }
                    openModalWithData(data);
                })
                .catch(error => {
                    console.error('Error fetching trip details:', error);
                    alert('Произошла ошибка при получении данных о поездке');
                });
        });
    });

    document.querySelectorAll('.add-button').forEach(button => {
        button.addEventListener('click', function() {
            const tripId = this.dataset.tripId;
            fetch(`/add_passenger/${tripId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: '{{ request.user.id }}' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error(data.error);
                }
            })
            .catch(error => console.error('There was a problem with the fetch operation:', error));
        });
    });

    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', function() {
            const tripId = this.dataset.tripId;
            fetch(`/remove_passenger/${tripId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: '{{ request.user.id }}' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error(data.error);
                }
            })
            .catch(error => console.error('There was a problem with the fetch operation:', error));
        });
    });
});

// Кнопка прокрутки наверх
var scrollToTopBtn = document.getElementById("scrollToTopBtn");

function toggleScrollToTopButton() {
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        scrollToTopBtn.style.display = "block";
    } else {
        scrollToTopBtn.style.display = "none";
    }
}

function scrollToTop() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

window.onscroll = function() {
    toggleScrollToTopButton();
};

scrollToTopBtn.onclick = function() {
    scrollToTop();
};