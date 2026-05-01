document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const searchButton = document.getElementById("searchButton");
    const loading = document.getElementById("loading");
    const resultsContainer = document.getElementById("resultsContainer");
    const cardsWrapper = document.getElementById("cardsWrapper");
    // Export Elements
    const exportBtn = document.getElementById("exportBtn");
    const micButton = document.getElementById("micButton");
    let currentResults = [];

    // Chat Modal Elements
    const chatModal = document.getElementById("chatModal");
    const closeModal = document.getElementById("closeModal");
    const chatModalTitle = document.getElementById("chatModalTitle");
    const chatHistory = document.getElementById("chatHistory");
    const chatInput = document.getElementById("chatInput");
    const sendChatBtn = document.getElementById("sendChatBtn");
    let currentChatStandardId = null;

    closeModal.addEventListener("click", () => chatModal.classList.add("hidden"));
    
    // Close modal when clicking outside
    window.addEventListener("click", (e) => {
        if (e.target === chatModal) chatModal.classList.add("hidden");
    });

    // Voice Input Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        micButton.addEventListener("click", () => {
            recognition.start();
            micButton.classList.add("recording");
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            searchInput.value = transcript;
            micButton.classList.remove("recording");
            // Automatically submit
            searchButton.click();
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            micButton.classList.remove("recording");
        };

        recognition.onend = () => {
            micButton.classList.remove("recording");
        };
    } else {
        micButton.style.display = "none";
    }

    // Keyword Highlighter Helper
    const highlightKeywords = (text, query) => {
        if (!query) return text;
        const words = query.split(/\s+/).filter(w => w.length > 2);
        if (words.length === 0) return text;
        
        let highlighted = text;
        words.forEach(word => {
            // Escape special regex characters in word
            const safeWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`(${safeWord})`, 'gi');
            highlighted = highlighted.replace(regex, '<mark class="highlight">$1</mark>');
        });
        return highlighted;
    };

    searchForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const query = searchInput.value.trim();
        if (!query) return;

        // UI updates for loading state
        searchButton.disabled = true;
        searchButton.style.opacity = "0.7";
        resultsContainer.classList.add("hidden");
        loading.classList.remove("hidden");
        cardsWrapper.innerHTML = "";

        try {
            const response = await fetch("/api/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });

            if (!response.ok) throw new Error("Failed to fetch recommendations");

            const data = await response.json();
            currentResults = data.context; // store for export
            
            // Display Results
            latencyBadge.textContent = `${data.latency_seconds}s`;
            
            if (data.context && data.context.length > 0) {
                data.context.forEach((item, index) => {
                    const card = document.createElement("div");
                    card.className = "card";
                    card.style.animation = `fadeInUp 0.5s ease-out ${index * 0.1}s both`;
                    
                    card.innerHTML = `
                        <div class="card-header">
                            <h3 class="card-title">${item.id}</h3>
                            <div class="card-rank">#${index + 1}</div>
                        </div>
                        <div class="card-content">
                            ${highlightKeywords(item.snippet, query)}
                        </div>
                        <div class="card-actions">
                            <button class="chat-btn" data-id="${item.id}">Talk to Standard 💬</button>
                            <a href="https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails" target="_blank" class="bis-btn">View on BIS Portal 🔗</a>
                        </div>
                    `;
                    cardsWrapper.appendChild(card);
                    
                    // 3D Magnetic Hover Effect
                    card.addEventListener('mousemove', (e) => {
                        const rect = card.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        const centerX = rect.width / 2;
                        const centerY = rect.height / 2;
                        const rotateX = ((y - centerY) / centerY) * -5;
                        const rotateY = ((x - centerX) / centerX) * 5;
                        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
                    });
                    card.addEventListener('mouseleave', () => {
                        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
                    });
                });

                // Attach chat listeners
                document.querySelectorAll(".chat-btn").forEach(btn => {
                    btn.addEventListener("click", (e) => {
                        currentChatStandardId = e.target.getAttribute("data-id");
                        chatModalTitle.textContent = `Talk to ${currentChatStandardId}`;
                        chatHistory.innerHTML = '<div class="bot-msg">Hi! Ask me any specific compliance questions about this standard.</div>';
                        chatInput.value = "";
                        chatModal.classList.remove("hidden");
                        chatInput.focus();
                    });
                });

            } else {
                cardsWrapper.innerHTML = `<p style="text-align:center; color:#64748b;">No standards found for this query.</p>`;
            }

            resultsContainer.classList.remove("hidden");
        } catch (error) {
            console.error(error);
            alert("An error occurred while fetching recommendations.");
        } finally {
            loading.classList.add("hidden");
            searchButton.disabled = false;
            searchButton.style.opacity = "1";
        }
    });

    // Export Logic
    exportBtn.addEventListener('click', () => {
        if (currentResults.length === 0) return;
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Rank,Standard ID,Snippet\n";
        
        currentResults.forEach((item, index) => {
            let safeSnippet = item.snippet.replace(/"/g, '""'); // escape quotes
            csvContent += `${index + 1},"${item.id}","${safeSnippet}"\n`;
        });
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "BIS_Recommendations.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Chat API Logic
    const sendChatMessage = async () => {
        const question = chatInput.value.trim();
        if (!question || !currentChatStandardId) return;

        // Add user msg
        chatHistory.innerHTML += `<div class="user-msg">${question}</div>`;
        chatInput.value = "";
        
        // Add loading bot msg
        const loadingId = "loading-" + Date.now();
        chatHistory.innerHTML += `<div class="bot-msg" id="${loadingId}">Thinking...</div>`;
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ standard_id: currentChatStandardId, question })
            });
            const data = await res.json();
            
            // Streaming/Typing Effect
            const botMsgEl = document.getElementById(loadingId);
            botMsgEl.textContent = "";
            botMsgEl.classList.add("typing-cursor");
            
            const answerText = data.answer;
            for (let i = 0; i < answerText.length; i++) {
                botMsgEl.textContent += answerText.charAt(i);
                chatHistory.scrollTop = chatHistory.scrollHeight;
                await new Promise(r => setTimeout(r, 15)); // typing speed
            }
            botMsgEl.classList.remove("typing-cursor");
            
        } catch (err) {
            document.getElementById(loadingId).textContent = "Error: Could not reach the server.";
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };

    sendChatBtn.addEventListener("click", sendChatMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendChatMessage();
    });

});
