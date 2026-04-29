document.addEventListener('DOMContentLoaded', () => {
    // ── Tab Navigation ──
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        });
    });

    // ── Chat ──
    const chatInput = document.getElementById('chat-input');
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
    });

    // Load stats on startup
    loadStats();
    loadCuratedTexts();
});

// ── Utility ──
function showToast(msg, isError) {
    const t = document.createElement('div');
    t.className = 'toast' + (isError ? ' error' : '');
    t.innerHTML = `<i class="fa-solid fa-${isError ? 'circle-exclamation' : 'check-circle'}"></i> ${msg}`;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

async function loadStats() {
    try {
        const r = await fetch('/api/people');
        const d = await r.json();
        document.getElementById('stat-people').textContent = d.total || 0;
    } catch(e) { /* ignore */ }
    try {
        const r = await fetch('/api/suggestions');
        // Just show dms count from reference
    } catch(e) { /* ignore */ }
}

// ── Feature #1: Connection Texts ──
async function generateConnectionTexts() {
    const btn = document.getElementById('btn-gen-texts');
    const grid = document.getElementById('grid-connection-texts');
    btn.classList.add('loading');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';
    grid.innerHTML = '<div class="empty-state"><span class="spinner" style="display:inline-block;width:24px;height:24px;border:3px solid rgba(255,255,255,0.1);border-top-color:var(--primary);border-radius:50%;animation:spin 0.6s linear infinite"></span><h3>Generating 25 messages...</h3><p>The AI is researching each person and crafting personalized texts</p></div>';

    try {
        const r = await fetch('/api/connection-texts');
        const d = await r.json();
        renderSuggestionCards(d.suggestions || [], grid, 'connection_text');
        document.getElementById('badge-texts').textContent = (d.suggestions || []).length;
        showToast(`Generated ${(d.suggestions||[]).length} connection texts`);
    } catch(e) {
        grid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><h3>Generation failed</h3><p>Check if the server is running</p></div>';
        showToast('Failed to generate', true);
    }
    btn.classList.remove('loading');
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate 25';
}

// ── Feature #4: Connection Requests ──
async function generateConnectionRequests() {
    const btn = document.getElementById('btn-gen-requests');
    const grid = document.getElementById('grid-connection-requests');
    btn.classList.add('loading');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';
    grid.innerHTML = '<div class="empty-state"><span class="spinner" style="display:inline-block;width:24px;height:24px;border:3px solid rgba(255,255,255,0.1);border-top-color:var(--green);border-radius:50%;animation:spin 0.6s linear infinite"></span><h3>Generating 25 requests...</h3><p>The AI is crafting personalized connection request notes</p></div>';

    try {
        const r = await fetch('/api/connection-requests');
        const d = await r.json();
        renderSuggestionCards(d.suggestions || [], grid, 'connection_request');
        document.getElementById('badge-requests').textContent = (d.suggestions || []).length;
        showToast(`Generated ${(d.suggestions||[]).length} connection requests`);
    } catch(e) {
        grid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><h3>Generation failed</h3><p>Check if the server is running</p></div>';
        showToast('Failed to generate', true);
    }
    btn.classList.remove('loading');
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate 25';
}

// ── Render Suggestion Cards ──
function renderSuggestionCards(suggestions, grid, type) {
    if (!suggestions.length) {
        const statusText = type === 'connection_request' ? 'prospect' : 'connection';
        grid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-database"></i><h3>No results</h3><p>No people with status "${statusText}" found. Add people to your database first.</p></div>`;
        return;
    }
    grid.innerHTML = '';
    suggestions.forEach((s, i) => {
        const card = document.createElement('div');
        card.className = 'suggestion-card';
        card.style.animationDelay = (i * 0.05) + 's';
        const conf = Math.round((s.confidence_score || 0.7) * 100);
        const confColor = conf >= 85 ? 'var(--green)' : conf >= 70 ? 'var(--orange)' : 'var(--red)';
        const typeLabel = type === 'connection_request' ? 'REQUEST' : 'TEXT';
        card.innerHTML = `
            <div class="card-top">
                <div class="card-person">
                    <span class="card-name">${esc(s.name)}</span>
                    <span class="card-role">${esc(s.title || '')} ${s.company ? 'at ' + esc(s.company) : ''}</span>
                </div>
                <div class="card-badges">
                    <span class="badge badge-confidence" style="background:${confColor}22;color:${confColor}">${conf}%</span>
                    <span class="badge badge-type">${typeLabel}</span>
                </div>
            </div>
            <div class="card-message">${esc(s.suggested_message || '')}</div>
            <div class="card-actions">
                <button class="card-btn" onclick="event.stopPropagation();copyMessage(this,'${esc4attr(s.suggested_message||'')}')"><i class="fa-regular fa-copy"></i> Copy</button>
                <button class="card-btn" onclick="event.stopPropagation();openContextWindow(${s.person_id})"><i class="fa-solid fa-microscope"></i> Context</button>
            </div>`;
        card.addEventListener('click', () => {
            document.querySelectorAll('.suggestion-card').forEach(c => c.classList.remove('active-card'));
            card.classList.add('active-card');
            openContextWindow(s.person_id);
        });
        grid.appendChild(card);
    });
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function esc4attr(s) { return s.replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/\n/g,'\\n'); }

function copyMessage(btn, msg) {
    const text = msg.replace(/\\n/g, '\n');
    navigator.clipboard.writeText(text).then(() => {
        btn.classList.add('copied');
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy'; }, 2000);
    });
}

// ── Feature #3: Context Window ──
async function openContextWindow(personId) {
    const panel = document.getElementById('context-panel');
    const body = document.getElementById('context-body');
    panel.classList.add('open');

    body.innerHTML = '<div class="context-empty"><span class="spinner" style="display:inline-block;width:20px;height:20px;border:2px solid rgba(255,255,255,0.1);border-top-color:var(--accent);border-radius:50%;animation:spin 0.6s linear infinite"></span><p>Loading context...</p></div>';

    try {
        const r = await fetch(`/api/context-window/${personId}`);
        const d = await r.json();

        if (d.status === 'not_found' || !d.context_window) {
            body.innerHTML = `<div class="context-empty"><i class="fa-solid fa-circle-info"></i><h3>No Context Yet</h3><p>${d.message || 'Generate suggestions first to see the AI reasoning.'}</p></div>`;
            return;
        }

        const ctx = d.context_window;
        const person = d.person || {};
        const chain = ctx.reasoning_chain || {};
        const web = ctx.web_research || {};
        const step1 = chain.step_1_person_analysis || {};
        const step2 = chain.step_2_pattern_matching || {};
        const step3 = chain.step_3_voice_alignment || {};
        const step4 = chain.step_4_decision || {};

        const voiceScore = Math.round((ctx.voice_alignment_score || 0) * 100);
        const confScore = Math.round((step4.confidence_score || 0) * 100);
        const voiceColor = voiceScore >= 75 ? 'var(--green)' : voiceScore >= 50 ? 'var(--orange)' : 'var(--red)';
        const confColor = confScore >= 80 ? 'var(--green)' : confScore >= 65 ? 'var(--orange)' : 'var(--red)';

        body.innerHTML = `
            <div class="ctx-person-card">
                <div class="ctx-person-name">${esc(person.name || step1.name || 'Unknown')}</div>
                <div class="ctx-person-role">${esc(person.title || step1.title || '')} ${person.company ? 'at ' + esc(person.company) : ''}</div>
            </div>

            <div class="ctx-section">
                <div class="ctx-section-header"><i class="fa-solid fa-user-check"></i><span>Person Analysis</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Industry</span><span class="ctx-item-value">${esc(step1.industry || '—')}</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Interests</span><span class="ctx-item-value">${esc(step1.interests || '—')}</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Traits</span><span class="ctx-item-value">${esc(step1.traits || '—')}</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Contacts</span><span class="ctx-item-value">${(step1.contact_history||{}).total_contacts || 0}</span></div>
            </div>

            <div class="ctx-section">
                <div class="ctx-section-header"><i class="fa-solid fa-diagram-project"></i><span>Pattern Matching</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Matched DM</span><span class="ctx-item-value">${esc(step2.matched_reference_dm || '—')}</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Context</span><span class="ctx-item-value">${esc(step2.matched_context || '—')}</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Success</span><span class="ctx-item-value">${esc(step2.success_indicator || '—')}</span></div>
            </div>

            <div class="ctx-section">
                <div class="ctx-section-header"><i class="fa-solid fa-gauge-high"></i><span>Scores</span></div>
                <div style="margin-bottom:8px">
                    <div class="ctx-item"><span class="ctx-item-label">Voice Alignment</span><span class="ctx-item-value" style="color:${voiceColor}">${voiceScore}%</span></div>
                    <div class="ctx-score"><div class="ctx-score-bar"><div class="ctx-score-fill" style="width:${voiceScore}%;background:${voiceColor}"></div></div></div>
                </div>
                <div>
                    <div class="ctx-item"><span class="ctx-item-label">Confidence</span><span class="ctx-item-value" style="color:${confColor}">${confScore}%</span></div>
                    <div class="ctx-score"><div class="ctx-score-bar"><div class="ctx-score-fill" style="width:${confScore}%;background:${confColor}"></div></div></div>
                </div>
            </div>

            <div class="ctx-section">
                <div class="ctx-section-header"><i class="fa-solid fa-lightbulb"></i><span>Why This Person</span></div>
                <div class="ctx-reason">${esc(step4.why_this_person || 'No reasoning available')}</div>
            </div>

            <div class="ctx-section">
                <div class="ctx-section-header"><i class="fa-solid fa-globe"></i><span>Web Research</span></div>
                <div class="ctx-web">${esc(web.raw_context || 'No web research performed')}</div>
            </div>

            <div class="ctx-section">
                <div class="ctx-section-header"><i class="fa-solid fa-microphone-lines"></i><span>Voice Profile Used</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Tone</span><span class="ctx-item-value">${esc(step3.tone_applied || '—')}</span></div>
                <div class="ctx-item"><span class="ctx-item-label">Themes</span><span class="ctx-item-value">${(step3.core_themes_used || []).join(', ') || '—'}</span></div>
            </div>`;
    } catch(e) {
        body.innerHTML = '<div class="context-empty"><i class="fa-solid fa-triangle-exclamation"></i><h3>Error</h3><p>Could not load context window</p></div>';
    }
}

function closeContextPanel() {
    document.getElementById('context-panel').classList.remove('open');
    document.querySelectorAll('.suggestion-card').forEach(c => c.classList.remove('active-card'));
}

// ── Feature #2: Curated Texts ──
async function loadCuratedTexts() {
    try {
        const r = await fetch('/api/curated-texts');
        const d = await r.json();
        renderCuratedTexts(d.texts || []);
        document.getElementById('badge-curated').textContent = (d.texts || []).length;
    } catch(e) { /* server may not be running */ }
}

function renderCuratedTexts(texts) {
    const grid = document.getElementById('grid-curated-texts');
    if (!texts.length) {
        grid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-pen-fancy"></i><h3>No curated texts yet</h3><p>Add your first message template to get started</p></div>';
        return;
    }
    grid.innerHTML = '';
    texts.forEach((t, i) => {
        const card = document.createElement('div');
        card.className = 'suggestion-card';
        card.style.animationDelay = (i * 0.04) + 's';
        const tags = (t.tags || '').split(',').filter(Boolean).map(tag => `<span class="curated-tag">${esc(tag.trim())}</span>`).join('');
        card.innerHTML = `
            <div class="card-top">
                <div class="card-person">
                    <span class="card-name">${esc(t.title)}</span>
                    <span class="card-role">${esc(t.target_role || '')} ${t.target_industry ? '• ' + esc(t.target_industry) : ''}</span>
                </div>
                <div class="card-badges">
                    <span class="badge" style="background:var(--accent-dim);color:var(--accent)">TEMPLATE</span>
                    ${t.usage_count ? `<span class="badge" style="background:var(--orange-dim);color:var(--orange)">Used ${t.usage_count}x</span>` : ''}
                </div>
            </div>
            <div class="card-message">${esc(t.message_template)}</div>
            <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px">${tags}</div>
            <div class="card-actions">
                <button class="card-btn" onclick="event.stopPropagation();copyMessage(this,'${esc4attr(t.message_template)}')"><i class="fa-regular fa-copy"></i> Copy</button>
                <button class="card-btn" onclick="event.stopPropagation();editCuratedText(${t.id},'${esc4attr(t.title)}','${esc4attr(t.message_template)}','${esc4attr(t.target_industry||'')}','${esc4attr(t.target_role||'')}','${esc4attr(t.tags||'')}')"><i class="fa-solid fa-pen"></i> Edit</button>
                <button class="card-btn" onclick="event.stopPropagation();deleteCuratedText(${t.id})"><i class="fa-solid fa-trash"></i> Delete</button>
            </div>`;
        grid.appendChild(card);
    });
}

function showAddCuratedForm() {
    document.getElementById('curated-form').style.display = 'block';
    document.getElementById('curated-form-title').textContent = 'New Curated Text';
    document.getElementById('curated-edit-id').value = '';
    document.getElementById('curated-title').value = '';
    document.getElementById('curated-message').value = '';
    document.getElementById('curated-industry').value = '';
    document.getElementById('curated-role').value = '';
    document.getElementById('curated-tags').value = '';
    document.getElementById('curated-title').focus();
}

function editCuratedText(id, title, msg, industry, role, tags) {
    document.getElementById('curated-form').style.display = 'block';
    document.getElementById('curated-form-title').textContent = 'Edit Curated Text';
    document.getElementById('curated-edit-id').value = id;
    document.getElementById('curated-title').value = title.replace(/\\n/g, '\n');
    document.getElementById('curated-message').value = msg.replace(/\\n/g, '\n');
    document.getElementById('curated-industry').value = industry;
    document.getElementById('curated-role').value = role;
    document.getElementById('curated-tags').value = tags;
}

function hideCuratedForm() {
    document.getElementById('curated-form').style.display = 'none';
}

async function saveCuratedText() {
    const editId = document.getElementById('curated-edit-id').value;
    const payload = {
        title: document.getElementById('curated-title').value.trim(),
        message_template: document.getElementById('curated-message').value.trim(),
        target_industry: document.getElementById('curated-industry').value.trim(),
        target_role: document.getElementById('curated-role').value.trim(),
        tags: document.getElementById('curated-tags').value.trim()
    };
    if (!payload.title || !payload.message_template) { showToast('Title and message are required', true); return; }

    try {
        const url = editId ? `/api/curated-texts/${editId}` : '/api/curated-texts';
        const method = editId ? 'PUT' : 'POST';
        const r = await fetch(url, { method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        const d = await r.json();
        if (d.status === 'success') {
            showToast(editId ? 'Template updated' : 'Template created');
            hideCuratedForm();
            loadCuratedTexts();
        } else {
            showToast(d.message || 'Failed to save', true);
        }
    } catch(e) {
        showToast('Error saving template', true);
    }
}

async function deleteCuratedText(id) {
    if (!confirm('Delete this template?')) return;
    try {
        const r = await fetch(`/api/curated-texts/${id}`, { method: 'DELETE' });
        const d = await r.json();
        if (d.status === 'success') {
            showToast('Template deleted');
            loadCuratedTexts();
        }
    } catch(e) {
        showToast('Error deleting', true);
    }
}

// ── Chat ──
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = 'auto';

    const msgs = document.getElementById('chat-messages');
    appendChatMsg(msgs, 'user', text);

    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'message ai-message fade-in';
    typingDiv.innerHTML = '<div class="chat-avatar"><i class="fa-solid fa-brain"></i></div><div class="message-content"><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>';
    msgs.appendChild(typingDiv);
    msgs.scrollTo({ top: msgs.scrollHeight, behavior: 'smooth' });

    try {
        const r = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:text}) });
        const d = await r.json();
        document.getElementById(typingId)?.remove();
        appendChatMsg(msgs, 'ai', d.response || 'No response');
    } catch(e) {
        document.getElementById(typingId)?.remove();
        appendChatMsg(msgs, 'ai', 'Error connecting to the server.');
    }
}

function appendChatMsg(container, sender, text) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message fade-in`;
    const avatar = `<div class="chat-avatar"><i class="fa-solid fa-${sender==='ai'?'brain':'user'}"></i></div>`;
    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = sender === 'ai' ? marked.parse(text) : `<p>${text.replace(/\n/g,'<br>')}</p>`;
    div.innerHTML = avatar;
    div.appendChild(content);
    container.appendChild(div);
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}

// ── Feature #6: Auto-Send Pipeline ──
let autoPolling = null;

async function launchAutoOutreach() {
    const mode = document.getElementById('auto-mode').value;
    const count = parseInt(document.getElementById('auto-count').value) || 25;
    const btn = document.getElementById('btn-launch');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;animation:spin 0.6s linear infinite"></span> Launching...';

    try {
        const r = await fetch('/api/auto-outreach/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ mode, count })
        });
        const d = await r.json();

        if (d.status === 'started') {
            showToast(`Auto-outreach launched — mode: ${mode}`);
            document.getElementById('auto-status').style.display = 'block';
            document.getElementById('auto-log').style.display = 'block';

            // Start polling
            if (autoPolling) clearInterval(autoPolling);
            autoPolling = setInterval(pollAutoStatus, 2000);
            pollAutoStatus();
        } else {
            showToast(d.message || 'Failed to launch', true);
        }
    } catch(e) {
        showToast('Error launching auto-outreach', true);
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-rocket"></i> Launch Auto-Send';
}

async function pollAutoStatus() {
    try {
        const r = await fetch('/api/auto-outreach/status');
        const s = await r.json();

        // Phase indicator
        const phaseEl = document.getElementById('auto-phase');
        const phaseMap = {
            'idle': { text: 'Idle', color: 'var(--text-faint)' },
            'generating': { text: '🧠 Generating AI Messages...', color: 'var(--primary)' },
            'logging_in': { text: '🌐 Logging into LinkedIn...', color: 'var(--orange)' },
            'sending': { text: '📤 Sending to LinkedIn DMs...', color: 'var(--green)' },
            'done': { text: '✅ Complete!', color: 'var(--green)' },
            'error': { text: '❌ Error: ' + (s.error || ''), color: 'var(--red)' },
            'stopped': { text: '⏹ Stopped', color: 'var(--orange)' },
        };
        const phase = phaseMap[s.phase] || { text: s.phase, color: 'var(--text-dim)' };
        phaseEl.querySelector('.phase-text').textContent = phase.text;
        phaseEl.querySelector('.phase-dot').style.background = phase.color;

        // Generation progress
        const genPct = s.gen_total > 0 ? (s.gen_completed / s.gen_total * 100) : 0;
        document.getElementById('gen-bar').style.width = genPct + '%';
        document.getElementById('gen-numbers').textContent = `${s.gen_completed} / ${s.gen_total}`;

        // Send progress
        const sendPct = s.send_total > 0 ? (s.send_completed / s.send_total * 100) : 0;
        document.getElementById('send-bar').style.width = sendPct + '%';
        document.getElementById('send-numbers').textContent = `${s.send_completed} / ${s.send_total}`;

        // Stats
        document.getElementById('auto-sent').textContent = s.send_sent;
        document.getElementById('auto-failed').textContent = s.send_failed;
        document.getElementById('auto-total').textContent = s.send_total;

        // Log
        const logBody = document.getElementById('auto-log-body');
        if (s.log && s.log.length) {
            logBody.innerHTML = s.log.map(line => `<div class="log-line">${esc(line)}</div>`).join('');
            logBody.scrollTop = logBody.scrollHeight;
        }

        // Stop polling if done
        if (!s.running && s.phase !== 'idle') {
            clearInterval(autoPolling);
            autoPolling = null;

            if (s.phase === 'done') {
                showToast(`Auto-outreach complete! ${s.send_sent} sent, ${s.send_failed} failed`);
            }
        }
    } catch(e) { /* ignore polling errors */ }
}

async function stopAutoOutreach() {
    try {
        await fetch('/api/auto-outreach/stop', { method: 'POST' });
        showToast('Auto-outreach stopped');
        if (autoPolling) { clearInterval(autoPolling); autoPolling = null; }
        pollAutoStatus();
    } catch(e) {
        showToast('Error stopping', true);
    }
}

// ═══════════════════════════════════════════════════════════════════
// ── CAMPAIGNS ──────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

let _activePollJobId = null;
let _jobPollInterval = null;

// ── Campaign CRUD ─────────────────────────────────────────────────

function showCampaignForm() {
    document.getElementById('campaign-form').style.display = 'block';
    document.getElementById('cmp-name').focus();
}
function hideCampaignForm() { document.getElementById('campaign-form').style.display = 'none'; }

async function saveCampaign() {
    const name  = document.getElementById('cmp-name').value.trim();
    const mode  = document.getElementById('cmp-mode').value;
    const limit = parseInt(document.getElementById('cmp-limit').value) || 25;
    if (!name) { showToast('Campaign name is required', true); return; }
    try {
        const r = await fetch('/api/campaigns', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ name, mode, daily_limit: limit })
        });
        const d = await r.json();
        if (d.status === 'success') {
            showToast(`Campaign "${name}" created`);
            hideCampaignForm();
            loadCampaigns();
        } else { showToast(d.message || 'Failed', true); }
    } catch(e) { showToast('Error creating campaign', true); }
}

async function loadCampaigns() {
    const grid = document.getElementById('grid-campaigns');
    try {
        const r = await fetch('/api/campaigns');
        const d = await r.json();
        const campaigns = d.campaigns || [];
        document.getElementById('badge-campaigns').textContent = campaigns.length;
        if (!campaigns.length) {
            grid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-bullhorn"></i><h3>No campaigns yet</h3><p>Create your first campaign to start the automated pipeline</p></div>';
            return;
        }
        grid.innerHTML = '';
        campaigns.forEach((c, i) => {
            const card = document.createElement('div');
            card.className = 'suggestion-card';
            card.style.animationDelay = (i * 0.05) + 's';
            const statusColor = c.status === 'active' ? 'var(--green)' : c.status === 'paused' ? 'var(--orange)' : 'var(--text-faint)';
            const hasJob = !!c.active_job;
            card.innerHTML = `
                <div class="card-top">
                    <div class="card-person">
                        <span class="card-name">${esc(c.name)}</span>
                        <span class="card-role">Mode: ${c.mode} &nbsp;·&nbsp; Daily limit: ${c.daily_limit} &nbsp;·&nbsp; Sent: ${c.total_sent}</span>
                    </div>
                    <div class="card-badges">
                        <span class="badge" style="background:${statusColor}22;color:${statusColor}">${c.status.toUpperCase()}</span>
                        ${hasJob ? '<span class="badge" style="background:var(--primary-dim);color:var(--primary)">RUNNING</span>' : ''}
                    </div>
                </div>
                <div class="card-actions" style="flex-wrap:wrap;gap:6px">
                    <button class="card-btn" onclick="event.stopPropagation();showImportForm(${c.id},'${esc(c.name)}')"><i class="fa-solid fa-file-import"></i> Import Leads</button>
                    <button class="card-btn card-btn-send" onclick="event.stopPropagation();showRunForm(${c.id},'${esc(c.name)}')"><i class="fa-solid fa-rocket"></i> Run Now</button>
                    <button class="card-btn" onclick="event.stopPropagation();toggleCampaignStatus(${c.id},'${c.status}')">
                        <i class="fa-solid fa-${c.status === 'active' ? 'pause' : 'play'}"></i> ${c.status === 'active' ? 'Pause' : 'Resume'}
                    </button>
                    <button class="card-btn" onclick="event.stopPropagation();viewCampaignJob(${c.id},'${c.active_job || ''}')"><i class="fa-solid fa-terminal"></i> Monitor</button>
                    <button class="card-btn" style="color:var(--red)" onclick="event.stopPropagation();deleteCampaign(${c.id})"><i class="fa-solid fa-trash"></i></button>
                </div>`;
            grid.appendChild(card);
        });
    } catch(e) {
        grid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><h3>Failed to load</h3><p>Is the server running?</p></div>';
    }
}

async function toggleCampaignStatus(id, current) {
    const next = current === 'active' ? 'paused' : 'active';
    try {
        await fetch(`/api/campaigns/${id}/status`, {
            method: 'PATCH',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ status: next })
        });
        showToast(`Campaign ${next}`);
        loadCampaigns();
    } catch(e) { showToast('Error', true); }
}

async function deleteCampaign(id) {
    if (!confirm('Delete this campaign and all its leads?')) return;
    try {
        await fetch(`/api/campaigns/${id}`, { method: 'DELETE' });
        showToast('Campaign deleted');
        loadCampaigns();
        document.getElementById('job-monitor').style.display = 'none';
    } catch(e) { showToast('Error', true); }
}

// ── Import Leads ──────────────────────────────────────────────────

function showImportForm(id, name) {
    document.getElementById('import-form').style.display = 'block';
    document.getElementById('import-cmp-id').value = id;
    document.getElementById('import-cmp-name').textContent = name;
}
function hideImportForm() { document.getElementById('import-form').style.display = 'none'; }

async function importLeads() {
    const cmpId  = parseInt(document.getElementById('import-cmp-id').value);
    const status = document.getElementById('import-status').value;
    const limit  = parseInt(document.getElementById('import-limit').value) || 100;
    const msgType = status === 'prospect' ? 'request' : 'dm';
    try {
        const r = await fetch('/api/leads/import', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ campaign_id: cmpId, connection_status: status, message_type: msgType, limit })
        });
        const d = await r.json();
        if (d.status === 'success') {
            showToast(`Imported ${d.added} leads (${d.total_available} available in Supabase)`);
            hideImportForm();
            loadCampaigns();
        } else { showToast(d.message || 'Import failed', true); }
    } catch(e) { showToast('Error importing leads', true); }
}

// ── Run Campaign ──────────────────────────────────────────────────

function showRunForm(id, name) {
    document.getElementById('run-form').style.display = 'block';
    document.getElementById('run-cmp-id').value = id;
    document.getElementById('run-cmp-name').textContent = name;
}
function hideRunForm() { document.getElementById('run-form').style.display = 'none'; }

async function runCampaign() {
    const cmpId    = parseInt(document.getElementById('run-cmp-id').value);
    const email    = document.getElementById('run-email').value.trim() || null;
    const password = document.getElementById('run-password').value || null;
    try {
        const r = await fetch(`/api/campaigns/${cmpId}/run`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ email, password, headless: false })
        });
        const d = await r.json();
        if (d.status === 'started') {
            showToast(`Pipeline started — job ${d.job_id.slice(0,8)}...`);
            hideRunForm();
            loadCampaigns();
            startJobPoll(d.job_id);
            document.getElementById('job-monitor').style.display = 'block';
        } else { showToast(d.message || 'Failed to start', true); }
    } catch(e) { showToast('Error starting pipeline', true); }
}

// ── Job Monitor ───────────────────────────────────────────────────

async function viewCampaignJob(cmpId, jobId) {
    document.getElementById('job-monitor').style.display = 'block';
    document.getElementById('job-monitor').scrollIntoView({ behavior: 'smooth' });
    if (jobId) {
        startJobPoll(jobId);
    } else {
        // Find most recent job for campaign
        try {
            const r = await fetch('/api/jobs');
            const d = await r.json();
            const job = (d.jobs || []).find(j => j.campaign_id === cmpId);
            if (job) startJobPoll(job.job_id);
            else updateJobMonitor({ phase: 'idle', status: 'no_jobs', sent: 0, failed: 0, total: 0, log_entries: [] });
        } catch(e) {}
    }
}

function startJobPoll(jobId) {
    _activePollJobId = jobId;
    if (_jobPollInterval) clearInterval(_jobPollInterval);
    pollJob();
    _jobPollInterval = setInterval(pollJob, 2000);
}

async function pollJob() {
    if (!_activePollJobId) return;
    try {
        const r = await fetch(`/api/jobs/${_activePollJobId}`);
        const d = await r.json();
        if (d.status !== 'success') return;
        const job = d.job;
        updateJobMonitor(job);
        if (!job.is_active && job.status !== 'running') {
            clearInterval(_jobPollInterval);
            _jobPollInterval = null;
            if (job.status === 'completed') showToast(`Job done — ${job.sent} sent, ${job.failed} failed`);
            loadCampaigns();
        }
    } catch(e) {}
}

function updateJobMonitor(job) {
    const phaseMap = {
        idle: { text: 'Idle', color: 'var(--text-faint)', pulse: false },
        checking_limits: { text: '🔍 Checking Daily Limits...', color: 'var(--accent)', pulse: true },
        fetching_leads: { text: '👥 Fetching Leads...', color: 'var(--accent)', pulse: true },
        generating: { text: '🧠 Generating AI Messages...', color: 'var(--primary)', pulse: true },
        logging_in: { text: '🌐 Logging into LinkedIn...', color: 'var(--orange)', pulse: true },
        sending: { text: '📤 Sending Messages...', color: 'var(--green)', pulse: true },
        done: { text: '✅ Complete', color: 'var(--green)', pulse: false },
        error: { text: '❌ Error', color: 'var(--red)', pulse: false },
        stopped: { text: '⏹ Stopped', color: 'var(--orange)', pulse: false },
        no_jobs: { text: 'No recent jobs', color: 'var(--text-faint)', pulse: false },
    };
    const p = phaseMap[job.phase] || { text: job.phase, color: 'var(--text-dim)', pulse: false };
    document.getElementById('jm-phase-text').textContent = p.text;
    const dot = document.getElementById('jm-dot');
    dot.style.background = p.color;
    dot.classList.toggle('pulsing', p.pulse);

    const total = job.total || 0;
    const genPct = (job.phase === 'sending' || job.phase === 'done') ? 100 : (job.phase === 'generating' ? 50 : 0);
    const sendPct = total > 0 ? ((job.completed || 0) / total * 100) : 0;

    document.getElementById('jm-gen-bar').style.width = genPct + '%';
    document.getElementById('jm-gen-nums').textContent = job.phase === 'done' ? '✓' : (job.phase === 'generating' ? '...' : '—');
    document.getElementById('jm-send-bar').style.width = sendPct + '%';
    document.getElementById('jm-send-nums').textContent = total ? `${job.completed || 0} / ${total}` : '—';
    document.getElementById('jm-sent').textContent = job.sent || 0;
    document.getElementById('jm-failed').textContent = job.failed || 0;
    document.getElementById('jm-total').textContent = total;

    // Log
    const logBody = document.getElementById('jm-log-body');
    const entries = job.log_entries || [];
    if (entries.length) {
        logBody.innerHTML = entries.map(l => `<div class="log-line">${esc(l)}</div>`).join('');
        logBody.scrollTop = logBody.scrollHeight;
    }

    // Show/hide cancel button
    const cancelBtn = document.getElementById('jm-cancel-btn');
    cancelBtn.style.display = job.is_active ? 'flex' : 'none';
}

async function cancelActiveJob() {
    if (!_activePollJobId) return;
    try {
        await fetch(`/api/jobs/${_activePollJobId}/cancel`, { method: 'POST' });
        showToast('Job cancellation requested');
    } catch(e) { showToast('Error', true); }
}

// ═══════════════════════════════════════════════════════════════════
// ── ANALYTICS ──────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

async function loadAnalytics() {
    try {
        const r = await fetch('/api/analytics');
        const d = await r.json();
        if (d.status !== 'success') return;

        // ── Stat cards ────────────────────────────────────────────
        const t = d.totals;
        const statsEl = document.getElementById('an-stats');
        statsEl.innerHTML = [
            { label: 'Total Sent',    value: t.sent,             color: 'var(--green)' },
            { label: 'Success Rate',  value: t.success_rate+'%', color: 'var(--primary)' },
            { label: 'Pending',       value: t.pending,          color: 'var(--orange)' },
            { label: 'Failed',        value: t.failed,           color: 'var(--red)' },
            { label: 'Campaigns',     value: t.campaigns,        color: 'var(--accent)' },
            { label: 'Active Cmp',    value: t.active_campaigns, color: 'var(--accent)' },
        ].map(s => `
            <div class="an-stat-card" style="border-color:${s.color}22">
                <div class="an-stat-value" style="color:${s.color}">${s.value}</div>
                <div class="an-stat-label">${s.label}</div>
            </div>`).join('');

        // ── Daily chart ───────────────────────────────────────────
        const daily = d.daily || [];
        if (daily.length) {
            document.getElementById('an-daily-wrap').style.display = 'block';
            const maxVal = Math.max(...daily.map(x => x.sent), 1);
            document.getElementById('an-chart').innerHTML = daily.map(row => `
                <div class="an-bar-group">
                    <div class="an-bar-wrap">
                        <div class="an-bar" style="height:${Math.round(row.sent / maxVal * 100)}%" title="${row.sent} sent on ${row.day}"></div>
                    </div>
                    <div class="an-bar-label">${row.day ? row.day.slice(5) : ''}</div>
                    <div class="an-bar-value">${row.sent}</div>
                </div>`).reverse().join('');
        }

        // ── Campaign breakdown table ──────────────────────────────
        const cmps = d.campaigns || [];
        if (cmps.length) {
            document.getElementById('an-cmp-wrap').style.display = 'block';
            document.getElementById('an-cmp-body').innerHTML = cmps.map(c => {
                const sc = c.status === 'active' ? 'var(--green)' : 'var(--orange)';
                return `<tr>
                    <td>${esc(c.name)}</td>
                    <td>${c.mode}</td>
                    <td>${c.total_leads}</td>
                    <td style="color:var(--green)">${c.sent}</td>
                    <td style="color:var(--red)">${c.failed}</td>
                    <td style="color:var(--orange)">${c.pending}</td>
                    <td><span style="color:${sc}">${c.status}</span></td>
                </tr>`;
            }).join('');
        }

        // ── Scheduler ─────────────────────────────────────────────
        const sr = await fetch('/api/scheduler/status');
        const sd = await sr.json();
        const sched = sd.scheduler || {};
        const schedBody = document.getElementById('an-scheduler-body');
        if (sched.running && sched.jobs && sched.jobs.length) {
            const next = sched.jobs[0].next_run;
            schedBody.innerHTML = `<span style="color:var(--green)">● Running</span> &nbsp; Next auto-trigger: <strong>${next ? new Date(next).toLocaleString() : '—'}</strong>`;
        } else {
            schedBody.innerHTML = `<span style="color:var(--text-faint)">● Stopped</span>`;
        }
    } catch(e) {
        document.getElementById('an-stats').innerHTML = '<div style="color:var(--red);font-size:0.82rem">Failed to load analytics</div>';
    }
}

async function updateSchedulerInterval() {
    const hours = parseInt(document.getElementById('scheduler-hours').value) || 6;
    try {
        await fetch('/api/scheduler/interval', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ hours })
        });
        showToast(`Scheduler updated — every ${hours}h`);
        loadAnalytics();
    } catch(e) { showToast('Error', true); }
}
