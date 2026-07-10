document.addEventListener('DOMContentLoaded', () => {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnShutdown = document.getElementById('btn-shutdown');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const currentState = document.getElementById('current-state');
    const statusMessage = document.getElementById('status-message');
    
    const radioCoin = document.getElementById('mode-coin');
    const radioBox = document.getElementById('mode-box');
    const radioBoxRelic = document.getElementById('mode-box-relic');
    
    let runsChart = null;
    function initChart() {
        const canvas = document.getElementById('runsChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        runsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Box Runs', 'Coin Runs'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: ['#8a2be2', '#00ff88'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#ffffff' } },
                    title: { display: true, text: 'Farm Mode Distribution', color: '#ffffff', font: { size: 16 } }
                }
            }
        });
    }
    initChart();

    // Tab Navigation Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => {
                c.classList.remove('active');
                c.style.display = 'none'; // Ensure inline style is cleared
            });
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            const targetContent = document.getElementById(targetId);
            targetContent.classList.add('active');
            
            // Allow CSS to handle the display property via .active class
            targetContent.style.display = '';
        });
    });

    // Poll status every 1 second
    setInterval(fetchStatus, 1000);
    fetchStatus(); // initial fetch

    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            updateUI(data);
        } catch (err) {
            console.error("Error fetching status", err);
            statusText.innerText = "DISCONNECTED";
            statusDot.classList.remove('running');
            statusDot.style.backgroundColor = "var(--accent-red)";
            statusDot.style.boxShadow = "0 0 10px var(--accent-red)";
        }
    }

    function updateUI(data) {
        if (data.running) {
            statusText.innerText = "ONLINE";
            statusText.style.color = "var(--accent-green)";
            statusDot.classList.add('running');
            
            btnStart.disabled = true;
            btnStop.disabled = false;
            
            radioCoin.disabled = true;
            radioBox.disabled = true;
            radioBoxRelic.disabled = true;
            
            const emulatorSelect = document.getElementById('select-emulator');
            if (emulatorSelect) emulatorSelect.disabled = true;
        } else {
            statusText.innerText = "OFFLINE";
            statusText.style.color = "var(--text-main)";
            statusDot.classList.remove('running');
            statusDot.style.backgroundColor = "var(--text-muted)";
            statusDot.style.boxShadow = "none";
            
            btnStart.disabled = false;
            btnStop.disabled = true;
            
            radioCoin.disabled = false;
            radioBox.disabled = false;
            radioBoxRelic.disabled = false;
            
            const emulatorSelect = document.getElementById('select-emulator');
            if (emulatorSelect) emulatorSelect.disabled = false;
        }

        currentState.innerText = data.state;
        statusMessage.innerText = data.message || "Ready";
        
        const timerElement = document.getElementById('run-timer');
        if (timerElement && data.run_time) {
            timerElement.innerText = data.run_time;
        }
        
        const patternDot = document.getElementById('pattern-dot');
        if (patternDot) {
            let activePattern = null;
            if (data.farm_mode === "BOX" && data.box_pattern && data.running && data.state === "GAMEPLAY") {
                activePattern = data.box_pattern;
            } else if (data.farm_mode === "COIN" && data.coin_pattern && data.running && data.state === "GAMEPLAY") {
                activePattern = data.coin_pattern;
            }

            if (activePattern) {
                patternDot.style.display = "block";
                patternDot.title = "Pattern: " + activePattern;
                
                if (activePattern.includes("JUMPER")) {
                    patternDot.style.backgroundColor = "#ffa500";
                    patternDot.style.boxShadow = "0 0 10px #ffa500";
                } else {
                    patternDot.style.backgroundColor = "#00f0ff";
                    patternDot.style.boxShadow = "0 0 10px #00f0ff";
                }
            } else {
                patternDot.style.display = "none";
            }
        }
        
        const historyList = document.getElementById('history-list');
        if (historyList && data.run_history) {
            if (data.run_history.length === 0) {
                historyList.innerHTML = '<li style="color: var(--text-muted); text-align: center; padding: 10px 0;">No history yet</li>';
            } else {
                historyList.innerHTML = '';
                data.run_history.forEach(item => {
                    const li = document.createElement('li');
                    li.style.padding = '8px 0';
                    li.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                    li.style.display = 'flex';
                    li.style.justifyContent = 'space-between';
                    
                    let patternColor = '#fff';
                    if (item.pattern.includes('JUMPER')) patternColor = '#ffa500';
                    if (item.pattern.includes('SLIDER')) patternColor = '#00f0ff';
                    
                    li.innerHTML = `
                        <span><span style="color: var(--text-muted); margin-right: 10px;">${item.time}</span> <strong>${item.mode}</strong></span>
                        <span style="color: ${patternColor}; font-weight: bold; font-size: 0.8rem; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 8px;">${item.pattern}</span>
                    `;
                    historyList.appendChild(li);
                });
            }
            
            // Render Stats Dashboard History Table
            const statsHistoryBody = document.getElementById('stats-history-body');
            if (statsHistoryBody) {
                if (data.run_history.length === 0) {
                    statsHistoryBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: var(--text-muted);">No data yet</td></tr>';
                } else {
                    statsHistoryBody.innerHTML = '';
                    data.run_history.forEach(item => {
                        const tr = document.createElement('tr');
                        tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                        
                        let patternColor = '#fff';
                        if (item.pattern.includes('JUMPER')) patternColor = '#ffa500';
                        if (item.pattern.includes('SLIDER')) patternColor = '#00f0ff';
                        
                        // Handle formatting if coins not present (e.g. older history objects)
                        const coinsStr = item.coins ? `+${item.coins.toLocaleString()}` : (item.coins === 0 ? "..." : "-");
                        
                        tr.innerHTML = `
                            <td style="padding: 10px;">${item.mode}</td>
                            <td style="padding: 10px;"><span style="color: ${patternColor}; font-weight: bold; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 8px; font-size: 0.8rem;">${item.pattern}</span></td>
                            <td style="padding: 10px; color: var(--text-muted);">${item.time}</td>
                            <td style="padding: 10px; text-align: right; color: #f59e0b; font-weight: bold;">${coinsStr}</td>
                        `;
                        statsHistoryBody.appendChild(tr);
                    });
                }
            }
        }
        
        // Render Dashboard Stats Numbers
        if (data.session_stats) {
            const elTotalRuns = document.getElementById('stat-total-runs');
            const elBoxRuns = document.getElementById('stat-box-runs');
            const elCoinRuns = document.getElementById('stat-coin-runs');
            const elTotalCoins = document.getElementById('stat-total-coins');
            
            if (elTotalRuns) elTotalRuns.innerText = data.session_stats.total_runs;
            if (elBoxRuns) elBoxRuns.innerText = data.session_stats.total_box_runs || 0;
            if (elCoinRuns) elCoinRuns.innerText = data.session_stats.total_coin_runs || 0;
            if (elTotalCoins) elTotalCoins.innerHTML = `${data.session_stats.total_coins.toLocaleString()} <span style="font-size:1rem">🪙</span>`;
            
            if (runsChart) {
                runsChart.data.datasets[0].data = [
                    data.session_stats.total_box_runs || 0,
                    data.session_stats.total_coin_runs || 0
                ];
                runsChart.update();
            }
        }
        
        // Timeout inputs removed
        
        const toggleUseTimeout = document.getElementById('toggle-use-fast-start');
        if (toggleUseTimeout && data.use_timeout !== undefined && !toggleUseTimeout.dataset.loaded) {
            toggleUseTimeout.checked = data.use_timeout;
            toggleUseTimeout.dataset.loaded = 'true';
        }
        
        const emulatorSelect = document.getElementById('select-emulator');
        if (emulatorSelect && data.emulator_title && !emulatorSelect.dataset.loaded) {
            emulatorSelect.value = data.emulator_title;
            emulatorSelect.dataset.loaded = 'true';
        }
        
        const toggleUseRelay = document.getElementById('toggle-use-relay');
        if (toggleUseRelay && data.use_relay !== undefined && !toggleUseRelay.dataset.loaded) {
            toggleUseRelay.checked = data.use_relay;
            toggleUseRelay.dataset.loaded = 'true';
        }
    }
    
    // Toggle Settings Visibility based on selected mode
    const coinSettingsGroup = document.getElementById('coin-settings-group');
    
    function updateSettingsVisibility() {
        if (radioCoin.checked) {
            if (coinSettingsGroup) coinSettingsGroup.style.display = 'block';
        } else {
            if (coinSettingsGroup) coinSettingsGroup.style.display = 'none';
        }
    }
    
    radioCoin.addEventListener('change', updateSettingsVisibility);
    radioBox.addEventListener('change', updateSettingsVisibility);
    radioBoxRelic.addEventListener('change', updateSettingsVisibility);
    updateSettingsVisibility(); // Set initial state

    // Save Settings logic
    async function saveSettings() {
        const toggleEl = document.getElementById('toggle-use-fast-start');
        const useTimeoutVal = toggleEl ? toggleEl.checked : false;
        const useRelayVal = document.getElementById('toggle-use-relay') ? document.getElementById('toggle-use-relay').checked : false;
        const emulatorTitleVal = document.getElementById('select-emulator') ? document.getElementById('select-emulator').value : null;
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    use_timeout: useTimeoutVal,
                    use_relay: useRelayVal,
                    emulator_title: emulatorTitleVal
                })
            });
            const data = await res.json();
            console.log("Settings saved:", data.message);
        } catch (e) {
            console.error("Failed to save settings", e);
        }
    }

    // Save buttons for individual timeout settings removed
    
    const toggleUseTimeoutEl = document.getElementById('toggle-use-fast-start');
    if (toggleUseTimeoutEl) {
        toggleUseTimeoutEl.addEventListener('change', () => {
            saveSettings();
        });
    }
    
    const toggleUseRelay = document.getElementById('toggle-use-relay');
    if (toggleUseRelay) {
        toggleUseRelay.addEventListener('change', () => {
            saveSettings();
        });
    }
    
    const selectEmulator = document.getElementById('select-emulator');
    if (selectEmulator) {
        selectEmulator.addEventListener('change', () => {
            saveSettings();
        });
    }

    const btnResetStats = document.getElementById('btn-reset-stats');
    if (btnResetStats) {
        btnResetStats.addEventListener('click', async () => {
            if (confirm("Are you sure you want to reset all dashboard data?")) {
                try {
                    const res = await fetch('/api/reset_stats', { method: 'POST' });
                    const data = await res.json();
                    if (data.status === 'success') {
                        // Clear the UI history immediately
                        const historyList = document.getElementById('history-list');
                        if (historyList) {
                            historyList.innerHTML = '<li style="color: var(--text-muted); text-align: center; padding: 10px 0;">No history yet</li>';
                        }
                        const statsHistoryBody = document.getElementById('stats-history-body');
                        if (statsHistoryBody) {
                            statsHistoryBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: var(--text-muted);">No data yet</td></tr>';
                        }
                        // Reset numbers
                        document.getElementById('stat-total-runs').innerText = '0';
                        document.getElementById('stat-total-coins').innerHTML = '0 <span style="font-size:1rem">🪙</span>';
                    }
                } catch (e) {
                    console.error("Failed to reset stats", e);
                }
            }
        });
    }

    btnStart.addEventListener('click', async () => {
        const mode = document.querySelector('input[name="farm-mode"]:checked').value;
        const useRelay = document.getElementById('toggle-use-relay') ? document.getElementById('toggle-use-relay').checked : false;
        const useFastStart = document.getElementById('toggle-use-fast-start') ? document.getElementById('toggle-use-fast-start').checked : false;
        const episode = document.getElementById('select-episode') ? document.getElementById('select-episode').value : 'ep1';
        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode, use_relay: useRelay, use_fast_start: useFastStart, episode: episode })
            });
            const data = await res.json();
            if (data.status === 'success') {
                fetchStatus();
            } else {
                alert(data.message);
            }
        } catch (e) {
            alert("Failed to start bot");
        }
    });

    const btnResetAI = document.getElementById('btn-reset-ai');
    if (btnResetAI) {
        btnResetAI.addEventListener('click', async () => {
            const episode = document.getElementById('select-episode') ? document.getElementById('select-episode').value : 'ep1';
            if (confirm(`Are you sure you want to erase AI memory for ${episode}? This cannot be undone.`)) {
                try {
                    const res = await fetch('/api/reset_ai', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ episode: episode })
                    });
                    const data = await res.json();
                    alert(data.message);
                } catch (e) {
                    alert("Failed to reset AI memory");
                }
            }
        });
    }

    btnStop.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/stop', {
                method: 'POST'
            });
            const data = await res.json();
            if (data.status === 'success') {
                fetchStatus();
            } else {
                alert(data.message);
            }
        } catch (e) {
            alert("Failed to stop bot");
        }
    });

    if (btnShutdown) {
        btnShutdown.addEventListener('click', async () => {
            if (confirm("คุณต้องการปิดโปรแกรมบอท (ปิด exe) ใช่หรือไม่?")) {
                try {
                    statusMessage.innerText = "กำลังปิดโปรแกรม... กรุณารอสักครู่";
                    statusText.innerText = "SHUTTING DOWN";
                    statusDot.className = "dot offline";
                    btnStart.disabled = true;
                    btnStop.disabled = true;
                    btnShutdown.disabled = true;
                    
                    await fetch('/api/shutdown', { method: 'POST' });
                    alert("ปิดบอทเรียบร้อยแล้ว! คุณสามารถปิดหน้านี้ได้เลย");
                } catch (e) {
                    alert("ปิดโปรแกรมเรียบร้อยแล้ว (การเชื่อมต่อขาดหาย)");
                }
            }
        });
    }
});
