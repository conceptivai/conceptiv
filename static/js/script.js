document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("messages");
    const sendButton = document.getElementById("send-btn");
    const countdownElement = document.getElementById("countdown");
    const modal = document.getElementById("premium-modal");
    const buyPremiumBtn = document.getElementById("buy-premium-btn");
    const chatWindow = document.getElementById('chat-window');
  
    const FREE_USAGE_DURATION = 10 * 60 * 1000; // 10 minutes in milliseconds
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
  
    // Split long messages into chunks
    function splitMessage(message) {
        const MAX_LENGTH = 120; // Example threshold
        const sentences = message.split(/(?<=[.!?])\s+/);
        let chunks = [];
        let currentChunk = "";
  
        sentences.forEach((sentence) => {
            if (currentChunk.length + sentence.length <= MAX_LENGTH) {
                currentChunk += (currentChunk ? " " : "") + sentence;
            } else {
                chunks.push(currentChunk);
                currentChunk = sentence;
            }
        });
        if (currentChunk) chunks.push(currentChunk);
  
        return chunks;
    }

    const updateChatboxTitle = () => {
        const botName = localStorage.getItem("customPromptName") || "Bot";
        document.getElementById("chat-title").textContent = botName;
    };
  
    // Function to append a message with the chatbot's custom name
    function appendMessage(text, sender, isFirstMessage = false) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
  
        if (sender === "bot" && isFirstMessage) {
            const nameSpan = document.createElement("span");
            nameSpan.classList.add("name");
            // Dynamically set the bot's name from localStorage
            nameSpan.textContent = localStorage.getItem("customPromptName") || "Bot";
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
        
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  
    // Add Typing Indicator
    function addTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.classList.add("message", "bot", "typing-indicator");
        typingDiv.innerHTML = `
            <div class="bubble">
                <span class="dots"><span>.</span><span>.</span><span>.</span></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);

        const chatWindow = document.getElementById('chat-window');
        chatWindow.scrollTop = chatWindow.scrollHeight;
        // console.log("Wroking")
    }
  
    // Remove Typing Indicator
    function removeTypingIndicator() {
        const typingDiv = document.querySelector(".typing-indicator");
        if (typingDiv) typingDiv.remove();
    }
  
    function appendMessageWithDelay(text, sender, typingDelay = 0, showTitle = false) {
        const messageChunks = splitMessage(text); // Split the message into chunks
        let totalDelay = 0;
    
        // Ensure only one typing indicator is visible
        const manageTypingIndicator = (action) => {
            if (action === "add") {
                if (!document.querySelector(".typing-indicator")) {
                    addTypingIndicator();
                }
            } else if (action === "remove") {
                removeTypingIndicator();
            }
        };
    
        messageChunks.forEach((chunk, index) => {
            // chatWindow.scrollTop = chatWindow.scrollHeight;
            // Show typing indicator for the duration proportional to the chunk length
            setTimeout(() => {
                manageTypingIndicator("add");
                const chatWindow = document.getElementById('chat-window');
                chatWindow.scrollTop = chatWindow.scrollHeight;
        // console.log("Wroking")
            }, totalDelay);
    
            // Remove typing indicator and show the message
            setTimeout(() => {
                manageTypingIndicator("remove");
                if(chunk.length>0){
                if (index === 0 && sender === "bot" && showTitle) {
                    appendMessage(chunk, sender, true); // Show title for the first chunk if required
                    const chatWindow = document.getElementById('chat-window');
                    chatWindow.scrollTop = chatWindow.scrollHeight;
                // console.log("Wroking")
                } else {
                    appendMessage(chunk, sender);
                    const chatWindow = document.getElementById('chat-window');
                    chatWindow.scrollTop = chatWindow.scrollHeight;
                }}
            }, totalDelay + 30 * chunk.length);
            // console.log("Im triggering");
        
            // const chatWindow = document.getElementById('chat-window');
            // chatWindow.scrollTop = chatWindow.scrollHeight;
            // console.log("Wroking");
    
            // Increment delay to handle the next chunk
            totalDelay += 30 * chunk.length + typingDelay;
        });
    
        // Clean up the last typing indicator
        setTimeout(() => {
            manageTypingIndicator("remove");
        }, totalDelay);        
    }
  
    // Function to send user messages to the bot
    function sendMessage() {
        const userText = userInput.value.trim();
        if (!userText) return; // Do nothing if the input is empty
  
        appendMessage(userText, "user");
        userInput.value = ""; // Clear the input field
        addTypingIndicator();
        const chatWindow = document.getElementById('chat-window');
        chatWindow.scrollTop = chatWindow.scrollHeight;
  
        fetch("/chat", {
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
                appendMessageWithDelay(data.reply, "bot", 300, true);
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
    function fetchInitialMessage() {
        addTypingIndicator();
  
        fetch("/chat", {
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
                appendMessageWithDelay(data.reply, "bot", 0, true);
            })
            .catch((error) => {
                removeTypingIndicator();
                appendMessage("Sorry, something went wrong. Please try again later.", "bot");
            });
    }

    updateChatboxTitle();
    fetchInitialMessage();
    initializeTimer();
  });
  