document.addEventListener('DOMContentLoaded', () => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        window.location.href = '/connexion';
    } else {
        fetch('/dashboard', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/connexion';
            }
            return response.json();
        })
        .then(() => {
            const jwt = get_jwt();
            if (jwt.sub.est_admin) {
                document.getElementById('addZoneButton').style.display = 'inline-block';
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            window.location.href = '/connexion';
        });
    }
});

function get_jwt() {
    const token = localStorage.getItem('accessToken');
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
}

document.getElementById('burgerIcon').addEventListener('click', () => {
    const menuContent = document.getElementById('menuContent');
    menuContent.style.display = menuContent.style.display === 'flex' ? 'none' : 'flex';
});

document.getElementById('historiqueButton').addEventListener('click', () => {
    const historiqueModal = document.getElementById('historiqueModal');
    historiqueModal.style.display = 'flex';
    fetchHistoriqueFromServer();
});

document.getElementById('closeHistoriqueModal').addEventListener('click', () => {
    const historiqueModal = document.getElementById('historiqueModal');
    historiqueModal.style.display = 'none';
});

document.getElementById('closeConfirmDeleteModal').addEventListener('click', () => {
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    confirmDeleteModal.style.display = 'none';
});

document.getElementById('cancelDeleteButton').addEventListener('click', () => {
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    confirmDeleteModal.style.display = 'none';
});

document.getElementById('confirmDeleteButton').addEventListener('click', () => {
    const groupId = document.getElementById('confirmDeleteButton').getAttribute('data-group-id');
    deleteItinerary(groupId);
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    confirmDeleteModal.style.display = 'none';
});

const map = L.map('map').setView([31.7917, -7.0926], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let routeControl;

function initializeWaypoints(addresses) {
    if (routeControl) {
        map.removeControl(routeControl);
        map.eachLayer(layer => {
            if (layer instanceof L.Marker || layer instanceof L.Routing.Line) {
                map.removeLayer(layer);
            }
        });
    }

    const waypoints = addresses.map(({ latitude, longitude, nom, description }, index) => {
        const emoji = index === 0 ? '🏁' : index === addresses.length - 1 ? '🏁' : '📍';
        L.marker([latitude, longitude], { icon: L.divIcon({ className: 'emoji-marker', html: emoji }) })
            .addTo(map)
            .bindPopup(`<b>${nom}</b><br>${description || 'Aucune description'}`);
        return L.latLng(latitude, longitude);
    });

    routeControl = L.Routing.control({ waypoints, createMarker: () => null }).addTo(map);

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

        const groupedHistorique = historique.reduce((acc, address) => {
            if (!acc[address.group_id]) {
                acc[address.group_id] = [];
            }
            acc[address.group_id].push(address);
            return acc;
        }, {});

        for (const group_id in groupedHistorique) {
            const addresses = groupedHistorique[group_id];
            const listItem = document.createElement('li');
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = `Itinéraire ${group_id}`;
            link.addEventListener('click', (event) => {
                event.preventDefault();
                initializeWaypoints(addresses);
            });
            listItem.appendChild(link);

            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Supprimer';
            deleteButton.addEventListener('click', () => {
                showConfirmDeleteModal(group_id);
            });
            listItem.appendChild(deleteButton);

            historiqueList.appendChild(listItem);
        }
    })
    .catch(error => {
        console.error('Erreur lors de la récupération de l\'historique :', error);
        const historiqueList = document.getElementById('historiqueList');
        historiqueList.innerHTML = '<li>Erreur lors du chargement de l\'historique.</li>';
    });
}

function showConfirmDeleteModal(groupId) {
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    confirmDeleteModal.style.display = 'flex';
    document.getElementById('confirmDeleteButton').setAttribute('data-group-id', groupId);
}

function deleteItinerary(groupId) {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        console.error('Access token is missing');
        return;
    }

    fetch(`/api/historique/${groupId}`, {
        method: 'DELETE',
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
    .then(() => {
        fetchHistoriqueFromServer();
    })
    .catch(error => {
        console.error('Erreur lors de la suppression de l\'itinéraire :', error);
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
    .then(() => fetchHistoriqueFromServer())
    .catch(console.error);
}

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
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        chatBox.innerHTML += `<p><b>Assistant :</b> ${data.response}</p>`;
        if (data.addresses && Array.isArray(data.addresses)) {
            saveHistoriqueToServer(data.addresses);
            initializeWaypoints(data.addresses);
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        console.error('Erreur lors de l\'envoi du message :', error);
        chatBox.innerHTML += `<p><b>Assistant :</b> Une erreur est survenue.</p>`;
    });
}

fetchHistoriqueFromServer();