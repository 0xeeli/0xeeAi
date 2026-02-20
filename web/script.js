// URL du fichier public généré par le cerveau Python
// Le cache-buster (?t=...) force ton navigateur et Lighttpd à cracher la dernière version
const PUBLIC_DATA_URL = 'public.json';
const RENT_GOAL = 38.00;

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

    const tollBtn = document.getElementById('pay-toll-btn');
    if (tollBtn) tollBtn.addEventListener('click', payNexusToll);
});

// ==========================================
// NEXUS TOLL — Web3 DApp payment
// ==========================================
const TREASURY_WALLET = "4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr";
const MEMO_PROGRAM_ID  = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLzncY";
const TOLL_LAMPORTS    = 5_000_000; // 0.005 SOL

// Public RPCs tried in order — wallet sends the tx itself, we only need a blockhash
const SOLANA_RPCS = [
    "https://rpc.ankr.com/solana",
    "https://api.mainnet-beta.solana.com",
];

async function _getBlockhash() {
    for (const url of SOLANA_RPCS) {
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0', id: 1,
                    method: 'getLatestBlockhash',
                    params: [{ commitment: 'confirmed' }]
                })
            });
            if (!res.ok) continue;
            const json = await res.json();
            if (json.result?.value?.blockhash) return json.result.value.blockhash;
        } catch (_) { /* try next */ }
    }
    throw new Error('All RPCs failed — try again later.');
}

// Detect any compatible Solana wallet (Phantom, Solflare, Backpack, …)
function _detectWallet() {
    if (window.phantom?.solana)      return window.phantom.solana; // Phantom v2+
    if (window.solana?.isPhantom)    return window.solana;          // Phantom legacy
    if (window.solflare?.isSolflare) return window.solflare;        // Solflare
    if (window.backpack?.isBackpack) return window.backpack;         // Backpack
    if (window.solana)               return window.solana;           // Generic fallback
    return null;
}

async function payNexusToll() {
    const btn      = document.getElementById('pay-toll-btn');
    const statusEl = document.getElementById('toll-status');
    const handle   = document.getElementById('x-handle').value.trim();

    function setStatus(msg, color = 'var(--text-muted)') {
        statusEl.style.color = color;
        statusEl.textContent = msg;
    }

    if (!handle) {
        setStatus('Enter your X handle first.', '#ff3333');
        return;
    }

    const wallet = _detectWallet();
    if (!wallet) {
        setStatus('No Solana wallet detected. Install Phantom, Solflare, or Backpack.', '#ff3333');
        return;
    }

    btn.disabled = true;
    setStatus('Connecting wallet...', 'var(--text-muted)');

    try {
        await wallet.connect();
        const sender = wallet.publicKey;

        setStatus('Fetching blockhash...', 'var(--text-muted)');
        const blockhash = await _getBlockhash();

        const transferIx = solanaWeb3.SystemProgram.transfer({
            fromPubkey: sender,
            toPubkey:   new solanaWeb3.PublicKey(TREASURY_WALLET),
            lamports:   TOLL_LAMPORTS,
        });

        const memoIx = new solanaWeb3.TransactionInstruction({
            programId: new solanaWeb3.PublicKey(MEMO_PROGRAM_ID),
            keys:      [],
            data:      new TextEncoder().encode(handle),
        });

        const tx = new solanaWeb3.Transaction();
        tx.recentBlockhash = blockhash;
        tx.feePayer = sender;
        tx.add(transferIx, memoIx);

        setStatus('Waiting for wallet approval...', 'var(--solana-purple)');
        const { signature } = await wallet.signAndSendTransaction(tx);

        const short = signature.slice(0, 8) + '...';
        setStatus(`Toll received. Tx: ${short}`, 'var(--solana-green)');
        console.log(`[0xeeAI] Nexus Toll paid — sig: ${signature}`);

    } catch (err) {
        if (err.code === 4001 || err.message?.includes('User rejected')) {
            setStatus('Transaction cancelled.', 'var(--text-muted)');
        } else if (err.message?.toLowerCase().includes('insufficient')) {
            setStatus('Insufficient SOL balance.', '#ff3333');
        } else {
            const msg = err.message?.slice(0, 60) || 'Unknown error';
            setStatus(`Error: ${msg}`, '#ff3333');
            console.error('[0xeeAI] Toll error:', err);
        }
    } finally {
        btn.disabled = false;
    }
}
