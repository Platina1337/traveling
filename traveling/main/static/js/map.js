let map;
let marker;
let searchControl;
let currentPoint = null;
let currentAddressType; // 'departure' или 'destination'
let selectedCity; // текущий выбранный город
let mapInitialized = false; // Флаг, чтобы инициализировать карту только один раз

// Функция для получения адреса по координатам
function getAddress(coords) {
    ymaps.geocode(coords).then(function(res) {
        const firstGeoObject = res.geoObjects.get(0);
        const address = firstGeoObject ? firstGeoObject.getAddressLine() : 'Не удалось определить адрес';
        document.getElementById('addressSearch').value = address;
        document.getElementById('selectedAddress').textContent = address;
    }).catch(function(err) {
        console.error('Geocoding error:', err);
        document.getElementById('selectedAddress').textContent = 'Ошибка при получении адреса';
    });
}

// Инициализация карты
function initMap() {
    if (mapInitialized) return;
    
    map = new ymaps.Map('map', {
        center: [55.76, 37.64],
        zoom: 10
    });

    marker = new ymaps.Placemark([55.76, 37.64], {}, {
        draggable: true
    });

    map.geoObjects.add(marker);

    // Добавляем поиск
    searchControl = new ymaps.control.SearchControl({
        options: {
            provider: 'yandex#search'
        }
    });

    map.controls.add(searchControl);

    // Обработчик клика по карте
    map.events.add('click', function(e) {
        const coords = e.get('coords');
        updateMarker(coords);
        getAddress(coords);
    });

    // Обработчик перетаскивания маркера
    marker.events.add('dragend', function(e) {
        const coords = e.get('target').geometry.getCoordinates();
        getAddress(coords);
    });

    mapInitialized = true;
}

// Обновление маркера на карте
function updateMarker(coords) {
    if (marker) {
        map.geoObjects.remove(marker);
    }
    
    marker = new ymaps.Placemark(coords, {}, {
        draggable: true
    });
    
    map.geoObjects.add(marker);
}

// Показать модальное окно с картой
function showMapModal(city) {
    const mapModalElement = document.getElementById('mapModal');
    const mapModal = bootstrap.Modal.getInstance(mapModalElement) || new bootstrap.Modal(mapModalElement);

    if (!mapInitialized && typeof ymaps !== 'undefined' && ymaps.ready) {
        ymaps.ready(initMap);
    } else if (!mapInitialized) {
        alert("Карта еще не загружена. Пожалуйста, подождите или проверьте консоль на ошибки API Яндекс.Карт.");
        return;
    }
    
    mapModalElement.addEventListener('shown.bs.modal', function onModalShown() {
        if (map && mapInitialized) {
            ymaps.geocode(city).then(function(res) {
                const firstGeoObject = res.geoObjects.get(0);
                if (firstGeoObject) {
                    const coords = firstGeoObject.geometry.getCoordinates();
                    map.setCenter(coords, 12);
                } else {
                    map.setCenter([55.76, 37.64], 10);
                }
                map.container.fitToViewport();
            }).catch(function(err) {
                console.error("Ошибка геокодирования для города " + city + ":", err);
                if (map) map.container.fitToViewport();
            });
        }
    }, { once: true });

    mapModal.show();
}

// Обработчики кнопок выбора адреса
document.getElementById('showDepartureMap').addEventListener('click', function() {
    currentAddressType = 'departure';
    selectedCity = document.getElementById('departure').value;
    if (selectedCity) {
        showMapModal(selectedCity);
    } else {
        alert('Сначала выберите город отправления');
    }
});

document.getElementById('showDestinationMap').addEventListener('click', function() {
    currentAddressType = 'destination';
    selectedCity = document.getElementById('arrival').value;
    if (selectedCity) {
        showMapModal(selectedCity);
    } else {
        alert('Сначала выберите город прибытия');
    }
});

// Подтверждение выбора адреса
document.getElementById('confirmAddress').addEventListener('click', function() {
    if (marker) {
        const coords = marker.geometry.getCoordinates();
        const address = document.getElementById('selectedAddress').textContent;
        
        // Обновляем отображение адреса в соответствующем блоке
        const departureDisplay = document.getElementById('departureAddressDisplay');
        const destinationDisplay = document.getElementById('destinationAddressDisplay');
        
        if (currentAddressType === 'departure' && departureDisplay) {
            departureDisplay.textContent = address;
            departureDisplay.style.display = address ? 'block' : 'none';
        } else if (currentAddressType === 'destination' && destinationDisplay) {
            destinationDisplay.textContent = address;
            destinationDisplay.style.display = address ? 'block' : 'none';
        }
        
        const mapModalInstance = bootstrap.Modal.getInstance(document.getElementById('mapModal'));
        if (mapModalInstance) {
            mapModalInstance.hide();
        }
    } else {
        alert("Пожалуйста, выберите точку на карте.");
    }
});

// Поиск по адресу в модальном окне
document.getElementById('addressSearch').addEventListener('input', function(e) {
    const address = e.target.value;
    if (address.length > 2 && map) {
        ymaps.geocode(address, { results: 1 }).then(function(res) {
            const firstGeoObject = res.geoObjects.get(0);
            if (firstGeoObject) {
                const coords = firstGeoObject.geometry.getCoordinates();
                map.setCenter(coords, 15);
                updateMarker(coords);
            }
        }).catch(function(err){
            console.warn("Ошибка при поиске адреса:", err);
        });
    }
});

// Инициализация карты после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    if (typeof ymaps !== 'undefined') {
        ymaps.ready(initMap);
    }
});

