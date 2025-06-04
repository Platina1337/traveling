document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('deleteModal');
    const closeBtn = document.querySelector('.close');
    const cancelBtn = document.querySelector('.modal-button-cancel');
    const confirmBtn = document.getElementById('confirmDelete');
    let deleteType = '';
    let tripId = '';
    let carId = '';

    // Объект для хранения статусов всех поездок
    const tripStatuses = {};

    // При загрузке страницы получаем статусы всех поездок
    fetchAllTripsStatuses();

    // Функция для получения статусов всех поездок
    function fetchAllTripsStatuses() {
        // Собираем все ID поездок со страницы
        const tripIds = [];
        document.querySelectorAll('.delete-button[data-trip-id]').forEach(button => {
            const id = button.getAttribute('data-trip-id');
            if (id && !tripIds.includes(id)) {
                tripIds.push(id);
            }
        });

        // Если нет поездок, выходим
        if (tripIds.length === 0) return;

        // Отправляем запрос на получение статусов всех поездок
        fetch('/get_all_trips_statuses/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ trip_ids: tripIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.statuses) {
                // Сохраняем статусы и обновляем интерфейс
                Object.assign(tripStatuses, data.statuses);
                updateDeleteButtonsUI();
            }
        })
        .catch(error => console.error('Error fetching trips statuses:', error));
    }

    // Добавляем обработчики событий для кнопок удаления автомобилей
    document.querySelectorAll('.delete-car-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            carId = this.getAttribute('data-car-id');
            
            // Проверяем, не используется ли автомобиль в активных поездках
            fetch(`/check_car_active_trips/${carId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.has_active_trips) {
                        if (data.has_in_progress_trips) {
                            alert('Невозможно удалить автомобиль, т.к. он используется в начатой поездке. Сначала завершите поездку.');
                        } else {
                            alert('Невозможно удалить автомобиль, т.к. он используется в запланированной поездке. Сначала отмените поездку.');
                        }
                    } else {
                        // Если автомобиль не используется в активных поездках, показываем подтверждение
                        deleteType = 'car';
                        modal.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке автомобиля:', error);
                    // Перестраховка: в случае ошибки запроса все равно показываем диалог подтверждения
                    deleteType = 'car';
                    modal.style.display = 'block';
                });
        });
    });

    // Функция обновления интерфейса кнопок удаления
    function updateDeleteButtonsUI() {
        document.querySelectorAll('.delete-button').forEach(button => {
            const btnTripId = button.getAttribute('data-trip-id');
            const btnDeleteType = button.getAttribute('data-delete-type');
            
            // Если это кнопка удаления поездки и поездка начата
            if (btnDeleteType === 'trip' && tripStatuses[btnTripId] === 'in_progress') {
                button.disabled = true;
                button.classList.add('disabled-button');
                button.title = 'Нельзя удалить начатую поездку';
            } 
            // Если это кнопка выхода из поездки и поездка начата
            else if (btnDeleteType === 'passenger' && tripStatuses[btnTripId] === 'in_progress') {
                button.disabled = true;
                button.classList.add('disabled-button');
                button.title = 'Нельзя выйти из начатой поездки';
            }
        });
    }

    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', function() {
            tripId = this.getAttribute('data-trip-id');
            deleteType = this.getAttribute('data-delete-type');
            
            // Проверяем статус поездки перед открытием модального окна
            if ((deleteType === 'trip' || deleteType === 'passenger') && 
                tripStatuses[tripId] === 'in_progress') {
                const message = deleteType === 'trip' 
                    ? 'Нельзя удалить начатую поездку. Сначала завершите поездку.'
                    : 'Нельзя выйти из начатой поездки.';
                alert(message);
                return;
            }
            
            modal.style.display = 'block';
        });
    });

    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    cancelBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    confirmBtn.addEventListener('click', function() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        let url;
        
        // Определяем URL в зависимости от типа удаляемого объекта
        if (deleteType === 'trip') {
            url = `/delete_trip/${tripId}/`;
        } else if (deleteType === 'passenger') {
            url = `/leave_trip/${tripId}/`;
        } else if (deleteType === 'car') {
            url = `/delete_car/${carId}/`;
        } else {
            console.error('Unknown delete type:', deleteType);
            modal.style.display = 'none';
            return;
        }
        
        // Проверяем, можно ли удалить поездку/пассажира
        if ((deleteType === 'trip' || deleteType === 'passenger') && 
            tripStatuses[tripId] === 'in_progress') {
            const message = deleteType === 'trip' 
                ? 'Нельзя удалить начатую поездку. Сначала завершите поездку.'
                : 'Нельзя выйти из начатой поездки.';
            alert(message);
            modal.style.display = 'none';
            return;
        }
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                return response.json().then(data => {
                    throw new Error(data.message || 'Произошла ошибка при удалении.');
                });
            }
        })
        .then(data => {
            if (data && data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Произошла ошибка при удалении.');
            }
        })
        .catch(error => {
            alert(error.message || 'Произошла ошибка при удалении.');
        });
    });

    document.getElementById('passwordForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);

        fetch(this.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closePasswordModal();
                alert('Пароль успешно изменен');
            } else {
                if (data.errors) {
                    const errors = JSON.parse(data.errors);
                    for (const [field, messages] of Object.entries(errors)) {
                        alert(`${field}: ${messages.map(message => message.message).join(', ')}`);
                    }
                } else {
                    alert('Ошибка при смене пароля');
                }
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
    });

    window.openPasswordModal = function() {
        document.getElementById('passwordModal').style.display = 'block';
    }

    window.closePasswordModal = function() {
        document.getElementById('passwordModal').style.display = 'none';
    }

    document.querySelector('.navbar-toggle').addEventListener('click', function() {
        document.querySelector('.header-buttons').classList.toggle('active');
    });

    function updateSVGDisplay() {
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
    }

    window.addEventListener('resize', updateSVGDisplay);
    document.addEventListener('DOMContentLoaded', updateSVGDisplay);

    document.querySelectorAll('.add-button').forEach(function(button) {
        button.addEventListener('click', function() {
            const tripId = this.dataset.tripId;
            console.log(`Добавление пассажира в поездку с ID: ${tripId}`);
            fetch(`/add_passenger/${tripId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
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
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        });
    });

    document.querySelectorAll('.notification-action').forEach(function(button) {
        button.addEventListener('click', function() {
            const notificationId = this.dataset.notificationId;
            const action = this.dataset.action;
            console.log(`Обработка действия ${action} для уведомления с ID: ${notificationId}`);
            fetch(`/handle_passenger_request/${notificationId}/${action}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
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
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        });
    });

    const avatarIcon = document.getElementById('avatar-icon');
    const avatarInput = document.getElementById('avatar-input');
    const avatarImage = document.getElementById('avatar-image');
    const saveButton = document.querySelector('.profile-save');

    avatarIcon.addEventListener('click', function() {
        avatarInput.click();
    });

    avatarInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                avatarImage.src = e.target.result;
                avatarIcon.innerHTML = '';
                avatarIcon.appendChild(avatarImage);
                saveButton.classList.add('needs-save');
            }
            reader.readAsDataURL(file);
        }
    });

    window.editField = function(field) {
        const displayElement = document.getElementById(field + '_display');
        const inputElement = document.getElementById(field + '_input');

        if (inputElement.style.display === 'none') {
            inputElement.style.display = 'block';
            displayElement.style.display = 'none';
        } else {
            inputElement.style.display = 'none';
            displayElement.style.display = 'block';
        }
    }

let currentTripId = null; // Добавляем глобальную переменную для текущего tripId

document.querySelectorAll('.openModalBtn').forEach(function(button) {
    button.addEventListener('click', function() {
        const tripId = this.dataset.tripId;
        const userTrip = this.dataset.userTrip === 'True';

        if (!tripId) {
            console.error('tripId is undefined');
            return;
        }

        currentTripId = tripId; // Устанавливаем текущий tripId

        fetch(`/get_trip_details_profile/${tripId}/`)
            .then(response => response.json())
            .then(data => {
                console.log(data);
                const fromAddressElem = document.getElementById('trip-from-address');
                const toAddressElem = document.getElementById('trip-to-address');
                const seatsElem = document.getElementById('trip-seats');
                const priceElem = document.getElementById('trip-price');
                const departureDateElem = document.getElementById('trip-departure-date');
                const arrivalDateElem = document.getElementById('trip-arrival-date');
                const driverInfoElem = document.getElementById('driver-info');
                const priceSectionElem = document.getElementById('trip-price-section');
                const passengersInfoElem = document.getElementById('passengers-info');
                const tripActionsElem = document.getElementById('trip-actions');
                const startTripBtn = document.getElementById('start-trip-btn');
                const endTripBtn = document.getElementById('end-trip-btn');
                const passengersListElem = document.getElementById('passengers-list');

                if (fromAddressElem) fromAddressElem.textContent = data.departure_address || '';
                if (toAddressElem) toAddressElem.textContent = data.destination_address || '';
                if (seatsElem) seatsElem.textContent = `${data.seats_taken || 0}/${data.total_seats || 0}`;
                if (priceElem) priceElem.textContent = (data.price || 0) + " р";

                if (departureDateElem) {
                    departureDateElem.textContent = `${data.departure_date || ''} ${data.departure_time || ''}`;
                }
                if (arrivalDateElem) {
                    arrivalDateElem.textContent = `${data.arrival_date || ''} ${data.arrival_time || ''}`;
                }

                    // Сохраняем статус поездки глобально
                    tripStatus = data.status;

                    // Показываем/скрываем предупреждение о статусе поездки
                    const tripStatusMessage = document.getElementById('trip-status-message');
                    if (tripStatusMessage) {
                        tripStatusMessage.style.display = data.status === 'in_progress' ? 'block' : 'none';
                    }

                if (userTrip) {
                    if (driverInfoElem) driverInfoElem.style.display = 'none';
                    if (priceSectionElem) priceSectionElem.style.display = 'none';

                    if (passengersInfoElem) passengersInfoElem.style.display = 'block';
                    if (tripActionsElem) tripActionsElem.style.display = 'block';
                    if (startTripBtn) startTripBtn.style.display = data.status === 'planned' ? 'block' : 'none';
                    if (endTripBtn) endTripBtn.style.display = data.status === 'in_progress' ? 'block' : 'none';

                    if (passengersListElem) {
                        passengersListElem.innerHTML = ''; // Clear the list before adding passengers
                        if (Array.isArray(data.passengers)) {
                            data.passengers.forEach((passenger, index) => {
                                const listItem = document.createElement('li');
                                listItem.textContent = passenger.name;

                                    // Добавляем кнопку "Удалить" только если поездка еще не началась
                                    if (data.status === 'planned') {
                                const removeButton = document.createElement('button');
                                removeButton.textContent = 'Удалить';
                                removeButton.classList.add('remove-passenger-btn');
                                removeButton.dataset.passengerId = passenger.id;

                                removeButton.addEventListener('click', function() {
                                    removePassenger(tripId, passenger.id, index);
                                });

                                listItem.appendChild(removeButton);
                                    }
                                    
                                passengersListElem.appendChild(listItem);
                            });
                        }
                    }
                } else {
                    if (driverInfoElem) driverInfoElem.style.display = 'block';
                    if (priceSectionElem) priceSectionElem.style.display = 'block';
                    if (passengersInfoElem) passengersInfoElem.style.display = 'none';
                    if (tripActionsElem) tripActionsElem.style.display = 'none';

                    if (data.driver_photo) {
                        const driverPhotoElem = document.getElementById('driver-photo');
                        if (driverPhotoElem) driverPhotoElem.src = data.driver_photo;
                    }
                    const driverNameElem = document.getElementById('driver-name');
                    const driverProfileLinkElem = document.getElementById('driver-profile-link');

                    if (driverNameElem) {
                        driverNameElem.textContent = `${data.driver_name || ''} ${data.driver_surname || ''}`;
                    }
                    if (driverProfileLinkElem) {
                        driverProfileLinkElem.href = `/profile_user/?user_id=${data.driver_id}`;
                    }

                    const driverDescElem = document.getElementById('driver-description');
                    if (driverDescElem) driverDescElem.textContent = data.driver_description || '';

                    const driverRatingElem = document.getElementById('driver-rating');
                    if (driverRatingElem) {
                        driverRatingElem.textContent = data.driver_rating !== undefined ? data.driver_rating + "★" : "No rating";
                    }
                }

                const customModalElem = document.getElementById('customModal');
                if (customModalElem) customModalElem.style.display = 'block';
                document.body.classList.add('modal-open');

                    // Обновляем состояние кнопок удаления поездки на странице
                    updateDeleteButtons(data.status);
            })
            .catch(error => console.error('Error fetching trip details:', error));
    });
});

const customCloseBtn = document.querySelector('.custom-close-btn');
if (customCloseBtn) {
    customCloseBtn.addEventListener('click', function() {
        const customModalElem = document.getElementById('customModal');
        if (customModalElem) customModalElem.style.display = 'none';
        document.body.classList.remove('modal-open');
        currentTripId = null; // Сбрасываем текущий tripId
    });
    }

const startTripBtn = document.getElementById('start-trip-btn');
if (startTripBtn) {
    startTripBtn.addEventListener('click', function() {
        if (!currentTripId) {
            console.error('No tripId available');
            return;
        }

        fetch(`/start_trip/${currentTripId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Поездка началась');
                startTripBtn.style.display = 'none';
                endTripBtn.style.display = 'block';

                const tripStatusElem = document.querySelector(`.trip-status[data-trip-id="${currentTripId}"]`);
                if (tripStatusElem) {
                    tripStatusElem.textContent = 'in_progress';
                }
            } else {
                alert(data.message || 'Ошибка при начале поездки');
            }
        })
        .catch(error => console.error('Error starting trip:', error));
    });
}

const endTripBtn = document.getElementById('end-trip-btn');
if (endTripBtn) {
    endTripBtn.addEventListener('click', function() {
        if (!currentTripId) {
            console.error('No tripId available');
            return;
        }

        fetch(`/end_trip/${currentTripId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Поездка завершена');
                const customModalElem = document.getElementById('customModal');
                if (customModalElem) customModalElem.style.display = 'none';
                document.body.classList.remove('modal-open');
                window.location.reload();
            } else {
                alert(data.message || 'Ошибка при завершении поездки');
            }
        })
        .catch(error => console.error('Error ending trip:', error));
    });
}

function removePassenger(tripId, passengerId, index) {
    console.log('Trip ID:', tripId);
    console.log('Passenger ID:', passengerId);

        // Проверяем, не началась ли уже поездка
        if (tripStatus === 'in_progress') {
            alert('Нельзя удалить пассажира из начатой поездки.');
            return;
        }

    if (!tripId || !passengerId) {
        console.error('Trip ID or Passenger ID is missing');
        return;
    }

    fetch(`/remove_passenger/${tripId}/${passengerId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Пассажир удален');
            const passengersListElem = document.getElementById('passengers-list');
            if (passengersListElem) {
                const listItems = passengersListElem.getElementsByTagName('li');
                if (listItems[index]) {
                    passengersListElem.removeChild(listItems[index]);
                }
            }
        } else {
            alert(data.message || 'Ошибка при удалении пассажира');
        }
    })
    .catch(error => console.error('Error removing passenger:', error));
}

    // Глобальная переменная для хранения статуса поездки
    let tripStatus = null;

    // Функция для обновления состояния кнопок удаления
    function updateDeleteButtons(status) {
        // Найдем все кнопки удаления для поездок водителя
        document.querySelectorAll('.delete-button[data-delete-type="trip"]').forEach(button => {
            const tripId = button.getAttribute('data-trip-id');
            
            // Если это та поездка, что мы просматриваем, и она уже началась
            if (tripId === currentTripId && status === 'in_progress') {
                button.disabled = true;
                button.classList.add('disabled-button');
                button.title = 'Нельзя удалить начатую поездку';
            } else {
                button.disabled = false;
                button.classList.remove('disabled-button');
                button.removeAttribute('title');
}
        });
    }

    // Функция для проверки статусов всех поездок и отключения кнопок удаления
    function updateTripDeleteButtons() {
        // Собираем все ID поездок на странице
        const tripIds = [];
        document.querySelectorAll('[data-trip-id]').forEach(el => {
            const tripId = el.getAttribute('data-trip-id');
            if (tripId) tripIds.push(tripId);
        });
        
        if (tripIds.length === 0) return;

        // Запрашиваем статусы всех поездок
        fetch('/get_all_trips_statuses/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ trip_ids: tripIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем состояние кнопок для каждой поездки
                Object.entries(data.statuses).forEach(([tripId, status]) => {
                    const tripElement = document.querySelector(`[data-trip-id="${tripId}"]`);
                    if (tripElement) {
                        const deleteBtn = tripElement.querySelector('.delete-trip-btn');
                        const removePassengerBtns = tripElement.querySelectorAll('.remove-passenger-btn');
                        
                        if (status === 'in_progress') {
                            // Если поездка начата, отключаем кнопки удаления
                            if (deleteBtn) {
                                deleteBtn.disabled = true;
                                deleteBtn.title = 'Нельзя удалить начатую поездку';
                                deleteBtn.classList.add('disabled-btn');
                            }
                            
                            // Отключаем кнопки удаления пассажиров
                            removePassengerBtns.forEach(btn => {
                                btn.disabled = true;
                                btn.title = 'Нельзя удалить пассажира из начатой поездки';
                                btn.classList.add('disabled-btn');
                            });
                        }
                    }
                });
            }
        })
        .catch(error => console.error('Ошибка при получении статусов поездок:', error));
    }

    // Получаем CSRF токен из куки
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Запускаем проверку при загрузке страницы
    updateTripDeleteButtons();
    
    // Добавляем CSS для отключенных кнопок
    const style = document.createElement('style');
    style.textContent = `
        .disabled-btn {
            opacity: 0.5;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
    
    // Изменяем функцию открытия модального окна с информацией о поездке
    const originalOpenTripDetailsModal = window.openTripDetailsModal;
    if (originalOpenTripDetailsModal) {
        window.openTripDetailsModal = function(tripId) {
            originalOpenTripDetailsModal(tripId);
            
            // Добавляем предупреждение о невозможности удаления если поездка в процессе
            fetch(`/get_trip_details_profile/${tripId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'in_progress') {
                        const modalContent = document.querySelector('.trip-modal-content');
                        if (modalContent) {
                            const warningEl = document.createElement('div');
                            warningEl.className = 'trip-status-warning';
                            warningEl.innerHTML = '<p><strong>Внимание:</strong> Поездка уже начата. Удаление поездки и изменение списка пассажиров невозможно.</p>';
                            warningEl.style.color = '#e74c3c';
                            warningEl.style.padding = '10px';
                            warningEl.style.marginTop = '10px';
                            warningEl.style.border = '1px solid #e74c3c';
                            warningEl.style.borderRadius = '5px';
                            
                            modalContent.insertBefore(warningEl, modalContent.querySelector('#trip-actions'));
                        }
                    }
                })
                .catch(error => console.error('Ошибка при получении данных о поездке:', error));
        };
    }
});