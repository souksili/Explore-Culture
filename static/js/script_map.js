document.addEventListener('DOMContentLoaded', () => {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
        window.location.href = '/connexion';
    } else {
        fetch('/dashboard', {
            method: 'GET',
        });
    }
});

document.getElementById('burgerIcon').addEventListener('click', () => {
    const menuContent = document.getElementById('menuContent');
    menuContent.style.display = menuContent.style.display === 'flex' ? 'none' : 'flex';
});

const culturalAddresses = JSON.parse(localStorage.getItem('culturalAddresses')) || [];
const map = L.map('map').setView([31.7917, -7.0926], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

if (culturalAddresses.length > 0) {
    const waypoints = culturalAddresses.map(({ latitude, longitude, nom, description }, index) => {
        const emoji = index === 0 ? '🏁' : index === culturalAddresses.length - 1 ? '🏁' : '📍';
        L.marker([latitude, longitude], { icon: L.divIcon({ className: 'emoji-marker', html: emoji }) })
            .addTo(map)
            .bindPopup(`<b>${nom}</b><br>${description || 'Aucune description'}`);
        return L.latLng(latitude, longitude);
    });

    const routeControl = L.Routing.control({ waypoints, createMarker: () => null }).addTo(map);

    const animatedMarker = L.marker([0, 0], { icon: L.divIcon({ className: 'emoji-marker', html: '🚗' }) }).addTo(map);
    const startButton = document.getElementById('startButton');
    const toggleInstructions = document.getElementById('toggleInstructions');

    let instructionsVisible = true;

    routeControl.on('routesfound', ({ routes }) => {
        const routeCoordinates = routes[0].coordinates;
        startButton.disabled = routeCoordinates.length === 0;

        startButton.addEventListener('click', () => {
            let index = 0;
            const interval = setInterval(() => {
                if (index < routeCoordinates.length) {
                    animatedMarker.setLatLng(routeCoordinates[index]);
                    index++;
                } else {
                    clearInterval(interval);
                    showEndTripModal();
                }
            }, 50);
        });

        // Afficher le modal
        const showEndTripModal = () => {
            const endTripModal = document.getElementById('endTripModal');
            endTripModal.style.display = 'flex';
        };

        // Cacher le modal après fermeture
        document.getElementById('closeModal').addEventListener('click', () => {
            document.getElementById('endTripModal').style.display = 'none';
        });

        // Gestion des étoiles pour avis
        const stars = document.querySelectorAll('.star');
        let selectedRating = 0;

        stars.forEach(star => {
            star.addEventListener('click', () => {
                stars.forEach(s => s.classList.remove('selected'));
                star.classList.add('selected');
                selectedRating = star.getAttribute('data-value');
            });
        });

        // Soumettre la note
        document.getElementById('submitRating').addEventListener('click', () => {
            if (selectedRating > 0) {
                alert(`Merci pour votre avis de ${selectedRating} étoiles !`);
                document.getElementById('endTripModal').style.display = 'none';
            } else {
                alert('Veuillez sélectionner une note avant de soumettre.');
            }
        });
    });

    toggleInstructions.addEventListener('click', () => {
        const routingContainer = document.querySelector('.leaflet-routing-container');
        if (routingContainer) {
            instructionsVisible = !instructionsVisible;
            routingContainer.style.display = instructionsVisible ? 'block' : 'none';
            toggleInstructions.textContent = instructionsVisible ? 'Masquer Instructions' : 'Afficher Instructions';
        }
    });
}

document.getElementById('toggleChat').addEventListener('click', () => {
    const chatContainer = document.getElementById('chatContainer');
    const toggleChatButton = document.getElementById('toggleChat');

    if (chatContainer.style.display === 'none') {
        chatContainer.style.display = 'flex';
        toggleChatButton.textContent = 'Masquer Chat';
    } else {
        chatContainer.style.display = 'none';
        toggleChatButton.textContent = 'Afficher Chat';
    }
});

function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    if (!message) return;

    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML += `<p><b>Vous :</b> ${message}</p>`;
    userInput.value = '';

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        chatBox.innerHTML += `<p><b>Assistant :</b> ${data.response}</p>`;
        if (data.addresses && Array.isArray(data.addresses)) {
            localStorage.setItem('culturalAddresses', JSON.stringify(data.addresses));
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(console.error);
}

let lastCulturalAddresses = localStorage.getItem('culturalAddresses');

function checkLocalStorage() {
    const currentCulturalAddresses = localStorage.getItem('culturalAddresses');
    if (currentCulturalAddresses !== lastCulturalAddresses) {
        lastCulturalAddresses = currentCulturalAddresses;
        location.reload();
    }
}

setInterval(checkLocalStorage, 500);

window.addEventListener('storage', (event) => {
    if (event.key === 'culturalAddresses') {
        location.reload();
    }
});

document.getElementById('logoutLink').addEventListener('click', (event) => {
    event.preventDefault();

    fetch('/deconnexion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Déconnexion réussie") {
            localStorage.removeItem('access_token');
            window.location.href = '/connexion';
        } else {
            alert('Erreur lors de la déconnexion');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Erreur lors de la déconnexion');
    });
});
