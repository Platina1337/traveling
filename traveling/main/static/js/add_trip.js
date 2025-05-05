document.addEventListener('DOMContentLoaded', (event) => {
    const modal = document.getElementById("customModal");
    const btn = document.getElementById("openModalBtn");
    const span = document.getElementsByClassName("custom-close-btn")[0];

    // Проверяем существование элементов перед установкой обработчиков
    if (btn && modal) {
        // Open the modal
        btn.onclick = function() {
            modal.style.display = "flex";
            document.body.classList.add('modal-open');
        }
    }

    if (span && modal) {
        // Close the modal
        span.onclick = function() {
            modal.style.display = "none";
            document.body.classList.remove('modal-open');
        }
    }

    // Close the modal when clicking outside of it
    if (modal) {
        window.onclick = function(event) {
            if (event.target === modal) {
                modal.style.display = "none";
                document.body.classList.remove('modal-open');
            }
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const departureInput = document.getElementById('departure');
    const arrivalInput = document.getElementById('arrival');

    function setupAutocomplete(input, dataListId) {
        input.addEventListener('input', function () {
            const value = this.value;
            const dataList = document.getElementById(dataListId);
            dataList.innerHTML = '';

            console.log(`Input value: ${value}`);

            if (value) {
                const url = `/city_suggestions?q=${encodeURIComponent(value)}`;
                console.log(`Fetching URL: ${url}`);

                fetch(url)
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        } else {
                            console.error(`Error: ${response.status} ${response.statusText}`);
                            throw new Error(`Network response was not ok: ${response.statusText}`);
                        }
                    })
                    .then(cities => {
                        console.log(cities);
                        cities.forEach(city => {
                            const option = document.createElement('option');
                            option.value = city.name;
                            dataList.appendChild(option);
                        });
                    })
                    .catch(error => {
                        console.error('There was a problem with the fetch operation:', error);
                    });
            }
        });
    }

    setupAutocomplete(departureInput, 'departure-list');
    setupAutocomplete(arrivalInput, 'arrival-list');
});

// Функция инициализации модального окна
function initializeModal() {
    const modal = document.getElementById("customModal");
    const closeBtn = document.getElementsByClassName("custom-close-btn")[0];

    if (closeBtn && modal) {
        // Закрытие по кнопке
        closeBtn.onclick = function() {
            modal.style.display = "none";
            document.body.classList.remove('modal-open');
        }

        // Закрытие по клику вне модального окна
        window.onclick = function(event) {
            if (event.target === modal) {
                modal.style.display = "none";
                document.body.classList.remove('modal-open');
            }
        }
    }
}

// Функция открытия модального окна с данными поездки
function openTripModal(tripId) {
    const modal = document.getElementById("customModal");
    if (!modal) return;

    // Загрузка данных поездки
    fetch(`/get_trip_details_profile/${tripId}/`)
        .then(response => response.json())
        .then(data => {
            console.log('Полученные данные:', data); // Для отладки
            
            // Заполнение данных в модальном окне
            document.getElementById('modal-departure-city').textContent = data.departure_address || '';
            document.getElementById('modal-departure-time').textContent = data.departure_time || '';
            document.getElementById('modal-passengers-count').textContent = data.passengers_count || 0;
            document.getElementById('modal-max-passengers').textContent = data.max_passengers || 0;
            document.getElementById('modal-destination-city').textContent = data.destination_address || '';
            document.getElementById('modal-arrival-time').textContent = data.arrival_time || '';
            document.getElementById('modal-price').textContent = `${data.price} ₽` || '0 ₽';

            // Очищаем и заполняем список пассажиров, если есть элемент списка пассажиров
            const passengersList = document.getElementById('modal-passengers-list');
            if (passengersList) {
                passengersList.innerHTML = '';
                
                if (data.passengers && data.passengers.length > 0) {
                    data.passengers.forEach(passenger => {
                        const li = document.createElement('li');
                        li.classList.add('modal-passenger-item');
                        li.textContent = `${passenger.first_name} ${passenger.last_name}`;
                        passengersList.appendChild(li);
                    });
                } else {
                    const li = document.createElement('li');
                    li.classList.add('modal-passenger-item');
                    li.textContent = 'Пока нет пассажиров';
                    passengersList.appendChild(li);
                }
            }

            // Обновляем время до начала поездки, если есть такой элемент
            if (data.departure_datetime && document.getElementById('modal-time-until')) {
                const timeUntil = document.getElementById('modal-time-until');
                updateTimeUntil(data.departure_datetime);
            }

            // Отображение модального окна
            modal.style.display = "flex";
            document.body.classList.add('modal-open');
        })
        .catch(error => {
            console.error('Ошибка при загрузке данных:', error);
        });
}

// Функция для обновления времени до начала поездки
function updateTimeUntil(departureDatetime) {
    const departure = new Date(departureDatetime);
    const now = new Date();
    const diff = departure - now;
    
    const timeUntil = document.getElementById('modal-time-until');
    
    if (diff <= 0) {
        timeUntil.textContent = 'Поездка уже началась';
        return;
    }
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    let timeString = '';
    if (days > 0) timeString += `${days} д. `;
    if (hours > 0) timeString += `${hours} ч. `;
    timeString += `${minutes} мин.`;
    
    timeUntil.textContent = timeString;
}

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация модального окна
    initializeModal();

    // Добавление обработчиков для всех кнопок деталей поездки
    const tripDetailButtons = document.querySelectorAll('[data-trip-id]');
    tripDetailButtons.forEach(button => {
        button.onclick = function() {
            const tripId = this.getAttribute('data-trip-id');
            openTripModal(tripId);
        };
    });

    // Обработчик для кнопки отмены
    const cancelButton = document.querySelector('button[type="button"]');
    if (cancelButton) {
        cancelButton.onclick = function() {
            window.location.href = '/profile/';
        };
    }
});