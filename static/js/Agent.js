document.addEventListener("DOMContentLoaded", () => {
    const agentCards = document.querySelectorAll(".agent-card input[type='radio']");
    const customPromptContainer = document.getElementById("custom-prompt-container");
    const customPromptInput = document.getElementById("custom-prompt");
    const form = document.getElementById("agent-selection-form");

  

    // Show custom prompt input when a card is selected
    agentCards.forEach((card) => {
        card.addEventListener("input", () => {
            customPromptContainer.classList.remove("hidden");
            try {
                customPromptInput.value = localStorage.getItem(savedcustompropt)||null;
            } catch (error) {
                // Code that runs if an error occurs
                localStorage.setItem(savedcustompropt,"");
                console.error("An error occurred:", error.message);
            } finally {
                // Code that runs no matter what (optional)
                console.log("This will always run.");
            }
            
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
        const prevsavedcustompropt = localStorage.getItem(savedcustompropt) || null;
        const payload = {
            modelname: selectedAgent.value,
            localprompt: prevsavedcustompropt,
            customprompt: customPrompt,
            user_id: userId
        };

        try {
            // Send POST request to the Flask backend
            const response = await fetch("https://conceptiv.onrender.com/prompt", {
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
                localStorage.setItem(savedcustompropt,customPrompt);
                window.location.href = "/home";
                
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
