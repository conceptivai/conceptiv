document.addEventListener("DOMContentLoaded", () => {
    const loginRadio = document.getElementById("login-radio");
    const signupRadio = document.getElementById("signup-radio");
    const authTitle = document.getElementById("auth-title");
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");

    // Toggle between Login and Signup forms
    loginRadio.addEventListener("change", () => {
        if (loginRadio.checked) {
            authTitle.textContent = "Login to Your Account";
            loginForm.classList.remove("hidden");
            signupForm.classList.add("hidden");
        }
    });

    signupRadio.addEventListener("change", () => {
        if (signupRadio.checked) {
            authTitle.textContent = "Signup for an Account";
            signupForm.classList.remove("hidden");
            loginForm.classList.add("hidden");
        }
    });

    // Handle Login OTP Request
    document.getElementById("get-otp").addEventListener("click", () => {
        const email = document.getElementById("login-email").value;
        if (email) {
            alert(`OTP sent to ${email} (placeholder).`);
            // Add backend logic to send OTP.
        } else {
            alert("Please enter your email.");
        }
    });

    // Handle Signup OTP Request
    document.getElementById("get-signup-otp").addEventListener("click", () => {
        const email = document.getElementById("signup-email").value;
        if (email) {
            alert(`Signup OTP sent to ${email} (placeholder).`);
            // Add backend logic to send OTP.
        } else {
            alert("Please enter your email.");
        }
    });
});
