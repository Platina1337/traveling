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

