if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, showError);
} else {
    document.getElementById('message').innerText = "Geolocation is not supported by this browser.";
}

function showPosition(position) {
    var latitude = position.coords.latitude;
    var longitude = position.coords.longitude;

    fetch('/verify-location', {
        method: 'POST',
        body: JSON.stringify({
            lat: latitude,
            lng: longitude
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json()).then(data => {
        if (data.allowed) {
            window.location.href = "/location-verified";  // Redirect to a route that sets the verified status in session
        } else {
            window.location.href = "/not-on-campus";  // Redirect to a page notifying the user they're not on campus
        }
    });
}

function showError(error) {
    // ... your error handling code ...
}
