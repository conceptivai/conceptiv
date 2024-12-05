document.addEventListener("DOMContentLoaded", () => {
    const agentCards = document.querySelectorAll(".agent-card input[type='radio']");
    const customPromptContainer = document.getElementById("custom-prompt-container");
    const customPromptInput = document.getElementById("custom-prompt");
    const form = document.getElementById("agent-selection-form");

    // Show custom prompt input when a card is selected
    agentCards.forEach((card) => {
        card.addEventListener("input", () => {
            customPromptContainer.classList.remove("hidden");
            customPromptInput.value = localStorage.getItem(savedcustompropt);
        });
    });    

    // Handle form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Get selected agent and custom prompt value
        const selectedAgent = document.querySelector(".agent-card input[type='radio']:checked");
        const customPrompt = customPromptInput.value;

        if (!selectedAgent) {
            alert("Please select an agent.");
            return;
        }

        const userId = localStorage.getItem("user_id");
        if (!userId) {
            alert("User not logged in. Please log in again.");
            window.location.href = "login.html"; // Redirect to login if user_id is missing
            return;
        }
        // Prepare the JSON payload
        const payload = {
            modelname: selectedAgent.value,
            // customprompt: customPrompt || null,
            customprompt: customPrompt,
            user_id: userId
        };

        try {
            // Send POST request to the Flask backend
            const response = await fetch("http://127.0.0.1:8000/prompt", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                alert("Prompt updated successfully: " + data.message);
                // Redirect to index.html
                window.location.href = "index.html";
            } else {
                const errorData = await response.json();
                alert("Error: " + errorData.error);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to update the prompt. Please try again.");
        }
    });
});
