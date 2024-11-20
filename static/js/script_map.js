document.addEventListener('DOMContentLoaded', () => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        window.location.href = '/connexion';
    } else {
        fetch('/dashboard', {
            method: 'GET',
        })
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/connexion';
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            window.location.href = '/connexion';
        });
    }
});

document.getElementById('burgerIcon').addEventListener('click', () => {
    const menuContent = document.getElementById('menuContent');
    menuContent.style.display = menuContent.style.display === 'flex' ? 'none' : 'flex';
});

// Initialisation de la carte
const map = L.map('map').setView([31.7917, -7.0926], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Gestion des waypoints et de la navigation
function initializeWaypoints(addresses) {
    const waypoints = addresses.map(({ latitude, longitude, nom, description }, index) => {
        const emoji = index === 0 ? '🏁' : index === addresses.length - 1 ? '🏁' : '📍';
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

        toggleInstructions.addEventListener('click', () => {
            const routingContainer = document.querySelector('.leaflet-routing-container');
            if (routingContainer) {
                instructionsVisible = !instructionsVisible;
                routingContainer.style.display = instructionsVisible ? 'block' : 'none';
                toggleInstructions.textContent = instructionsVisible ? 'Masquer Instructions' : 'Afficher Instructions';
            }
        });
    });
}

// Modal de fin de trajet
function showEndTripModal() {
    const endTripModal = document.getElementById('endTripModal');
    endTripModal.style.display = 'flex';

    document.getElementById('closeModal').addEventListener('click', () => {
        endTripModal.style.display = 'none';
    });

    const stars = document.querySelectorAll('.star');
    let selectedRating = 0;

    stars.forEach(star => {
        star.addEventListener('click', () => {
            stars.forEach(s => s.classList.remove('selected'));
            star.classList.add('selected');
            selectedRating = star.getAttribute('data-value');
        });
    });

    document.getElementById('submitRating').addEventListener('click', () => {
        if (selectedRating > 0) {
            alert(`Merci pour votre avis de ${selectedRating} étoiles !`);
            endTripModal.style.display = 'none';
        } else {
            alert('Veuillez sélectionner une note avant de soumettre.');
        }
    });
}

// Gestion du chat et sauvegarde des adresses
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
            saveHistoriqueToServer(data.addresses); // Sauvegarde dans la BDD
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(console.error);
}

// Sauvegarde des adresses dans la BDD
function saveHistoriqueToServer(addresses) {
    fetch('/api/historique', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({ addresses })
    })
    .then(response => response.json())
    .then(() => fetchHistoriqueFromServer()) // Rafraîchit l'historique après sauvegarde
    .catch(console.error);
}

// Récupération de l'historique depuis la BDD
function fetchHistoriqueFromServer() {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        console.error('Access token is missing');
        return;
    }

    fetch('/api/historique', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(historique => {
        if (!Array.isArray(historique)) {
            throw new TypeError('Le format de la réponse est incorrect.');
        }

        const historiqueList = document.getElementById('historiqueList');
        historiqueList.innerHTML = '';

        if (historique.length === 0) {
            historiqueList.innerHTML = '<li>Aucun historique disponible</li>';
            return;
        }

        // Regrouper les adresses par identifiant historique
        const groupedHistorique = historique.reduce((acc, address) => {
            if (!acc[address.historiqueId]) {
                acc[address.historiqueId] = [];
            }
            acc[address.historiqueId].push(address);
            return acc;
        }, {});

        // Créer des liens cliquables pour chaque groupe d'adresses
        for (const historiqueId in groupedHistorique) {
            const addresses = groupedHistorique[historiqueId];
            const listItem = document.createElement('li');
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = `Itinéraire ${historiqueId}`;
            link.addEventListener('click', (event) => {
                event.preventDefault();
                initializeWaypoints(addresses);
            });
            listItem.appendChild(link);
            historiqueList.appendChild(listItem);
        }
    })
    .catch(error => {
        console.error('Erreur lors de la récupération de l\'historique :', error);
        const historiqueList = document.getElementById('historiqueList');
        historiqueList.innerHTML = '<li>Erreur lors du chargement de l\'historique.</li>';
    });
}

// Gestion du bouton de chat
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

// Déconnexion
document.getElementById('logoutLink').addEventListener('click', (event) => {
    event.preventDefault();

    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        alert('Vous n\'êtes pas connecté.');
        window.location.href = '/connexion';
        return;
    }

    fetch('/deconnexion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Déconnexion réussie") {
            localStorage.removeItem('accessToken');
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

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    fetchHistoriqueFromServer(); // Charger l'historique au démarrage
});