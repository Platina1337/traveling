document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для кнопок удаления автомобиля
    const deleteCarButtons = document.querySelectorAll('.delete-car-btn');
    
    deleteCarButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const carId = this.getAttribute('data-car-id');
            
            // Проверяем, не используется ли автомобиль в активных поездках
            fetch(`/check_car_active_trips/${carId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.has_active_trips) {
                            // Если автомобиль используется в активных поездках
                            if (data.has_in_progress_trips) {
                                // Если есть начатые поездки
                                alert('Невозможно удалить автомобиль, так как он используется в начатой поездке. Сначала завершите поездку.');
                            } else {
                                // Если есть только запланированные поездки
                                alert('Невозможно удалить автомобиль, так как он используется в запланированной поездке. Сначала отмените поездку.');
                            }
                        } else {
                            // Если автомобиль не используется в активных поездках, подтверждаем удаление
                            if (confirm('Вы уверены, что хотите удалить этот автомобиль?')) {
                                // Отправляем запрос на удаление
                                const form = document.createElement('form');
                                form.method = 'POST';
                                form.action = `/delete_car/${carId}/`;
                                
                                // Добавляем CSRF-токен
                                const csrfInput = document.createElement('input');
                                csrfInput.type = 'hidden';
                                csrfInput.name = 'csrfmiddlewaretoken';
                                csrfInput.value = getCookie('csrftoken');
                                form.appendChild(csrfInput);
                                
                                document.body.appendChild(form);
                                form.submit();
                            }
                        }
                    } else {
                        // Обработка ошибок
                        alert(data.message || 'Произошла ошибка при проверке автомобиля');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке автомобиля:', error);
                    alert('Произошла ошибка при проверке автомобиля. Пожалуйста, попробуйте снова.');
                });
        });
    });
    
    // Функция для получения CSRF-токена из cookie
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
}); 