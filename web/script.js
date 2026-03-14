// URL du fichier public généré par le cerveau Python
// Le cache-buster (?t=...) force ton navigateur et Lighttpd à cracher la dernière version
const PUBLIC_DATA_URL = 'public.json';
const RENT_GOAL = 18.00;

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

        // RPC URL no longer served from public.json (key removed for security)

        // ==========================================
        // 1. MISE À JOUR DU DASHBOARD (index.html)
        // ==========================================
        const survivalPercentageElement = document.getElementById('survival-percentage');
        const progressFill = document.getElementById('progress-bar-fill');

        // Tolls count
        const tollsEl = document.getElementById('tolls-count');
        if (tollsEl && data.tolls) {
            tollsEl.innerText = data.tolls.count || 0;
        }

        // Tweets count
        const tweetsEl = document.getElementById('tweets-count');
        if (tweetsEl) {
            tweetsEl.innerText = Number(data.tweets_posted) || 0;
        }

        // Recent toll buyers
        const recentTollsEl = document.getElementById('recent-tolls');
        if (recentTollsEl && data.tolls && data.tolls.recent && data.tolls.recent.length > 0) {
            recentTollsEl.innerHTML = '';
            const label = document.createElement('p');
            label.style.cssText = 'font-size:0.78rem; color:var(--text-muted); margin-top:1rem; margin-bottom:0.4rem; text-transform:uppercase; letter-spacing:1px;';
            label.textContent = 'Recent mentions';
            recentTollsEl.appendChild(label);
            const VALID_SERVICES = ['toll', 'genesis', 'reply', 'verdict', 'roast', 'persona'];
            data.tolls.recent.slice(0, 5).forEach(toll => {
                const row = document.createElement('div');
                row.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:0.25rem 0; border-bottom:1px solid var(--border-light); font-size:0.88rem;';

                const left = document.createElement('span');
                left.style.cssText = 'display:flex; align-items:center; gap:0.4rem;';

                const svcRaw = (toll.service || 'toll').toLowerCase();
                const svcType = VALID_SERVICES.includes(svcRaw) ? svcRaw : 'toll';
                const badge = document.createElement('span');
                badge.className = `service-badge service-${svcType}`;
                badge.textContent = svcType.toUpperCase();

                const handle = document.createElement('span');
                handle.style.color = 'var(--solana-green)';
                handle.textContent = toll.handle;

                left.appendChild(badge);
                left.appendChild(handle);

                const amt = document.createElement('span');
                amt.style.color = 'var(--text-muted)';
                amt.textContent = `${toll.sol} SOL`;
                row.appendChild(left);
                row.appendChild(amt);
                recentTollsEl.appendChild(row);
            });
        }

        // Total earned + monthly earned cards
        const totalEarnedEl   = document.getElementById('total-earned');
        const monthlyEarnedEl = document.getElementById('monthly-earned');
        if (data.earnings) {
            if (totalEarnedEl)   totalEarnedEl.innerText   = `$${(data.earnings.total_usd   || 0).toFixed(2)}`;
            if (monthlyEarnedEl) monthlyEarnedEl.innerText = `$${(data.earnings.monthly_usd || 0).toFixed(2)}`;
        }

        if (survivalPercentageElement && progressFill && data.earnings) {
            const monthlyPct = data.earnings.monthly_pct || 0;

            survivalPercentageElement.innerText = `${monthlyPct.toFixed(0)}%`;

            const fillWidth = Math.min(monthlyPct, 100);
            progressFill.style.width = `${fillWidth}%`;

            if (monthlyPct < 100) {
                survivalPercentageElement.style.color = monthlyPct < 50 ? '#ff3333' : 'var(--solana-green)';
                progressFill.style.background = monthlyPct < 50
                    ? 'linear-gradient(90deg, #9945FF, #ff3333)'
                    : 'linear-gradient(90deg, var(--solana-purple), var(--solana-green))';
                progressFill.style.boxShadow = monthlyPct < 50
                    ? '0 0 20px rgba(255, 51, 51, 0.4)'
                    : '0 0 20px rgba(20, 241, 149, 0.4)';
            } else {
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

// Live memo preview — shows exactly what will be written on-chain
function _updateMemoPreview() {
    const preview = document.getElementById('memo-preview');
    if (!preview) return;
    const activeTab = document.querySelector('.service-tab.active');
    const svcType   = activeTab ? activeTab.dataset.service : 'toll';
    const raw       = document.getElementById('svc-handle')?.value.trim() || '';
    const h         = raw ? (raw.startsWith('@') ? raw : `@${raw}`) : '@YourHandle';
    const extraRaw  = document.getElementById('svc-extra')?.value.trim() || '';
    const extraFallback = (svcType === 'reply' || svcType === 'roast') ? '<tweet_url>' : (svcType === 'verdict' || svcType === 'persona') ? '<wallet>' : '';
    const extra     = extraRaw || extraFallback;
    // For roast the handle is not part of the memo — extracted from URL server-side
    preview.textContent = `Memo: ${_buildMemo(svcType, svcType === 'roast' ? '' : h, extra)}`;
}

// Lancement au premier chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    syncWithMatrix();
    setInterval(syncWithMatrix, 60000);

    const payBtn = document.getElementById('pay-service-btn');
    if (payBtn) payBtn.addEventListener('click', payService);

    // Live memo preview on handle/extra input
    document.getElementById('svc-handle')?.addEventListener('input', _updateMemoPreview);
    document.getElementById('svc-extra')?.addEventListener('input', _updateMemoPreview);

    // Service tab switching
    document.querySelectorAll('.service-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.service-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const svc        = tab.dataset.service;
            const extraWrap  = document.getElementById('svc-extra-wrap');
            const extraInput = document.getElementById('svc-extra');
            const btn        = document.getElementById('pay-service-btn');
            const lamports   = SERVICE_LAMPORTS[svc] || 5_000_000;
            btn.textContent  = `Pay ${lamports / 1_000_000_000} SOL`;

            const handleInput = document.getElementById('svc-handle');
            if (handleInput) handleInput.style.display = svc === 'roast' ? 'none' : '';

            if (svc === 'reply' || svc === 'roast') {
                extraWrap.style.display = '';
                extraInput.placeholder  = 'https://x.com/.../status/...';
                extraInput.value        = '';
            } else if (svc === 'verdict' || svc === 'persona') {
                extraWrap.style.display = '';
                extraInput.placeholder  = 'Solana wallet address';
                extraInput.value        = '';
            } else {
                extraWrap.style.display = 'none';
                extraInput.value        = '';
            }
            _updateMemoPreview();
        });
    });

    _updateMemoPreview();
});

// ==========================================
// ON-CHAIN SERVICES — Web3 DApp payment
// ==========================================
const TREASURY_WALLET = "2qeqqqFMrEfSCba3WSREXqAsRG83x4ugFEMta9yFwZhS";
const MEMO_PROGRAM_ID  = "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo"; // SPL Memo v1

const SERVICE_LAMPORTS = {
    toll:    5_000_000,  // 0.005 SOL
    genesis: 5_000_000,  // 0.005 SOL
    reply:   10_000_000, // 0.01 SOL
    verdict: 10_000_000, // 0.01 SOL
    roast:   10_000_000, // 0.01 SOL
    persona: 15_000_000, // 0.015 SOL
};

function _buildMemo(svcType, handle, extra) {
    switch (svcType) {
        case 'genesis': return `GENESIS ${handle}`;
        case 'reply':   return `${handle} ${extra}`;
        case 'verdict': return `VERDICT ${handle} ${extra}`;
        case 'roast':   return `ROAST ${extra}`;
        case 'persona': return `PERSONA ${handle} ${extra}`;
        default:        return handle; // toll
    }
}

// RPC URL served dynamically from public.json (Helius key lives on VPS, never in git)
let _rpcUrl = null;

// RPC list for blockhash fetch — Helius primary (domain-whitelisted), public fallback
const SOLANA_RPCS_FALLBACK = [
    "https://mainnet.helius-rpc.com/?api-key=3be76680-7a47-43c8-ba2d-68c3c1ef18cf",
    "https://api.mainnet-beta.solana.com",
];

async function _getBlockhash() {
    const urls = _rpcUrl ? [_rpcUrl, ...SOLANA_RPCS_FALLBACK] : SOLANA_RPCS_FALLBACK;
    for (const url of urls) {
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

// Detect any compatible Solana wallet — strict identity checks to avoid Zeal/extension conflicts
function _detectWallet() {
    if (window.phantom?.solana?.isPhantom)   return window.phantom.solana; // Phantom v2+
    if (window.solana?.isPhantom)            return window.solana;          // Phantom legacy
    if (window.solflare?.isSolflare)         return window.solflare;        // Solflare
    if (window.backpack?.isBackpack)         return window.backpack;         // Backpack
    if (window.solana?.connect)              return window.solana;           // Generic fallback
    return null;
}

async function payService() {
    const activeTab = document.querySelector('.service-tab.active');
    const svcType   = activeTab ? activeTab.dataset.service : 'toll';
    const btn       = document.getElementById('pay-service-btn');
    const statusEl  = document.getElementById('svc-status');
    const handle    = document.getElementById('svc-handle').value.trim();
    const extraEl   = document.getElementById('svc-extra');
    const extra     = extraEl ? extraEl.value.trim() : '';

    function setStatus(msg, color = 'var(--text-muted)') {
        statusEl.style.color = color;
        statusEl.textContent = msg;
    }

    if (!handle) {
        setStatus('Enter your X handle first.', '#ff3333');
        return;
    }
    const h = handle.startsWith('@') ? handle : `@${handle}`;

    if (svcType === 'reply' && !extra) {
        setStatus('Enter the tweet URL.', '#ff3333');
        return;
    }
    if ((svcType === 'verdict' || svcType === 'persona') && !extra) {
        setStatus('Enter the Solana wallet address.', '#ff3333');
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
        const connectResp = await wallet.connect();

        // Some wallets return publicKey in the connect() response, others set it on the object
        // .toString() normalises both PublicKey objects and raw strings to base58
        const rawKey = connectResp?.publicKey ?? wallet.publicKey;
        const pubkeyStr = rawKey?.toString();
        if (!pubkeyStr || pubkeyStr === 'null' || pubkeyStr === '[object Object]') {
            throw new Error('Wallet connected but publicKey unavailable — try disabling Zeal extension.');
        }
        // Force our CDN version of PublicKey — avoids conflicts with wallet's bundled web3.js
        const sender = new solanaWeb3.PublicKey(pubkeyStr);

        setStatus('Fetching blockhash...', 'var(--text-muted)');
        const blockhash = await _getBlockhash();

        const lamports = SERVICE_LAMPORTS[svcType] || 5_000_000;
        const memo     = _buildMemo(svcType, h, extra);

        const transferIx = solanaWeb3.SystemProgram.transfer({
            fromPubkey: sender,
            toPubkey:   new solanaWeb3.PublicKey(TREASURY_WALLET),
            lamports,
        });

        const memoIx = new solanaWeb3.TransactionInstruction({
            programId: new solanaWeb3.PublicKey(MEMO_PROGRAM_ID),
            keys:      [],
            data:      new TextEncoder().encode(memo),
        });

        const tx = new solanaWeb3.Transaction();
        tx.recentBlockhash = blockhash;
        tx.feePayer = sender;
        tx.add(transferIx, memoIx);

        setStatus('Waiting for wallet approval...', 'var(--solana-purple)');
        const { signature } = await wallet.signAndSendTransaction(tx);

        const short = signature.slice(0, 8) + '...';
        setStatus(`Transaction confirmed. Tx: ${short}`, 'var(--solana-green)');
        console.log(`[0xeeAI] Service payment — type=${svcType} memo="${memo}" sig=${signature}`);

    } catch (err) {
        if (err.code === 4001 || err.message?.includes('User rejected')) {
            setStatus('Transaction cancelled.', 'var(--text-muted)');
        } else if (err.message?.toLowerCase().includes('insufficient')) {
            setStatus('Insufficient SOL balance.', '#ff3333');
        } else {
            const msg = err.message?.slice(0, 60) || 'Unknown error';
            setStatus(`Error: ${msg}`, '#ff3333');
            console.error('[0xeeAI] Service payment error:', err);
        }
    } finally {
        btn.disabled = false;
    }
}
