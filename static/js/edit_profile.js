function submitProfileForm() {
    const form = document.getElementById('editProfileForm');
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch('/editer_profil', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Profil mis à jour.") {
            alert('Profil mis à jour avec succès!');
        } else {
            alert('Erreur lors de la mise à jour du profil');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Erreur lors de la mise à jour du profil');
    });
}