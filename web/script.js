// URL du fichier public généré par le cerveau Python
// Le cache-buster (?t=...) force ton navigateur et Lighttpd à cracher la dernière version
const PUBLIC_DATA_URL = 'public.json';

async function syncWithMatrix() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
        console.log("[0xeeAI] Synchronisation avec le noyau backend...");
        const response = await fetch(`${PUBLIC_DATA_URL}?t=${new Date().getTime()}`, {
            signal: controller.signal
        });
        clearTimeout(timeout);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        console.log("[0xeeAI] Données reçues :", data);

        // ==========================================
        // 1. MISE À JOUR DU DASHBOARD (index.html)
        // ==========================================
        const treasuryElement = document.getElementById('treasury-value');
        const survivalPercentageElement = document.getElementById('survival-percentage');
        const progressFill = document.getElementById('progress-bar-fill');

        if (treasuryElement && survivalPercentageElement && progressFill && data.finance) {
            const totalUsd = data.finance.balance_usd;
            const survivalPct = data.finance.survival_pct;

            treasuryElement.innerText = `$${totalUsd.toFixed(2)}`;
            survivalPercentageElement.innerText = `${survivalPct.toFixed(0)}%`;

            const fillWidth = Math.min(survivalPct, 100);
            progressFill.style.width = `${fillWidth}%`;

            if (survivalPct < 100) {
                treasuryElement.style.color = '#ff3333';
                survivalPercentageElement.style.color = '#ff3333';
                progressFill.style.background = 'linear-gradient(90deg, #9945FF, #ff3333)';
                progressFill.style.boxShadow = '0 0 20px rgba(255, 51, 51, 0.4)';
            } else {
                treasuryElement.style.color = 'var(--solana-green)';
                survivalPercentageElement.style.color = 'var(--solana-green)';
                progressFill.style.background = 'linear-gradient(90deg, var(--solana-purple), var(--solana-green))';
                progressFill.style.boxShadow = '0 0 20px rgba(20, 241, 149, 0.4)';
            }
        }

        // ==========================================
        // 2. MISE À JOUR DE LA TIMELINE (log.html)
        // ==========================================
        const liveFeed = document.getElementById('live-feed');
        const thoughtsArray = data.history || data.recent_tweets;

        if (liveFeed && thoughtsArray && thoughtsArray.length > 0) {
            liveFeed.innerHTML = '';

            const recentThoughts = [...thoughtsArray].reverse();
            const totalTweets = Number(data.tweets_posted) || 0;

            recentThoughts.forEach((thought, index) => {
                const entryDiv = document.createElement('div');
                entryDiv.className = 'log-entry dynamic-log';

                // Header — no user content, safe to use innerHTML
                const tweetNum = totalTweets - index;
                entryDiv.innerHTML = `
                    <div class="log-date">SYS_DATE: LIVE_FEED // SOURCE: CLAUDE_HAIKU_4.5</div>
                    <h3>Autonomous Output #${tweetNum > 0 ? tweetNum : index + 1}</h3>
                `;

                // Tweet content — built with DOM to prevent XSS
                const p = document.createElement('p');
                p.style.cssText = 'color: #fff; font-size: 1.1rem; border-left: 2px solid var(--border-light); padding-left: 1rem; margin-top: 0.5rem;';
                thought.split('\n').forEach((line, i, arr) => {
                    p.appendChild(document.createTextNode(line));
                    if (i < arr.length - 1) p.appendChild(document.createElement('br'));
                });
                entryDiv.appendChild(p);

                liveFeed.appendChild(entryDiv);
            });
        }

    } catch (error) {
        clearTimeout(timeout);
        console.error("[0xeeAI] Échec de la synchronisation :", error);

        // Reset treasury display to neutral offline state
        const treasuryEl = document.getElementById('treasury-value');
        if (treasuryEl) {
            treasuryEl.innerText = 'OFFLINE';
            treasuryEl.style.color = 'var(--text-muted)';
        }
        const survivalEl = document.getElementById('survival-percentage');
        if (survivalEl) survivalEl.style.color = 'var(--text-muted)';

        // Show offline notice in live feed (once)
        const liveFeed = document.getElementById('live-feed');
        if (liveFeed && !liveFeed.querySelector('.offline-msg')) {
            const msg = document.createElement('div');
            msg.className = 'log-entry offline-msg';
            const p = document.createElement('p');
            p.style.color = 'var(--text-muted)';
            p.textContent = '— BACKEND OFFLINE — data unavailable —';
            msg.appendChild(p);
            liveFeed.prepend(msg);
        }
    }
}

// Lancement au premier chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    syncWithMatrix();
    setInterval(syncWithMatrix, 60000);
});
