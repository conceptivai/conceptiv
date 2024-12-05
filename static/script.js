document.addEventListener("DOMContentLoaded", () => {
  // Select DOM elements based on the existing HTML
  const userInput = document.getElementById("user-input");
  const chatMessages = document.getElementById("messages");
  const sendButton = document.getElementById("send-btn");
  const countdownElement = document.getElementById("countdown");
  const modal = document.getElementById("premium-modal");
  const buyPremiumBtn = document.getElementById("buy-premium-btn");

  // // Validate that elements exist in the DOM
  // if (!userInput || !chatMessages || !sendButton) {
  //     console.error("Required elements are missing in the DOM. Check your HTML structure.");
  //     return;
  // }

  const FREE_USAGE_DURATION = 10 * 60 * 1000 // 15 minutes in milliseconds
  const TIMER_KEY = "chat_start_time";

  let countdownInterval = null;

  // Initialize Timer
  function initializeTimer() {
    const now = Date.now();
    let startTime = localStorage.getItem(TIMER_KEY);

    if (!startTime) {
      startTime = now;
      localStorage.setItem(TIMER_KEY, startTime);
    }

    const elapsed = now - startTime;
    const remainingTime = Math.max(FREE_USAGE_DURATION - elapsed, 0);

    if (remainingTime <= 0) {
      showPremiumModal();
    } else {
      startCountdown(remainingTime);
    }
  }

  // Start Countdown
  function startCountdown(remainingTime) {
    clearInterval(countdownInterval); // Clear any previous intervals
    countdownInterval = setInterval(() => {
      if (remainingTime <= 0) {
        clearInterval(countdownInterval);
        localStorage.removeItem(TIMER_KEY); // Reset timer
        showPremiumModal();
      } else {
        remainingTime -= 1000;
        updateCountdownDisplay(remainingTime);
      }
    }, 1000);
  }

  // Update Countdown Display
  function updateCountdownDisplay(remainingTime) {
    const minutes = Math.floor(remainingTime / 60000);
    const seconds = Math.floor((remainingTime % 60000) / 1000);
    countdownElement.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;
  }

  // Reset Timer and Hide Modal
  function resetTimer() {
    const now = Date.now();
    localStorage.setItem(TIMER_KEY, now); // Reset timer to the current time
    hidePremiumModal();
    startCountdown(FREE_USAGE_DURATION); // Restart countdown
    alert("Thank you for upgrading to Premium!");
  }

  // Show Premium Modal
  function showPremiumModal() {
    modal.style.display = "flex";
    document.body.style.overflow = "hidden"; // Prevent scrolling
  }

  // Hide Premium Modal
  function hidePremiumModal() {
    modal.style.display = "none";
    document.body.style.overflow = "auto"; // Restore scrolling
  }

  // Function to append messages to the chat container
 // Append Message
 function appendMessage(text, sender) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);

  if (sender === "bot") {
    const nameSpan = document.createElement("span");
    nameSpan.classList.add("name");
    nameSpan.textContent = "Sensia Bot";
    messageDiv.appendChild(nameSpan);
  }

  const bubbleDiv = document.createElement("div");
  bubbleDiv.classList.add("bubble");
  bubbleDiv.textContent = text;

  messageDiv.appendChild(bubbleDiv);
  chatMessages.appendChild(messageDiv);

  chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: "smooth",
  });
}

// Add Typing Indicator
function addTypingIndicator() {
  const typingDiv = document.createElement("div");
  typingDiv.classList.add("message", "bot", "typing-indicator");
  typingDiv.innerHTML = `
    <span class="name">Bot Name</span>
    <div class="bubble">
      <span class="dots"><span>.</span><span>.</span><span>.</span></span>
    </div>
  `;
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: "smooth",
  });
}

// Remove Typing Indicator
function removeTypingIndicator() {
  const typingDiv = document.querySelector(".typing-indicator");
  if (typingDiv) typingDiv.remove();
}

  // Function to fetch the initial bot message
  function fetchInitialMessage() {
      addTypingIndicator();

      fetch("http://127.0.0.1:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: "hi", user_id: localStorage.getItem("user_id") }),
      })
          .then((response) => {
              if (!response.ok) {
                  throw new Error(`Failed to fetch initial message. Status: ${response.status}`);
              }
              return response.json();
          })
          .then((data) => {
              removeTypingIndicator();
              appendMessage(data.reply, "bot");
          })
          .catch((error) => {
              console.error("Error fetching initial message:", error);
              removeTypingIndicator();
              appendMessage("Sorry, something went wrong. Please try again later.", "bot");
          });
  }

  // Function to send user messages to the bot
  function sendMessage() {
    const userText = userInput.value.trim();
    if (!userText) return; // Do nothing if the input is empty

    appendMessage(userText, "user");
    userInput.value = ""; // Clear the input field
    addTypingIndicator();

    fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, user_id: localStorage.getItem("user_id") }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch response. Status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            removeTypingIndicator();
            appendMessage(data.reply, "bot");
        })
        .catch((error) => {
            removeTypingIndicator();
            appendMessage("Sorry, something went wrong. Please try again later.", "bot");
        });
}

  // Event listeners
  sendButton.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
          sendMessage();
      }
  });

  buyPremiumBtn.addEventListener("click", resetTimer);

  // Fetch the initial bot message on page load
  fetchInitialMessage();
  initializeTimer();
});
