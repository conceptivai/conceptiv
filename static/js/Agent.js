document.addEventListener("DOMContentLoaded", () => {
  const agentCards = document.querySelectorAll(
    ".agent-card input[type='radio']"
  );
  const fields = [
    "name",
    "persona",
    "purpose",
    "attitude",
    "uniquetraits",
    "limitations",
    "agent-profile-picture",
    "agent-profile-name",
    "agent-profile-description",
    "agent-profile-reviews",
  ];
  const savedcustompropt = "customPromptKey";

  const agentData = {
    Josephine: {
      name: "Josephine",
      persona: "Expert Healthcare Advisor",
      purpose: "Health Guidance",
      attitude: "Empathetic",
      uniquetraits: "Warm, Friendly",
      limitations: "Be Polite",
      "agent-profile-picture": "static/Assets/Josephine DP.png",
      "agent-profile-name": "Josephine",
      "agent-profile-description":
        "An expert healthcare advisor here to help you!",
      "agent-profile-reviews":
        "⭐ Excellent service!,⭐ Very professional,⭐ Highly recommended.",
    },
    Jasmine: {
      name: "Jasmine",
      persona: "Tech Support Specialist",
      purpose: "Tech Support",
      attitude: "Professional",
      uniquetraits: "Detail-oriented",
      limitations: "Be Polite",
      "agent-profile-picture": "static/Assets/Jasmine DP.png",
      "agent-profile-name": "Jasmine",
      "agent-profile-description": "Solving your tech needs always",
      "agent-profile-reviews":
        "⭐ Excellent service!,⭐ Very professional,⭐ Highly recommended.",
    },
    Tony: {
      name: "Tony",
      persona: "Marketing Expert",
      purpose: "Business Growth",
      attitude: "Charismatic",
      uniquetraits: "Strategic Thinker",
      limitations: "Be Polite",
      "agent-profile-picture": "static/Assets/Tony DP.png",
      "agent-profile-name": "Tony",
      "agent-profile-description": "Your own expert business guru",
      "agent-profile-reviews":
        "⭐ Excellent service!,⭐ Very professional,⭐ Highly recommended.",
    },
    agent4: {
      name: "Agent 4",
      persona: "",
      purpose: "",
      attitude: "",
      uniquetraits: "coming soon",
    },
    agent5: {
      name: "Agent 5",
      persona: "",
      purpose: "",
      attitude: "",
      uniquetraits: "coming soon",
    },
  };

  // const updateChatboxTitle = () => {
  //     const botName = localStorage.getItem("customPromptName") || "Bot";
  //     document.getElementById("chat-title").textContent = botName;
  // };

  // Populate saved fields from localStorage on page load
  fields.forEach((field) => {
    const input = document.getElementById(field);
    input.value = localStorage.getItem(field) || "";
    input.addEventListener("input", () => {
      localStorage.setItem(field, input.value);

      // Update bot name dynamically if the "name" field changes
      if (field === "name") {
        localStorage.setItem("customPromptName", input.value || "Bot");
        // updateChatboxTitle();
      }
    });
  });

  // Update fields and store selected bot name when an agent is selected
  agentCards.forEach((card) => {
    card.addEventListener("change", () => {
      const selectedAgent = card.value;
      const data = agentData[selectedAgent] || {};

      // Save the bot name for use in the chat interface
      localStorage.setItem("customPromptName", data.name || "Bot");
      // updateChatboxTitle();

      fields.forEach((field) => {
        const input = document.getElementById(field);
        input.value = data[field] || "";
        localStorage.setItem(field, data[field] || "");
      });
    });
  });

  document.querySelectorAll('input[type="radio"]').forEach((radio) => {
    radio.addEventListener("click", () => {
      const button = document.querySelector(".save-button");
      button.scrollIntoView({
        behavior: "smooth", // Smooth scrolling effect
        block: "center", // Align the button to the center of the viewport
      });
    });
  });

  // Submit handler
  document
    .getElementById("agent-selection-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const userId = localStorage.getItem("user_id");
      if (!userId) {
        alert("User not logged in. Please log in again.");
        window.location.href = "/";
        return;
      }

      const profilePicture =
        document.getElementById("agent-profile-picture").value ||
        "https://via.placeholder.com/150";
      const profileName =
        document.getElementById("agent-profile-name").value ||
        localStorage.getItem("name") ||
        "Agent Name";
      const profileDescription =
        document.getElementById("agent-profile-description").value ||
        localStorage.getItem("persona") ||
        "Title";
      const profileReviewsInput =
        document.getElementById("agent-profile-reviews").value ||
        "Excellent service!,Very professional.,Highly recommended.";
      const profileReviews = profileReviewsInput
        .split(",")
        .map((review) => review.trim());

      // Save to localStorage
      localStorage.setItem("profilePicture", profilePicture);
      localStorage.setItem("profileTitle", profileName);
      localStorage.setItem("profileDescription", profileDescription);
      localStorage.setItem("customerReviews", JSON.stringify(profileReviews));

      // // Create a custom prompt string for submission
      // const customPrompt = fields
      //     .map(field => {
      //         const value = document.getElementById(field).value;
      //         return value ? `Your ${field} is ${value}.` : null;
      //     })
      //     .filter(Boolean) // Remove null or undefined values
      //     .join(" ");

      // Create a custom prompt string for submission
      const customPrompt = fields
        .slice(0, 6) // Take only the first 6 fields
        .map((field) => {
          const value = document.getElementById(field).value;
          return value ? `Your ${field} is ${value}.` : null;
        })
        .filter(Boolean) // Remove null or undefined values
        .join(" ");

      if (!customPrompt) {
        alert("Please fill at least one field to create a custom prompt.");
        return;
      }

      const prevsavedcustompropt =
        localStorage.getItem(savedcustompropt) || null;
      const payload = {
        user_id: userId,
        localprompt: prevsavedcustompropt,
        customprompt: customPrompt,
      };

      try {
        const response = await fetch("/prompt", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          alert("Prompt updated successfully!");
          localStorage.setItem(savedcustompropt, customPrompt);
          window.location.href = "/home";
        } else {
          const errorData = await response.json();
          alert("Error: " + errorData.error);
        }
      } catch (error) {
        console.error("Error:", error);
        alert("Failed to update the prompt.");
      }
    });
});
