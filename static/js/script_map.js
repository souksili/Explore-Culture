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

        fetch('/api/user_role', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            userRole = data.est_admin; // Stocker le rôle de l'utilisateur
            if (userRole) {
                document.getElementById('addZoneButton').style.display = 'inline-block';
            }
        })
        .catch(error => {
            console.error('Erreur lors de la vérification du rôle de l\'utilisateur:', error);
        });

        // Récupérer et afficher les zones
        fetchZonesFromServer();

        // Vérifier les trajets et désactiver le bouton si nécessaire
        const startButton = document.getElementById('startButton');
        if (startButton) {
            startButton.disabled = true; // Désactiver le bouton par défaut
        }
    }
});

document.getElementById('addZoneButton').addEventListener('click', () => {
    const addZoneModal = document.getElementById('addZoneModal');
    addZoneModal.style.display = 'flex';
});

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

document.getElementById('closeAddZoneModal').addEventListener('click', () => {
    const addZoneModal = document.getElementById('addZoneModal');
    addZoneModal.style.display = 'none';
});

document.getElementById('closeAddCuisineModal').addEventListener('click', () => {
    const addCuisineModal = document.getElementById('addCuisineModal');
    addCuisineModal.style.display = 'none';
});

document.getElementById('closeAddHistoireModal').addEventListener('click', () => {
    const addHistoireModal = document.getElementById('addHistoireModal');
    addHistoireModal.style.display = 'none';
});

document.getElementById('closeAddPersonnaliteModal').addEventListener('click', () => {
    const addPersonnaliteModal = document.getElementById('addPersonnaliteModal');
    addPersonnaliteModal.style.display = 'none';
});

document.getElementById('closeAddMusiqueModal').addEventListener('click', () => {
    const addMusiqueModal = document.getElementById('addMusiqueModal');
    addMusiqueModal.style.display = 'none';
});

document.getElementById('size').addEventListener('input', (event) => {
    const sizeValue = document.getElementById('sizeValue');
    sizeValue.textContent = event.target.value;
});

document.getElementById('geolocationIcon').addEventListener('click', () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(getAddressFromCoordinates, handleLocationError);
    } else {
        alert('La géolocalisation n\'est pas supportée par ce navigateur.');
    }
});

document.getElementById('address').addEventListener('input', (event) => {
    const address = event.target.value;
    const addressError = document.getElementById('addressError');
    if (address) {
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
            .then(response => response.json())
            .then(data => {
                if (data.length > 0) {
                    addressError.textContent = '';
                } else {
                    addressError.textContent = 'Adresse non trouvée';
                }
            })
            .catch(error => {
                console.error('Erreur lors de la recherche de l\'adresse:', error);
                addressError.textContent = 'Erreur lors de la recherche de l\'adresse';
            });
    } else {
        addressError.textContent = '';
    }
});

document.getElementById('addZoneForm').addEventListener('submit', (event) => {
    event.preventDefault();
    const address = document.getElementById('address').value;
    const description = document.getElementById('description').value;
    const size = document.getElementById('size').value;
    const color = getRandomColor();
    const addressError = document.getElementById('addressError');

    if (addressError.textContent) {
        alert('Veuillez corriger l\'adresse avant de soumettre.');
        return;
    }

    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const { lat, lon } = data[0];
                const zoneData = {
                    nom: address,
                    description: description,
                    latitude: lat,
                    longitude: lon,
                    taille: size,
                    couleur: color
                };

                fetch('/api/zones', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                    },
                    body: JSON.stringify(zoneData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message === "Zone ajoutée.") {
                        const newZone = {
                            _leaflet_id: data.zone_id,
                            latitude: lat,
                            longitude: lon,
                            taille: size,
                            couleur: color,
                            nom: address,
                            description: description
                        };
                        addZoneToMap(newZone.latitude, newZone.longitude, newZone.taille, newZone.couleur, newZone.nom, newZone.description, newZone._leaflet_id);
                        zones.push(newZone);
                        const addZoneModal = document.getElementById('addZoneModal');
                        addZoneModal.style.display = 'none';
                    } else {
                        alert('Erreur lors de l\'ajout de la zone');
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de l\'ajout de la zone:', error);
                });
            } else {
                alert('Adresse non trouvée');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la recherche de l\'adresse:', error);
        });
});

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function addZoneToMap(lat, lon, size, color, title, description, zoneId) {
    const zone = L.circle([lat, lon], {
        color: color,
        fillColor: color,
        fillOpacity: 0.5,
        radius: size
    }).addTo(map).bindPopup(`<b>${title}</b><br>${description}`);

    // Ajouter une icône ou un signe "+" au centre de la zone uniquement pour les administrateurs
    if (userRole) {
        const icon = L.divIcon({
            className: 'zone-icon',
            html: '<div style="font-size: 24px; color: white;">+</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        const marker = L.marker([lat, lon], { icon: icon }).addTo(map);
        marker.zoneId = zoneId; // Stocker l'ID de la zone dans un attribut du marqueur

        marker.on('click', () => {
            const selectTypeModal = document.getElementById('selectTypeModal');
            selectTypeModal.style.display = 'flex';
            document.getElementById('confirmTypeButton').setAttribute('data-zone-id', marker.zoneId);
        });
    }
}

document.getElementById('closeSelectTypeModal').addEventListener('click', () => {
    const selectTypeModal = document.getElementById('selectTypeModal');
    selectTypeModal.style.display = 'none';
});

document.getElementById('confirmTypeButton').addEventListener('click', () => {
    const typePatrimoine = document.getElementById('typePatrimoineSelect').value;
    const zoneId = document.getElementById('confirmTypeButton').getAttribute('data-zone-id');
    const selectTypeModal = document.getElementById('selectTypeModal');
    selectTypeModal.style.display = 'none';

    const modalId = `add${typePatrimoine.charAt(0).toUpperCase() + typePatrimoine.slice(1)}Modal`;
    const addPatrimoineModal = document.getElementById(modalId);
    if (addPatrimoineModal) {
        addPatrimoineModal.style.display = 'flex';
        document.getElementById(`add${typePatrimoine.charAt(0).toUpperCase() + typePatrimoine.slice(1)}Form`).setAttribute('data-zone-id', zoneId);
    } else {
        alert('Type de patrimoine non reconnu.');
    }
});

function getAddressFromCoordinates(position) {
    const { latitude, longitude } = position.coords;
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
        .then(response => response.json())
        .then(data => {
            if (data.display_name) {
                const addressInput = document.getElementById('address');
                addressInput.value = data.display_name;
            } else {
                alert('Adresse non trouvée');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la récupération de l\'adresse:', error);
        });
}

function handleLocationError(error) {
    switch (error.code) {
        case error.PERMISSION_DENIED:
            alert('Vous avez refusé la demande de géolocalisation.');
            break;
        case error.POSITION_UNAVAILABLE:
            alert('L\'information de géolocalisation n\'est pas disponible.');
            break;
        case error.TIMEOUT:
            alert('La demande de géolocalisation a expiré.');
            break;
        case error.UNKNOWN_ERROR:
            alert('Une erreur inconnue s\'est produite.');
            break;
    }
}

// Initialisation de la carte
const map = L.map('map').setView([31.7917, -7.0926], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Ajouter du CSS pour styliser l'icône
const style = document.createElement('style');
style.innerHTML = `
    .zone-icon div {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 50%;
        cursor: pointer;
    }
`;
document.head.appendChild(style);

let routeControl;
let zones = [];
let visitedZones = new Set(); // Tableau pour suivre les zones visitées
let currentIndex = 0;
let interval;
let routeCoordinates = [];
let animatedMarker;
let isPaused = false; // Variable pour suivre si l'animation est en pause

// Gestion des waypoints et de la navigation
function initializeWaypoints(addresses) {
    // Supprimer les itinéraires précédents
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

    animatedMarker = L.marker([0, 0], { icon: L.divIcon({ className: 'emoji-marker', html: '🚗' }) }).addTo(map);
    const pauseResumeButton = document.getElementById('pauseResumeButton');
    const toggleInstructions = document.getElementById('toggleInstructions');

    let instructionsVisible = true;

    routeControl.on('routesfound', ({ routes }) => {
        routeCoordinates = routes[0].coordinates;
        const startButton = document.getElementById('startButton');
        startButton.disabled = routeCoordinates.length === 0; // Désactiver le bouton si aucun trajet n'est trouvé

        startButton.addEventListener('click', () => {
            currentIndex = 0;
            isPaused = false; // Réinitialiser la variable de pause
            if (interval) clearInterval(interval); // Arrêter l'intervalle précédent
            interval = setInterval(() => {
                if (!isPaused && currentIndex < routeCoordinates.length) {
                    animatedMarker.setLatLng(routeCoordinates[currentIndex]);
                    const zone = isInsideZone(routeCoordinates[currentIndex], zones);
                    if (zone && !visitedZones.has(zone.nom)) {
                        isPaused = true; // Mettre en pause l'animation
                        clearInterval(interval);
                        showPauseModal(zone, routeCoordinates, currentIndex);
                        visitedZones.add(zone.nom); // Ajouter la zone aux zones visitées
                    }
                    currentIndex++;
                } else if (currentIndex >= routeCoordinates.length) {
                    clearInterval(interval);
                    showEndTripModal();
                }
            }, 50);
            startButton.style.display = 'none';
            pauseResumeButton.style.display = 'inline-block';
        });

        pauseResumeButton.addEventListener('click', () => {
            if (isPaused) {
                // Reprendre l'animation
                isPaused = false;
                pauseResumeButton.innerHTML = '<i class="fas fa-pause-circle"></i> Pause';
                interval = setInterval(() => {
                    if (!isPaused && currentIndex < routeCoordinates.length) {
                        animatedMarker.setLatLng(routeCoordinates[currentIndex]);
                        const zone = isInsideZone(routeCoordinates[currentIndex], zones);
                        if (zone && !visitedZones.has(zone.nom)) {
                            isPaused = true; // Mettre en pause l'animation
                            clearInterval(interval);
                            showPauseModal(zone, routeCoordinates, currentIndex);
                            visitedZones.add(zone.nom); // Ajouter la zone aux zones visitées
                        }
                        currentIndex++;
                    } else if (currentIndex >= routeCoordinates.length) {
                        clearInterval(interval);
                        showEndTripModal();
                    }
                }, 50);
            } else {
                // Mettre en pause l'animation
                isPaused = true;
                pauseResumeButton.innerHTML = '<i class="fas fa-play-circle"></i> Reprendre';
                clearInterval(interval);
            }
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

// Ajouter l'événement pour le bouton "Découvrir"
document.getElementById('discoverButton').addEventListener('click', () => {
    const zoneId = document.getElementById('discoverButton').getAttribute('data-zone-id');
    console.log('Zone ID:', zoneId);

    if (zoneId) {
        localStorage.setItem('zoneId', zoneId);
    }

    if (zoneId) {
        const iframe = document.createElement('iframe');
        iframe.src = `discover?zoneId=${zoneId}`;
        iframe.style.width = '100%';
        iframe.style.height = '500px';
        iframe.style.border = 'none';

        const modalContent = document.getElementById('pauseModal').querySelector('.modal-content');
        if (modalContent) {
            // Nettoyer le contenu précédent
            modalContent.innerHTML = '';

            // Ajouter l'iframe au contenu du modal
            modalContent.appendChild(iframe);

            // Masquer les boutons inutiles
            const continueButton = document.getElementById('continueButton');
            const discoverButton = document.getElementById('discoverButton');
            if (continueButton) continueButton.style.display = 'none';
            if (discoverButton) discoverButton.style.display = 'none';

            // Masquer le titre et le message
            const zoneDetectedTitle = document.getElementById('zoneDetectedTitle');
            const zoneDetectedMessage = document.getElementById('zoneDetectedMessage');
            if (zoneDetectedTitle) zoneDetectedTitle.style.display = 'none';
            if (zoneDetectedMessage) zoneDetectedMessage.style.display = 'none';

            // Ajouter un gestionnaire d'événements pour le bouton de fermeture existant
            const closeButton = document.getElementById('closePauseModal');
            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    const modal = document.getElementById('pauseModal');
                    if (modal) {
                        modal.style.display = 'none';
                    }
                });
            }

            // Ajouter un bouton de fermeture à l'iframe
            const closeIframeButton = document.createElement('button');
            closeIframeButton.textContent = 'Fermer';
            closeIframeButton.style.position = 'absolute';
            closeIframeButton.style.top = '10px';
            closeIframeButton.style.right = '10px';
            closeIframeButton.style.zIndex = '1000';
            closeIframeButton.style.backgroundColor = 'red';
            closeIframeButton.style.color = 'white';
            closeIframeButton.style.border = 'none';
            closeIframeButton.style.padding = '5px 10px';
            closeIframeButton.style.cursor = 'pointer';

            // Ajouter le bouton de fermeture à l'iframe
            modalContent.appendChild(closeIframeButton);

            // Ajouter un gestionnaire d'événements pour le bouton de fermeture
            closeIframeButton.addEventListener('click', () => {
                const modal = document.getElementById('pauseModal');
                if (modal) {
                    modal.style.display = 'none';
                }
            });
        } else {
            console.error('Element with class "modal-content" not found.');
        }
    } else {
        console.error('Zone ID is undefined');
    }
});

// Modal de pause
function showPauseModal(zone, routeCoordinates, currentIndex) {
    const pauseModal = document.getElementById('pauseModal');
    if (pauseModal) {
        pauseModal.style.display = 'flex';

        document.getElementById('closePauseModal').addEventListener('click', () => {
            pauseModal.style.display = 'none';
        });

        document.getElementById('continueButton').addEventListener('click', () => {
            pauseModal.style.display = 'none';
            // Reprendre l'animation de la voiture à partir de l'endroit où elle s'est arrêtée
            isPaused = false; // Réinitialiser la variable de pause
            if (interval) clearInterval(interval); // Arrêter l'intervalle précédent
            interval = setInterval(() => {
                if (!isPaused && currentIndex < routeCoordinates.length) {
                    animatedMarker.setLatLng(routeCoordinates[currentIndex]);
                    const zone = isInsideZone(routeCoordinates[currentIndex], zones);
                    if (zone && !visitedZones.has(zone.nom)) {
                        isPaused = true; // Mettre en pause l'animation
                        clearInterval(interval);
                        showPauseModal(zone, routeCoordinates, currentIndex);
                        visitedZones.add(zone.nom); // Ajouter la zone aux zones visitées
                    }
                    currentIndex++;
                } else if (currentIndex >= routeCoordinates.length) {
                    clearInterval(interval);
                    showEndTripModal();
                }
            }, 50);
            // Mettre à jour le bouton de pause/reprise
            const pauseResumeButton = document.getElementById('pauseResumeButton');
            pauseResumeButton.innerHTML = '<i class="fas fa-pause-circle"></i> Pause';
        }, { once: true }); // Assurez-vous que l'événement ne soit ajouté qu'une seule fois

        // Ajouter l'ID de la zone au bouton "Découvrir"
        const discoverButton = document.getElementById('discoverButton');
        discoverButton.setAttribute('data-zone-id', zone.id);
    } else {
        console.error('Element with id "pauseModal" not found.');
    }
}

// Vérifier si la voiture est dans une zone
function isInsideZone(latLng, zones) {
    for (const zone of zones) {
        const distance = L.latLng(latLng).distanceTo(L.latLng(zone.latitude, zone.longitude));
        if (distance <= zone.taille) {
            return zone;
        }
    }
    return null;
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

        // Regrouper les adresses par group_id
        const groupedHistorique = historique.reduce((acc, address) => {
            if (!acc[address.group_id]) {
                acc[address.group_id] = [];
            }
            acc[address.group_id].push(address);
            return acc;
        }, {});

        // Créer des liens cliquables pour chaque groupe d'adresses
        for (const group_id in groupedHistorique) {
            const addresses = groupedHistorique[group_id];
            const listItem = document.createElement('li');
            const link = document.createElement('a');
            const dateAjout = new Date(addresses[0].date_ajout);
            const formattedDate = dateAjout.toLocaleDateString('fr-FR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            link.href = '#';
            link.textContent = `Itinéraire ajouté le ${formattedDate}`;
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
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        chatBox.innerHTML += `<p><b>Assistant :</b> ${data.response}</p>`;
        if (data.addresses && Array.isArray(data.addresses)) {
            saveHistoriqueToServer(data.addresses); // Sauvegarde dans la BDD
            initializeWaypoints(data.addresses); // Initialise l'itinéraire sur la carte
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        console.error('Erreur lors de l\'envoi du message :', error);
        chatBox.innerHTML += `<p><b>Assistant :</b> Une erreur est survenue.</p>`;
    });
}

// Fonction pour récupérer les zones depuis le serveur
function fetchZonesFromServer() {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        console.error('Access token is missing');
        return;
    }

    fetch('/api/zones', {
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
    .then(data => {
        zones = data;
        if (!Array.isArray(zones)) {
            throw new TypeError('Le format de la réponse est incorrect.');
        }

        // Supprimer les zones précédentes de la carte
        map.eachLayer(layer => {
            if (layer instanceof L.Circle) {
                map.removeLayer(layer);
            }
        });

        // Ajouter les nouvelles zones à la carte
        zones.forEach(zone => {
            addZoneToMap(zone.latitude, zone.longitude, zone.taille, zone.couleur, zone.nom, zone.description, zone.id);
        });
    })
    .catch(error => {
        console.error('Erreur lors de la récupération des zones :', error);
    });
}

// Initialisation
fetchHistoriqueFromServer();

// Gestion des formulaires d'ajout de patrimoine culturel
document.getElementById('addCuisineForm').addEventListener('submit', (event) => {
    event.preventDefault();
    const zoneId = document.getElementById('addCuisineForm').getAttribute('data-zone-id');
    const recette = document.getElementById('recette').value;
    const ingredients = document.getElementById('ingredients').value;
    const tempsPreparation = document.getElementById('tempsPreparation').value;

    const patrimoineData = {
        type_patrimoine: 'cuisine',
        recette: recette,
        ingredients: ingredients,
        temps_preparation: tempsPreparation
    };

    fetch(`/api/zones/${zoneId}/patrimoines`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(patrimoineData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Patrimoine culturel ajouté.") {
            alert('Patrimoine culturel ajouté avec succès');
            const addCuisineModal = document.getElementById('addCuisineModal');
            addCuisineModal.style.display = 'none';
        } else {
            alert('Erreur lors de l\'ajout du patrimoine culturel');
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout du patrimoine culturel:', error);
    });
});

document.getElementById('addHistoireForm').addEventListener('submit', (event) => {
    event.preventDefault();
    const zoneId = document.getElementById('addHistoireForm').getAttribute('data-zone-id');
    const evenement = document.getElementById('evenement').value;
    const dateEvenement = document.getElementById('dateEvenement').value;
    const personnagesCles = document.getElementById('personnagesCles').value;

    const patrimoineData = {
        type_patrimoine: 'histoire',
        evenement: evenement,
        date_evenement: dateEvenement,
        personnages_cles: personnagesCles
    };

    fetch(`/api/zones/${zoneId}/patrimoines`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(patrimoineData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Patrimoine culturel ajouté.") {
            alert('Patrimoine culturel ajouté avec succès');
            const addHistoireModal = document.getElementById('addHistoireModal');
            addHistoireModal.style.display = 'none';
        } else {
            alert('Erreur lors de l\'ajout du patrimoine culturel');
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout du patrimoine culturel:', error);
    });
});

document.getElementById('addPersonnaliteForm').addEventListener('submit', (event) => {
    event.preventDefault();
    const zoneId = document.getElementById('addPersonnaliteForm').getAttribute('data-zone-id');
    const nomPersonnalite = document.getElementById('nomPersonnalite').value;
    const biographie = document.getElementById('biographie').value;
    const contributions = document.getElementById('contributions').value;

    const patrimoineData = {
        type_patrimoine: 'personnalité',
        nom_personnalite: nomPersonnalite,
        biographie: biographie,
        contributions: contributions
    };

    fetch(`/api/zones/${zoneId}/patrimoines`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(patrimoineData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Patrimoine culturel ajouté.") {
            alert('Patrimoine culturel ajouté avec succès');
            const addPersonnaliteModal = document.getElementById('addPersonnaliteModal');
            addPersonnaliteModal.style.display = 'none';
        } else {
            alert('Erreur lors de l\'ajout du patrimoine culturel');
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout du patrimoine culturel:', error);
    });
});

document.getElementById('addMusiqueForm').addEventListener('submit', (event) => {
    event.preventDefault();
    const zoneId = document.getElementById('addMusiqueForm').getAttribute('data-zone-id');
    const titreMusique = document.getElementById('titreMusique').value;
    const artiste = document.getElementById('artiste').value;
    const genre = document.getElementById('genre').value;
    const lienMusique = document.getElementById('lienMusique').value;

    const patrimoineData = {
        type_patrimoine: 'musique',
        titre_musique: titreMusique,
        artiste: artiste,
        genre: genre,
        lien_musique: lienMusique
    };

    fetch(`/api/zones/${zoneId}/patrimoines`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(patrimoineData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Patrimoine culturel ajouté.") {
            alert('Patrimoine culturel ajouté avec succès');
            const addMusiqueModal = document.getElementById('addMusiqueModal');
            addMusiqueModal.style.display = 'none';
        } else {
            alert('Erreur lors de l\'ajout du patrimoine culturel');
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout du patrimoine culturel:', error);
    });
});

// Gestion de l'affichage des champs spécifiques en fonction du type de patrimoine
document.getElementById('typePatrimoine').addEventListener('change', (event) => {
    const typePatrimoine = event.target.value;
    document.getElementById('cuisineFields').style.display = 'none';
    document.getElementById('histoireFields').style.display = 'none';
    document.getElementById('personnaliteFields').style.display = 'none';
    document.getElementById('musiqueFields').style.display = 'none';

    if (typePatrimoine === "cuisine") {
        document.getElementById('cuisineFields').style.display = 'block';
    } else if (typePatrimoine === "histoire") {
        document.getElementById('histoireFields').style.display = 'block';
    } else if (typePatrimoine === "personnalité") {
        document.getElementById('personnaliteFields').style.display = 'block';
    } else if (typePatrimoine === "musique") {
        document.getElementById('musiqueFields').style.display = 'block';
    }
});