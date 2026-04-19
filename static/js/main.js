// Sound Feedback System
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playTone(type) {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    if (type === 'stamp') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(400, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(100, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start(); osc.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'freeze') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
        osc.frequency.linearRampToValueAtTime(1200, audioCtx.currentTime + 0.15);
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
        osc.start(); osc.stop(audioCtx.currentTime + 0.15);
    } else if (type === 'archive') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(300, audioCtx.currentTime);
        osc.frequency.setValueAtTime(400, audioCtx.currentTime + 0.1);
        osc.frequency.setValueAtTime(500, audioCtx.currentTime + 0.2);
        gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.start(); osc.stop(audioCtx.currentTime + 0.4);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Theme Switcher Logic
    const themeBtns = document.querySelectorAll('.theme-btn');
    const safeThemes = ['theme-glacier', 'theme-midnight', 'theme-banana', 'theme-cherry', 'theme-lavender', 'theme-mint', 'theme-peach'];
    
    // Load theme or migrate old dark mode
    let currentTheme = localStorage.getItem('pixelres-theme') || 'theme-glacier';
    if (localStorage.getItem('pixelres-dark') === 'true') {
        currentTheme = 'theme-midnight';
        localStorage.removeItem('pixelres-dark'); // Migration complete
        localStorage.setItem('pixelres-theme', currentTheme);
    }
    
    // Apply initial theme
    document.body.classList.add(currentTheme);

    // Bind UI buttons
    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const newTheme = `theme-${btn.dataset.theme}`;
            // Clean slate
            safeThemes.forEach(t => document.body.classList.remove(t));
            document.body.classList.remove('dark-mode'); 
            
            // Apply new
            document.body.classList.add(newTheme);
            localStorage.setItem('pixelres-theme', newTheme);
        });
    });

    // Category Filters
    const filterBtns = document.querySelectorAll('.filter-btn');
    const resItems = document.querySelectorAll('.res-item:not(.archived-item)'); // exclude archived from filtering if you want, or include
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update active state
            filterBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = '';
                b.style.color = '';
            });
            e.target.classList.add('active');
            e.target.style.background = 'var(--primary)';
            e.target.style.color = 'white';

            const filterId = e.target.dataset.filter;
            resItems.forEach(item => {
                if (filterId === 'All' || item.dataset.category === filterId) {
                    item.style.display = 'flex'; // res-item is flex
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Dynamic Mood Gradient Shift
            document.body.classList.remove('theme-health', 'theme-career', 'theme-golden', 'theme-glacier', 'theme-midnight', 'theme-banana', 'theme-cherry', 'theme-lavender', 'theme-mint', 'theme-peach');
            if (filterId === 'Health') {
                document.body.classList.add('theme-health');
            } else if (filterId === 'Career') {
                document.body.classList.add('theme-career');
            } else {
                // Fallback to Golden Streak or Native Theme
                if (document.body.classList.contains('theme-golden-cache') || document.querySelector('.theme-golden')) {
                    document.body.classList.add('theme-golden');
                } else {
                    const saved = localStorage.getItem('pixelres-theme') || 'theme-glacier';
                    document.body.classList.add(saved);
                }
            }
        });
    });

    // AI Coach
    const aiBtn = document.getElementById('ai-coach-btn');
    const coachBox = document.getElementById('coach-message-box');
    const coachText = document.getElementById('coach-message-text');
    if (aiBtn) {
        aiBtn.addEventListener('click', async () => {
            coachBox.style.display = 'block';
            coachText.innerText = "🤖 Coach is thinking...";
            try {
                const res = await fetch('/api/coach');
                const data = await res.json();
                coachText.innerText = data.message;
            } catch (err) {
                coachText.innerText = "🤖 Coach is taking a break right now.";
            }
        });
    }

    // Modal Logic
    const addBtn = document.getElementById('add-res-btn');
    const modalOverlay = document.getElementById('add-modal');
    const cancelBtn = document.getElementById('cancel-add');
    const saveBtn = document.getElementById('save-add');
    const newTitleInput = document.getElementById('new-res-title');
    const categoryInput = document.getElementById('new-res-category');
    const startInput = document.getElementById('new-res-start');
    const endInput = document.getElementById('new-res-end');
    const enhanceBtn = document.getElementById('enhance-goal-btn');

    if (addBtn) addBtn.addEventListener('click', () => { modalOverlay.classList.add('active'); newTitleInput.focus(); });
    if (cancelBtn) cancelBtn.addEventListener('click', () => { modalOverlay.classList.remove('active'); newTitleInput.value = ''; });

    if (enhanceBtn) {
        enhanceBtn.addEventListener('click', async () => {
            const draft = newTitleInput.value.trim();
            if(!draft) return;
            const originalIcon = enhanceBtn.innerText;
            enhanceBtn.innerText = '⏳';
            try {
                const res = await fetch('/api/enhance-goal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ draft })
                });
                const data = await res.json();
                if (data.success) {
                    newTitleInput.value = data.enhanced;
                } else {
                    alert(data.message);
                }
            } catch (err) {
                console.error(err);
            }
            enhanceBtn.innerText = originalIcon;
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const title = newTitleInput.value.trim();
            const target_start = startInput ? startInput.value : '';
            const target_end = endInput ? endInput.value : '';
            const category = categoryInput ? categoryInput.value : 'Other';
            if (!title) return;

            try {
                const res = await fetch('/api/resolutions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, target_start, target_end, category })
                });
                if (res.ok) window.location.reload();
            } catch (err) { console.error(err); }
        });
    }

    // Edit Modal Logic
    const editModalOverlay = document.getElementById('edit-modal');
    const editBtns = document.querySelectorAll('.btn-edit');
    const cancelEditBtn = document.getElementById('cancel-edit');
    const saveEditBtn = document.getElementById('save-edit');
    
    const editIdInput = document.getElementById('edit-res-id');
    const editTitleInput = document.getElementById('edit-res-title');
    const editCategoryInput = document.getElementById('edit-res-category');
    const editStartInput = document.getElementById('edit-res-start');
    const editEndInput = document.getElementById('edit-res-end');

    editBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const ds = e.currentTarget.dataset;
            editIdInput.value = ds.id;
            editTitleInput.value = ds.title;
            if(editCategoryInput) editCategoryInput.value = ds.category;
            if(editStartInput) editStartInput.value = ds.start;
            if(editEndInput) editEndInput.value = ds.end;
            editModalOverlay.classList.add('active');
            editTitleInput.focus();
        });
    });

    if (cancelEditBtn) cancelEditBtn.addEventListener('click', () => { editModalOverlay.classList.remove('active'); });

    if (saveEditBtn) {
        saveEditBtn.addEventListener('click', async () => {
            const resId = editIdInput.value;
            const title = editTitleInput.value.trim();
            const target_start = editStartInput ? editStartInput.value : '';
            const target_end = editEndInput ? editEndInput.value : '';
            const category = editCategoryInput ? editCategoryInput.value : 'Other';
            if (!title) return;

            try {
                const res = await fetch(`/api/resolutions/${resId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, target_start, target_end, category })
                });
                if (res.ok) window.location.reload();
            } catch (err) { console.error(err); }
        });
    }

    // Toggle & Mood Logic
    const checkboxes = document.querySelectorAll('.clay-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', async (e) => {
            const resId = e.target.dataset.id;
            
            if (e.target.checked) {
                // Show mood picker instead of instant sync
                const moodPicker = document.getElementById(`mood-picker-${resId}`);
                if (moodPicker) moodPicker.style.display = 'block';
                e.target.disabled = true; // disable until mood chosen
            } else {
                // unchecking
                await toggleProgress(resId, false, null, e.target);
            }
        });
    });

    const moodBtns = document.querySelectorAll('.mood-btn');
    moodBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const resId = e.target.dataset.id;
            const mood = e.target.dataset.mood;
            const cb = document.querySelector(`.clay-checkbox[data-id="${resId}"]`);
            await toggleProgress(resId, true, mood, cb);
        });
    });

    async function toggleProgress(resId, isChecking, mood, cbElement) {
        try {
            const res = await fetch(`/api/resolutions/${resId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mood: mood })
            });
            if (!res.ok) {
                if(cbElement) { cbElement.checked = !isChecking; cbElement.disabled = false; }
            } else {
                if (isChecking && typeof confetti === 'function') {
                    const moodPicker = document.getElementById(`mood-picker-${resId}`);
                    if (moodPicker) moodPicker.style.display = 'none';
                    playTone('stamp');
                    confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 }, zIndex: 1000 });
                    setTimeout(() => window.location.reload(), 1200);
                } else {
                    window.location.reload();
                }
            }
        } catch (err) {
            console.error(err);
            if(cbElement) { cbElement.checked = !isChecking; cbElement.disabled = false; }
        }
    }

    // Freezes
    const freezeBtns = document.querySelectorAll('.btn-freeze');
    freezeBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const resId = e.currentTarget.dataset.id;
            if (confirm("Use 1 Ice Cube to keep your streak today?")) {
                try {
                    const res = await fetch(`/api/resolutions/${resId}/freeze`, { method: 'POST' });
                    if (res.ok) {
                        playTone('freeze');
                        setTimeout(() => window.location.reload(), 500);
                    } else alert("Failed or no ice cubes left!");
                } catch (err) { console.error(err); }
            }
        });
    });

    // Archives
    const archiveBtns = document.querySelectorAll('.btn-archive');
    archiveBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const resId = e.currentTarget.dataset.id;
            if (confirm("Mastered this habit? Move to Trophy Case?")) {
                try {
                    const res = await fetch(`/api/resolutions/${resId}/archive`, { method: 'POST' });
                    if (res.ok) {
                        playTone('archive');
                        setTimeout(() => window.location.reload(), 500);
                    }
                } catch (err) { console.error(err); }
            }
        });
    });

    // Delete Logic
    const deleteBtns = document.querySelectorAll('.btn-delete');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const resId = e.currentTarget.dataset.id;
            if (confirm("Are you sure you want to delete this forever?")) {
                try {
                    const res = await fetch(`/api/resolutions/${resId}`, { method: 'DELETE' });
                    if (res.ok) window.location.reload();
                } catch (err) { console.error(err); }
            }
        });
    });

    // Drag & Drop Reordering
    const resolutionList = document.getElementById('resolution-list');
    let draggedItem = null;

    if (resolutionList) {
        resolutionList.addEventListener('dragstart', (e) => {
            if(e.target.classList && e.target.classList.contains('res-item')) {
                draggedItem = e.target;
                e.target.style.opacity = '0.5';
            }
        });
        resolutionList.addEventListener('dragend', async (e) => {
            if(e.target.classList && e.target.classList.contains('res-item')) {
                e.target.style.opacity = '1';
                draggedItem = null;
                const items = Array.from(resolutionList.querySelectorAll('.res-item:not(.archived-item)'));
                const order = items.map(item => item.dataset.id).filter(id => id);
                if(order.length > 0) {
                    try {
                        await fetch('/api/resolutions/reorder', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ order })
                        });
                    } catch(err) { console.error(err); }
                }
            }
        });
        resolutionList.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(resolutionList, e.clientX, e.clientY);
            if (draggedItem && afterElement !== draggedItem) {
                if(afterElement) {
                   resolutionList.insertBefore(draggedItem, afterElement);
                } else {
                   resolutionList.appendChild(draggedItem);
                }
            }
        });
    }

    function getDragAfterElement(container, x, y) {
        const draggableElements = [...container.querySelectorAll('.res-item:not([style*="opacity: 0.5"]):not(.archived-item)')];
        let closestDist = Infinity;
        let closestEl = null;
        draggableElements.forEach(child => {
            const box = child.getBoundingClientRect();
            const childCX = box.left + box.width/2;
            const childCY = box.top + box.height/2;
            const dist = Math.hypot(x - childCX, y - childCY);
            if(dist < closestDist && y < childCY + box.height/2) {
                closestDist = dist;
                closestEl = child;
            }
        });
        return closestEl;
    }

    // Focus Timer Logic
    const timerBtns = document.querySelectorAll('.btn-timer');
    const timerModal = document.getElementById('timer-modal');
    const timerTaskTitle = document.getElementById('timer-task-title');
    const countdownDisplay = document.getElementById('countdown-display');
    const startTimerBtn = document.getElementById('start-timer');
    const pauseTimerBtn = document.getElementById('pause-timer');
    const closeTimerBtn = document.getElementById('close-timer');
    const timerMinutesInput = document.getElementById('timer-minutes-input');
    
    let timerInterval = null;
    let timeRemaining = 25 * 60; // 25 mins
    let currentTimerResId = null;

    function updateTimerDisplay() {
        const mins = Math.floor(timeRemaining / 60);
        const secs = timeRemaining % 60;
        if (countdownDisplay) {
            countdownDisplay.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    }

    if(timerMinutesInput) {
        timerMinutesInput.addEventListener('input', () => {
            if(!timerInterval) {
                const mins = parseInt(timerMinutesInput.value) || 25;
                timeRemaining = mins * 60;
                updateTimerDisplay();
            }
        });
    }

    timerBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentTimerResId = e.currentTarget.dataset.id;
            if(timerTaskTitle) timerTaskTitle.innerText = "Focusing on: " + e.currentTarget.dataset.title;
            const defaultMins = timerMinutesInput ? parseInt(timerMinutesInput.value) || 25 : 25;
            timeRemaining = defaultMins * 60;
            updateTimerDisplay();
            if(startTimerBtn) startTimerBtn.style.display = 'inline-block';
            if(pauseTimerBtn) pauseTimerBtn.style.display = 'none';
            if(timerModal) timerModal.classList.add('active');
        });
    });

    if(closeTimerBtn) closeTimerBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        if(timerModal) timerModal.classList.remove('active');
    });

    if(startTimerBtn) startTimerBtn.addEventListener('click', () => {
        startTimerBtn.style.display = 'none';
        if(pauseTimerBtn) pauseTimerBtn.style.display = 'inline-block';
        if(timerMinutesInput) timerMinutesInput.disabled = true; // prevent changing while running
        timerInterval = setInterval(() => {
            timeRemaining--;
            updateTimerDisplay();
            if (timeRemaining <= 0) {
                clearInterval(timerInterval);
                if(timerMinutesInput) timerMinutesInput.disabled = false;
                playTone('archive'); // success sound
                if(typeof confetti === 'function') confetti({ particleCount: 200, spread: 100, origin: { y: 0.6 } });
                
                fetch(`/api/resolutions/${currentTimerResId}/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mood: '💪' })
                }).then(() => setTimeout(() => window.location.reload(), 2000));
            }
        }, 1000);
    });

    if(pauseTimerBtn) pauseTimerBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        timerInterval = null; // Mark interval as cleared for input editing
        if(startTimerBtn) startTimerBtn.style.display = 'inline-block';
        pauseTimerBtn.style.display = 'none';
        if(timerMinutesInput) timerMinutesInput.disabled = false;
    });

    // --- NEW FEATURES ---
    // Graveyard Logic
    const graveyardBtns = document.querySelectorAll('.btn-graveyard');
    const graveyardModal = document.getElementById('graveyard-modal');
    const graveyardIdInput = document.getElementById('graveyard-res-id');
    const graveyardReasonInput = document.getElementById('graveyard-reason');
    const confirmGraveyardBtn = document.getElementById('confirm-graveyard');
    const cancelGraveyardBtn = document.getElementById('cancel-graveyard');

    if(graveyardModal) {
        graveyardBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                graveyardIdInput.value = e.currentTarget.dataset.id;
                graveyardReasonInput.value = '';
                graveyardModal.classList.add('active');
            });
        });
        cancelGraveyardBtn.addEventListener('click', () => graveyardModal.classList.remove('active'));
        confirmGraveyardBtn.addEventListener('click', async () => {
            const resId = graveyardIdInput.value;
            const reason = graveyardReasonInput.value.trim();
            if(!reason) return alert("Please provide a reason.");
            try {
                const res = await fetch(`/api/resolutions/${resId}/graveyard`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason })
                });
                if(res.ok) { playTone('archive'); setTimeout(() => window.location.reload(), 500); }
            } catch(e) { console.error(e); }
        });
    }

    // Graveyard Chat Logic
    const chatBtns = document.querySelectorAll('.btn-graveyard-chat');
    const chatModal = document.getElementById('chat-modal');
    const chatTitle = document.getElementById('chat-habit-title');
    const chatHistoryBox = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatResId = document.getElementById('chat-res-id');
    
    let currentChatHistory = [];

    function appendMessage(text, align, role) {
        const div = document.createElement('div');
        div.style.textAlign = align;
        div.style.marginBottom = '5px';
        const span = document.createElement('span');
        if (role === 'user') {
            span.style.background = 'var(--primary)';
            span.style.color = 'white';
        } else {
            span.style.background = 'rgba(161, 140, 209, 0.2)';
            span.style.color = 'var(--text-dark)';
        }
        span.style.padding = '5px 10px';
        span.style.borderRadius = '10px';
        span.style.display = 'inline-block';
        span.innerText = text;
        div.appendChild(span);
        chatHistoryBox.appendChild(div);
        chatHistoryBox.scrollTop = chatHistoryBox.scrollHeight;
        return div;
    }

    if(chatModal) {
        chatBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                const title = e.currentTarget.dataset.title;
                
                chatResId.value = id;
                chatTitle.innerText = "Discussing: " + title;
                chatHistoryBox.innerHTML = '';
                currentChatHistory = [];
                chatInput.value = '';
                
                chatModal.classList.add('active');
                
                // Trigger INSANT local initial greeting
                const greeting = `I'm here to listen. Tell me more about what went wrong with "${title}" and why you felt that way.`;
                currentChatHistory.push({"role": "model", "content": greeting});
                appendMessage(greeting, 'left', 'model');
                
                setTimeout(() => chatInput.focus(), 100);
            });
        });
        
        closeChatBtn.addEventListener('click', () => {
            chatModal.classList.remove('active');
        });
        
        sendChatBtn.addEventListener('click', async () => {
            const msg = chatInput.value.trim();
            if(!msg) return;
            
            chatInput.value = '';
            
            appendMessage(msg, 'right', 'user');
            
            await sendChatMessage(msg);
        });
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatBtn.click();
            }
        });
    }

    async function sendChatMessage(message) {
        const id = chatResId.value;
        const msgBoxId = "msg-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
        
        if (message) {
            currentChatHistory.push({"role": "user", "content": message});
        }
        
        // Show typing indicator via appendChild
        const typingDiv = document.createElement('div');
        typingDiv.id = msgBoxId;
        typingDiv.style.textAlign = 'left';
        typingDiv.style.marginBottom = '5px';
        typingDiv.innerHTML = `<span style="background: rgba(0,0,0,0.1); padding: 5px 10px; border-radius: 10px; display: inline-block; color: var(--text-dark);">... thinking...</span>`;
        chatHistoryBox.appendChild(typingDiv);
        chatHistoryBox.scrollTop = chatHistoryBox.scrollHeight;
        
        try {
            const res = await fetch(`/api/graveyard/${id}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, history: currentChatHistory })
            });
            const data = await res.json();
            
            let parsedReply = data.reply;
            let optionsList = [];
            let offerRevive = false;
            let offerMicro = null;
            try {
                let cleanData = data.reply.replace(/```json/gi, '').replace(/```/g, '').trim();
                let jsonObj = JSON.parse(cleanData);
                parsedReply = jsonObj.reply || data.reply;
                optionsList = jsonObj.options || [];
                offerRevive = jsonObj.offer_revive || false;
                offerMicro = jsonObj.offer_micro || null;
            } catch(jsonErr) {
                console.error("Failed to parse JSON reply from therapist.", jsonErr);
            }
            
            const targetDiv = document.getElementById(msgBoxId);
            if(targetDiv) {
                targetDiv.innerHTML = `<span style="background: rgba(161, 140, 209, 0.2); padding: 5px 10px; border-radius: 10px; display: inline-block; color: var(--text-dark);">${parsedReply}</span>`;
            }
            currentChatHistory.push({"role": "model", "content": parsedReply});

            if (optionsList.length > 0) {
                const optionsDiv = document.createElement('div');
                optionsDiv.style.textAlign = 'right';
                optionsDiv.style.marginTop = '10px';
                optionsDiv.style.marginBottom = '15px';
                optionsDiv.style.display = 'flex';
                optionsDiv.style.flexWrap = 'wrap';
                optionsDiv.style.justifyContent = 'flex-end';
                optionsDiv.style.gap = '5px';
                
                optionsList.forEach(optText => {
                    const btn = document.createElement('button');
                    btn.className = 'btn clay-btn';
                    btn.style.margin = '2px';
                    btn.style.fontSize = '0.8rem';
                    btn.style.padding = '5px 10px';
                    btn.innerText = optText;
                    btn.onclick = () => {
                        chatInput.value = optText;
                        sendChatBtn.click();
                        optionsDiv.remove();
                    };
                    optionsDiv.appendChild(btn);
                });
                chatHistoryBox.appendChild(optionsDiv);
            }
            
            // Render Revive or Micro Habit buttons
            if (offerRevive || offerMicro) {
                const actionContainer = document.createElement('div');
                actionContainer.style.marginTop = '15px';
                actionContainer.style.background = 'rgba(255, 255, 255, 0.5)';
                actionContainer.style.padding = '10px';
                actionContainer.style.borderRadius = '10px';
                
                if (offerRevive) {
                    const reviveDiv = document.createElement('div');
                    reviveDiv.style.textAlign = 'center';
                    reviveDiv.style.marginBottom = offerMicro ? '15px' : '0';
                    
                    const reviveBtn = document.createElement('button');
                    reviveBtn.className = 'btn clay-btn';
                    reviveBtn.style.background = 'linear-gradient(135deg, #ff9a9e, #fecfef)';
                    reviveBtn.style.color = '#333';
                    reviveBtn.style.fontWeight = 'bold';
                    reviveBtn.style.width = '100%';
                    reviveBtn.innerText = '🔥 Revive this Habit!';
                    reviveBtn.onclick = async () => {
                        reviveBtn.innerText = 'Reviving...';
                        try {
                            const r = await fetch(`/api/resolutions/${id}/revive`, { method: 'POST' });
                            if(r.ok) { playTone('freeze'); setTimeout(() => window.location.reload(), 500); }
                        } catch(err) { console.error(err); }
                    };
                    
                    const explainText = document.createElement('p');
                    explainText.style.fontSize = '0.75rem';
                    explainText.style.color = '#666';
                    explainText.style.margin = '5px 0 0 0';
                    explainText.innerText = "Click to pull this out of the graveyard and put it back on your active dashboard with bonus XP!";
                    
                    reviveDiv.appendChild(reviveBtn);
                    reviveDiv.appendChild(explainText);
                    actionContainer.appendChild(reviveDiv);
                }
                
                if (offerMicro) {
                    const microDiv = document.createElement('div');
                    microDiv.style.textAlign = 'center';
                    
                    const microBtn = document.createElement('button');
                    microBtn.className = 'btn clay-btn';
                    microBtn.style.background = 'linear-gradient(135deg, #a1c4fd, #c2e9fb)';
                    microBtn.style.color = '#333';
                    microBtn.style.fontWeight = 'bold';
                    microBtn.style.width = '100%';
                    microBtn.innerText = '🌱 Try Micro-Habit: ' + offerMicro;
                    microBtn.onclick = async () => {
                        microBtn.innerText = 'Setting up...';
                        try {
                            const r = await fetch('/api/resolutions', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ title: offerMicro, category: 'Other', target_start: '', target_end: '' })
                            });
                            if(r.ok) { playTone('stamp'); setTimeout(() => window.location.reload(), 500); }
                        } catch(err) { console.error(err); }
                    };
                    
                    const explainMicro = document.createElement('p');
                    explainMicro.style.fontSize = '0.75rem';
                    explainMicro.style.color = '#666';
                    explainMicro.style.margin = '5px 0 0 0';
                    explainMicro.innerText = "Click to instantly track this bite-sized version as a new resolution on your dashboard.";
                    
                    microDiv.appendChild(microBtn);
                    microDiv.appendChild(explainMicro);
                    actionContainer.appendChild(microDiv);
                }
                chatHistoryBox.appendChild(actionContainer);
            }
            
        } catch(e) {
            const targetDiv = document.getElementById(msgBoxId);
            if(targetDiv) {
                targetDiv.innerHTML = `<span style="color: red;">Error connecting to therapist...</span>`;
            }
        }
        chatHistoryBox.scrollTop = chatHistoryBox.scrollHeight;
    }

    // Time Capsule 
    const addCapsuleBtn = document.getElementById('add-capsule-btn');
    const capsuleModal = document.getElementById('capsule-modal');
    const cancelCapsuleBtn = document.getElementById('cancel-capsule');
    const saveCapsuleBtn = document.getElementById('save-capsule');
    const capsuleContent = document.getElementById('capsule-content');
    const capsuleLevel = document.getElementById('capsule-unlock-level');

    if(capsuleModal) {
        if(addCapsuleBtn) addCapsuleBtn.addEventListener('click', () => {
            capsuleContent.value = '';
            capsuleModal.classList.add('active');
        });
        cancelCapsuleBtn.addEventListener('click', () => capsuleModal.classList.remove('active'));
        saveCapsuleBtn.addEventListener('click', async () => {
            const content = capsuleContent.value.trim();
            const level = capsuleLevel.value;
            if(!content) return;
            try {
                const res = await fetch('/api/capsule', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content, unlock_level: level })
                });
                if(res.ok) window.location.reload();
            } catch(e) { console.error(e); }
        });
    }

    const openCapsuleBtns = document.querySelectorAll('.btn-open-capsule');
    const capsuleOpenModal = document.getElementById('capsule-open-modal');
    const capsuleOpenText = document.getElementById('capsule-open-text');
    const closeCapsuleOpenBtn = document.getElementById('close-capsule-open');
    
    // Auth Modal
    const capsuleAuthModal = document.getElementById('capsule-auth-modal');
    const authCapsuleId = document.getElementById('auth-capsule-id');
    const capsuleAuthPassword = document.getElementById('capsule-auth-password');
    const confirmCapsuleAuth = document.getElementById('confirm-capsule-auth');
    const cancelCapsuleAuth = document.getElementById('cancel-capsule-auth');

    if(capsuleOpenModal && capsuleAuthModal) {
        openCapsuleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                authCapsuleId.value = id;
                capsuleAuthPassword.value = '';
                capsuleAuthModal.classList.add('active');
                capsuleAuthPassword.focus();
            });
        });
        
        cancelCapsuleAuth.addEventListener('click', () => {
            capsuleAuthModal.classList.remove('active');
        });
        
        confirmCapsuleAuth.addEventListener('click', async () => {
            const id = authCapsuleId.value;
            const password = capsuleAuthPassword.value;
            if(!password) return alert("Please present your credentials.");
            
            confirmCapsuleAuth.innerText = 'Verifying...';
            try {
                const res = await fetch(`/api/capsule/${id}/open`, { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });
                const data = await res.json();
                if(data.success) {
                    capsuleAuthModal.classList.remove('active');
                    capsuleOpenText.innerText = data.content;
                    capsuleOpenModal.classList.add('active');
                } else {
                    alert(data.message || "Invalid Security Credentials!");
                }
            } catch(err) { console.error(err); }
            confirmCapsuleAuth.innerText = 'Verify & Unlock 🔓';
        });

        closeCapsuleOpenBtn.addEventListener('click', () => {
            capsuleOpenModal.classList.remove('active');
            window.location.reload(); 
        });
    }
});

// ==========================================
// Glacier Snow Particle Effect
// ==========================================
function initSnow() {
    const canvas = document.createElement('canvas');
    canvas.id = 'snowCanvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '9999'; // Stay on top but don't block clicks
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;

    const snowflakes = [];
    const numFlakes = 75; // Number of snowflakes

    for (let i = 0; i < numFlakes; i++) {
        snowflakes.push({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 2.5 + 0.5,
            speed: Math.random() * 1.5 + 0.5,
            wind: Math.random() * 0.8 - 0.4
        });
    }

    function drawSnow() {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'; // Soft white snow
        ctx.beginPath();
        snowflakes.forEach(flake => {
            ctx.moveTo(flake.x, flake.y);
            ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
        });
        ctx.fill();
        updateSnow();
        requestAnimationFrame(drawSnow);
    }

    function updateSnow() {
        snowflakes.forEach(flake => {
            flake.y += flake.speed;
            flake.x += flake.wind;
            
            // Loop back to top
            if (flake.y > height) {
                flake.y = -flake.radius;
                flake.x = Math.random() * width;
            }
            // Loop sides
            if (flake.x > width) flake.x = 0;
            if (flake.x < 0) flake.x = width;
        });
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    });

    drawSnow();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSnow);
} else {
    initSnow();
}
