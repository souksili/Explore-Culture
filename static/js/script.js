document.addEventListener("DOMContentLoaded", function () {
    const page = document.body.getAttribute("data-page");

    if (page === "connexion") {
        setupConnexionPage();
    }

    if (page === "inscription") {
        setupInscriptionPage();
    }

    setupRealTimeValidation();
});

function getApiBaseUrl() {
    if (window.location.hostname === "localhost") {
        return "http://localhost:5000";
    } else {
        return window.location.origin;
    }
}

function setupRealTimeValidation() {
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(emailField => {
        emailField.addEventListener('input', function () {
            validateEmailInput(emailField.id, emailField.dataset.messageId || emailField.id + "-message");
        });
    });

    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(passwordField => {
        passwordField.addEventListener('input', function () {
            validatePasswordInput(passwordField.id, passwordField.dataset.messageId || passwordField.id + "-message");
        });
    });
}

function setupConnexionPage() {
    const modal = document.getElementById("recovery-modal");
    if (modal) {
        modal.style.display = "none";
    }

    const forgotPasswordLink = document.getElementById("forgot-password");
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener("click", function (e) {
            e.preventDefault();
            if (modal) {
                modal.style.display = "flex";
            }
        });
    }

    if (modal) {
        window.addEventListener("click", function (event) {
            if (event.target === modal) {
                closeModal();
            }
        });
    }

    console.log("Page de connexion chargée.");
}

function closeModal() {
    const modal = document.getElementById("recovery-modal");
    if (modal) {
        modal.style.display = "none";
    }
}

async function login() {
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value.trim();
    const messageElement = document.getElementById("login-message");

    if (!validateEmailInput("login-email", "login-email-message") || !validatePasswordInput("login-password", "login-password-message")) {
        return;
    }

    try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/connexion`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, mot_de_passe: password })
        });

        const data = await response.json();
        if (response.ok) {
            messageElement.textContent = "Connexion réussie !";
            messageElement.style.color = "green";
            localStorage.setItem("accessToken", data.access_token);
            setTimeout(() => window.location.href = "dashboard.html", 1000);
        } else {
            messageElement.textContent = data.message || "Erreur de connexion.";
            messageElement.style.color = "red";
        }
    } catch (error) {
        console.error("Erreur lors de la connexion:", error);
        messageElement.textContent = "Erreur lors de la connexion. Veuillez réessayer.";
        messageElement.style.color = "red";
    }
}

function setupInscriptionPage() {
    console.log("Page d'inscription chargée.");
}

async function register() {
    const username = document.getElementById("register-username").value.trim();
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value.trim();
    const messageElement = document.getElementById("register-message");

    if (!username || !validateEmailInput("register-email", "register-email-message") || !validatePasswordInput("register-password", "register-password-message")) {
        return;
    }

    try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/inscription`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, mot_de_passe: password, nom_utilisateur: username })
        });

        const data = await response.json();
        if (response.ok) {
            messageElement.textContent = "Inscription réussie ! Veuillez vérifier votre email.";
            messageElement.style.color = "green";
            setTimeout(() => window.location.href = "connexion.html", 2000);
        } else {
            messageElement.textContent = data.message || "Erreur lors de l'inscription.";
            messageElement.style.color = "red";
        }
    } catch (error) {
        console.error("Erreur lors de l'inscription:", error);
        messageElement.textContent = "Erreur lors de l'inscription. Veuillez réessayer.";
        messageElement.style.color = "red";
    }
}

function validateEmailInput(inputId, messageId) {
    const email = document.getElementById(inputId).value.trim();
    const messageElement = document.getElementById(messageId);
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (emailRegex.test(email)) {
        messageElement.textContent = "Email valide.";
        messageElement.style.color = "green";
        messageElement.classList.add("show");
        return true;
    } else {
        messageElement.textContent = "Veuillez entrer un email valide.";
        messageElement.style.color = "red";
        messageElement.classList.add("show");
        return false;
    }
}

function validatePasswordInput(inputId, messageId) {
    const password = document.getElementById(inputId).value.trim();
    const messageElement = document.getElementById(messageId);

    if (password.length >= 6) {
        messageElement.textContent = "Mot de passe valide.";
        messageElement.style.color = "green";
        messageElement.classList.add("show");
        return true;
    } else {
        messageElement.textContent = "Le mot de passe doit contenir au moins 6 caractères.";
        messageElement.style.color = "red";
        messageElement.classList.add("show");
        return false;
    }
}