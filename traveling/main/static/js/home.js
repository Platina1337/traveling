document.addEventListener('DOMContentLoaded', function() {
    // Кнопки публикации и поиска
    const publishButton = document.getElementById('publish-button');
    const findButton = document.getElementById('find-button');

    if (publishButton) {
        publishButton.addEventListener('click', function() {
            window.location.href = '/add_trip/';
        });
    }

    if (findButton) {
        findButton.addEventListener('click', function() {
            window.location.href = '/catalog/';
        });
    }

    // Кнопка навбара
    const navbarToggle = document.querySelector('.navbar-toggle');
    if (navbarToggle) {
        navbarToggle.addEventListener('click', function() {
            const headerButtons = document.querySelector('.header-buttons');
            if (headerButtons) {
                headerButtons.classList.toggle('active');
            }
        });
    }

    // SVG адаптивность
    const largeSVG = document.querySelector('.svg-large');
    const smallSVG = document.querySelector('.svg-small');

    if (largeSVG && smallSVG) {
        window.addEventListener('resize', function() {
            if (window.innerWidth <= 420) {
                largeSVG.style.display = 'none';
                smallSVG.style.display = 'block';
            } else {
                largeSVG.style.display = 'block';
                smallSVG.style.display = 'none';
            }
        });

        // Инициализация при загрузке страницы
        window.dispatchEvent(new Event('resize'));
    }

    // Автозаполнение городов
    const departureInput = document.getElementById('departure');
    const arrivalInput = document.getElementById('arrival');

    function setupAutocomplete(input, dataListId) {
        if (!input) return;

        input.addEventListener('input', function () {
            const value = this.value;
            const dataList = document.getElementById(dataListId);
            if (!dataList) return;
            
            dataList.innerHTML = '';

            if (value) {
                const url = `/city_suggestions?q=${encodeURIComponent(value)}`;

                fetch(url)
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        } else {
                            throw new Error(`Network response was not ok: ${response.statusText}`);
                        }
                    })
                    .then(cities => {
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

    if (departureInput) {
        setupAutocomplete(departureInput, 'departure-list');
    }
    if (arrivalInput) {
        setupAutocomplete(arrivalInput, 'arrival-list');
    }

    // FAQ
    const faqItems = document.querySelectorAll('.faq-item');
    if (faqItems.length > 0) {
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            const answer = item.querySelector('.faq-answer');
            const icon = question?.querySelector('.faq-icon');

            if (question && answer && icon) {
                question.addEventListener('click', () => {
                    faqItems.forEach(i => {
                        if (i !== item) {
                            i.classList.remove('open');
                            const otherAnswer = i.querySelector('.faq-answer');
                            const otherIcon = i.querySelector('.faq-icon');
                            if (otherAnswer) otherAnswer.style.maxHeight = 0;
                            if (otherIcon) otherIcon.textContent = '+';
                        }
                    });

                    item.classList.toggle('open');
                    icon.textContent = item.classList.contains('open') ? '-' : '+';

                    if (item.classList.contains('open')) {
                        answer.style.maxHeight = answer.scrollHeight + 'px';
                    } else {
                        answer.style.maxHeight = 0;
                    }
                });
            }
        });
    }
});