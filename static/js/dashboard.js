/* Dashboard-specific JavaScript functionality */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard script loaded');
    
    // Enhanced tablet app-like interactions
    const appCards = document.querySelectorAll('.app-card.available, .app-card.in-development');
    
    appCards.forEach(card => {
        card.addEventListener('touchstart', function() {
            if (navigator.vibrate) {
                navigator.vibrate(10);
            }
        });
        
        card.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(-4px) scale(0.98)';
        });
        
        card.addEventListener('mouseup', function() {
            this.style.transform = '';
        });
    });
    
    // Update time and date
    function updateDateTime() {
        const now = new Date();
        
        // Check if elements exist before updating
        const clockElement = document.getElementById('live-clock');
        const dateElement = document.getElementById('live-date');
        
        if (clockElement) {
            // Update time (12-hour format)
            const timeOptions = {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            };
            clockElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
        }
        
        if (dateElement) {
            // Update date
            const dateOptions = {
                weekday: 'long',
                month: 'short',
                day: 'numeric'
            };
            dateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
        }
        
        // Update greeting based on time
        updateGreeting(now.getHours());
    }
    
    // Update greeting based on time of day
    function updateGreeting(hour) {
        const greetingElement = document.getElementById('dynamic-greeting');
        if (!greetingElement) return;
        
        // Note: User name will be injected by Django template
        const userName = window.dashboardUserName || 'User';
        let greeting;
        
        if (hour < 12) {
            greeting = `Good morning, ${userName}`;
        } else if (hour < 17) {
            greeting = `Good afternoon, ${userName}`;
        } else {
            greeting = `Good evening, ${userName}`;
        }
        
        greetingElement.textContent = greeting;
    }
    
    // Location settings and weather functionality
    const LOCATIONS = {
        auto: { name: 'Auto-detect location', coords: null },
        auckland: { name: 'Auckland, New Zealand', coords: [-36.8485, 174.7633] },
        wellington: { name: 'Wellington, New Zealand', coords: [-41.2865, 174.7762] },
        christchurch: { name: 'Christchurch, New Zealand', coords: [-43.5321, 172.6362] },
        sydney: { name: 'Sydney, Australia', coords: [-33.8688, 151.2093] },
        melbourne: { name: 'Melbourne, Australia', coords: [-37.8136, 144.9631] },
        london: { name: 'London, United Kingdom', coords: [51.5074, -0.1278] }
    };

    // Open location settings modal
    function openLocationSettings() {
        const currentSetting = localStorage.getItem('weather-location') || 'auto';
        
        // Update modal with current setting
        const currentLocationTextElement = document.getElementById('currentLocationText');
        const radioElement = document.getElementById(currentSetting + 'Location');
        
        if (currentLocationTextElement) {
            currentLocationTextElement.textContent = LOCATIONS[currentSetting].name;
        }
        if (radioElement) {
            radioElement.checked = true;
        }
        
        // Show modal
        const modalElement = document.getElementById('locationModal');
        if (modalElement && window.bootstrap) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
    }

    // Save location settings
    function saveLocationSettings() {
        const selectedRadio = document.querySelector('input[name="locationOption"]:checked');
        if (!selectedRadio) return;
        
        const selectedLocation = selectedRadio.value;
        
        // Save to localStorage
        localStorage.setItem('weather-location', selectedLocation);
        
        // Update display
        const currentLocationTextElement = document.getElementById('currentLocationText');
        if (currentLocationTextElement) {
            currentLocationTextElement.textContent = LOCATIONS[selectedLocation].name;
        }
        
        // Close modal
        const modalElement = document.getElementById('locationModal');
        if (modalElement && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        }
        
        // Reload weather with new location
        loadWeather();
        
        // Show success message
        showLocationChangeMessage(LOCATIONS[selectedLocation].name);
    }

    // Show location change message
    function showLocationChangeMessage(locationName) {
        const weatherElement = document.getElementById('weather-info');
        if (weatherElement) {
            weatherElement.innerHTML = `
                <i class="bi bi-check-circle text-success weather-icon"></i>
                <span>Location updated</span>
            `;
            
            // Reload weather after 2 seconds
            setTimeout(() => {
                loadWeather();
            }, 2000);
        }
    }

    // Updated weather loading function
    async function loadWeather() {
        try {
            const preferredLocation = localStorage.getItem('weather-location') || 'auto';
            
            if (preferredLocation === 'auto') {
                // Use geolocation
                if ('geolocation' in navigator) {
                    navigator.geolocation.getCurrentPosition(
                        async (position) => {
                            await fetchWeather(position.coords.latitude, position.coords.longitude);
                        },
                        async (error) => {
                            console.log('Geolocation failed, using Auckland as fallback');
                            await fetchWeather(-36.8485, 174.7633);
                        },
                        { timeout: 5000, enableHighAccuracy: false }
                    );
                } else {
                    await fetchWeather(-36.8485, 174.7633);
                }
            } else {
                // Use selected location
                const coords = LOCATIONS[preferredLocation].coords;
                if (coords) {
                    await fetchWeather(coords[0], coords[1]);
                }
            }
        } catch (error) {
            console.error('Weather loading error:', error);
            showWeatherError();
        }
    }

    // Add initialization for location settings
    function initializeLocationSettings() {
        const savedLocation = localStorage.getItem('weather-location') || 'auto';
        const currentLocationTextElement = document.getElementById('currentLocationText');
        if (currentLocationTextElement) {
            currentLocationTextElement.textContent = LOCATIONS[savedLocation].name;
        }
    }

    // Make functions global so they can be called from HTML
    window.openLocationSettings = openLocationSettings;
    window.saveLocationSettings = saveLocationSettings;
    
    // Fetch weather data
    async function fetchWeather(lat, lon) {
        try {
            const API_KEY = '6853fa8ccafe8f81055f1f63af6a3d21'; // Replace with actual API key
            
            // Skip weather API if no key provided
            if (API_KEY === 'YOUR_OPENWEATHERMAP_API_KEY') {
                showWeatherPlaceholder();
                return;
            }
            
            const response = await fetch(
                `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`,
                { 
                    signal: AbortSignal.timeout(10000) // 10 second timeout
                }
            );
            
            if (!response.ok) throw new Error(`Weather API failed: ${response.status}`);
            
            const data = await response.json();
            displayWeather(data);
        } catch (error) {
            console.error('Weather fetch failed:', error);
            showWeatherError();
        }
    }
    
    // Display weather information
    function displayWeather(data) {
        const weatherElement = document.getElementById('weather-info');
        if (!weatherElement) return;
        
        const temp = Math.round(data.main.temp);
        const condition = data.weather[0].main;
        const icon = getWeatherIcon(condition);
        
        weatherElement.innerHTML = `
            <i class="bi ${icon} weather-icon"></i>
            <span>${temp}°C ${condition}</span>
        `;
    }
    
    // Map weather conditions to Bootstrap icons
    function getWeatherIcon(condition) {
        const iconMap = {
            'Clear': 'bi-sun',
            'Clouds': 'bi-cloud',
            'Rain': 'bi-cloud-rain',
            'Drizzle': 'bi-cloud-drizzle',
            'Thunderstorm': 'bi-cloud-lightning',
            'Snow': 'bi-snow',
            'Mist': 'bi-cloud-fog',
            'Fog': 'bi-cloud-fog',
            'Haze': 'bi-cloud-haze'
        };
        return iconMap[condition] || 'bi-cloud';
    }
    
    // Show placeholder when no API key
    function showWeatherPlaceholder() {
        const weatherElement = document.getElementById('weather-info');
        if (weatherElement) {
            weatherElement.innerHTML = `
                <i class="bi bi-sun weather-icon"></i>
                <span>22°C Sunny</span>
            `;
        }
    }
    
    // Show error state for weather
    function showWeatherError() {
        const weatherElement = document.getElementById('weather-info');
        if (weatherElement) {
            weatherElement.innerHTML = `
                <i class="bi bi-cloud-slash weather-icon"></i>
                <span>Weather unavailable</span>
            `;
        }
    }
    
    // Initialize everything
    console.log('Initializing dashboard features');
    initializeLocationSettings();
    updateDateTime();
    loadWeather();
    
    // Update time every minute
    setInterval(updateDateTime, 60000);
    
    console.log('Dashboard initialization complete');
});
