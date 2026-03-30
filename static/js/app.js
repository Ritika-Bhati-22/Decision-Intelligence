/**
 * DecisionIQ — Responsive Frontend Logic
 * File: static/js/app.js
 *
 * WHY SEPARATE FILE:
 * - Browser caches JS separately → faster repeat visits
 * - Easier to debug (clear separation of concerns)
 * - Team members can work on CSS/JS independently
 */

// ═══════════════════════════════════════════════════════════
// STATE
// WHY: Single source of truth. All app data lives here.
// Changing state here triggers UI updates — clean pattern.
// ═══════════════════════════════════════════════════════════
const App = {
  sid:         'S' + Math.random().toString(36).slice(2, 8),
  domain:      'startup',
  result:      null,
  history:     [],
  radarChart:  null,
  wiDeltas:    {},
  cmpMode:     false,
  cmpSelected: new Set(),
  rtTimer:     null,
  domains:     {},
  loaderTick:  null,
  loaderStep:  0,
};

// ── DOMAIN SUGGESTIONS ──
// WHY: Pre-filled suggestions guide users, reduces blank page anxiety
const SUGGESTIONS = {
  startup:    ['Launch EdTech app in Tier-2 cities', 'Build AI SaaS for SMBs', 'D2C health supplement brand', 'B2B marketplace for logistics'],
  career:     ['Switch from engineering to product manager', 'Transition into data science', 'Move abroad for MBA', 'Go freelance full-time'],
  business:   ['Open second outlet in new city', 'Pivot from B2C to enterprise', 'Launch international expansion', 'Acquire a competitor'],
  government: ['Digital literacy scheme in rural India', 'Affordable housing policy', 'EV subsidy programme', 'Reform public transport'],
  investment: ['Invest in Indian startup ecosystem', 'Real estate vs mutual funds', 'Bitcoin portfolio entry', 'US stocks via INR'],
  personal:   ['Relocate for better opportunities', 'Start side business while employed', 'Pursue higher education abroad', 'Major lifestyle change'],
};

// WHY: Descriptive feedback makes sliders educational, not just numeric
const FEEDBACK = {
  1: 'Very poor — critical concern',
  2: 'Poor — needs major work',
  3: 'Below average',
  4: 'Fair — some gaps',
  5: 'Average — baseline',
  6: 'Above average',
  7: 'Good — solid foundation',
  8: 'Strong — clear advantage',
  9: 'Excellent — key strength',
  10: 'Outstanding — exceptional!',
};

const LOADER_MSGS = [
  'Parsing decision parameters…',
  'Running weighted ML scoring…',
  'Generating risk profile…',
  'Building scenario simulations…',
  'Applying XAI explanation layer…',
];

// ═══════════════════════════════════════════════════════════
// INIT — called from HTML after Flask injects domains data
// ═══════════════════════════════════════════════════════════
function init(domainsData) {
  App.domains = domainsData;
  buildDomainCards();
  setDomain('startup');
  setupTitleInput();
  setupMobileSidebar(); // WHY: Wire up hamburger + overlay
  setupKeyboard();      // WHY: Keyboard shortcut to analyze
}

// ═══════════════════════════════════════════════════════════
// MOBILE SIDEBAR
// WHY: On mobile the sidebar is a drawer that slides in/out.
// We need: hamburger button → open, overlay click → close,
// close button → close. All managed here.
// ═══════════════════════════════════════════════════════════
function setupMobileSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sb-overlay');
  const menuBtn  = document.getElementById('nav-menu-btn');
  const closeBtn = document.getElementById('btn-close-sb');

  if (!sidebar) return;

  // Open sidebar
  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
    // WHY: Prevent background scroll when drawer is open (mobile UX)
  }

  // Close sidebar
  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (menuBtn) menuBtn.addEventListener('click', openSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);
  if (closeBtn) closeBtn.addEventListener('click', closeSidebar);

  // WHY: Auto-close sidebar on tablet+ resize if it was open
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 769) closeSidebar();
  });

  // WHY: Close sidebar after analyze on mobile (user wants to see results)
  document.getElementById('btn-go')?.addEventListener('click', () => {
    if (window.innerWidth < 769) closeSidebar();
  });
  document.getElementById('fab-analyze')?.addEventListener('click', () => {
    openSidebar(); // FAB opens sidebar to fill in details first
  });
}

// ═══════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// WHY: Power users love shortcuts. Ctrl+Enter = analyze.
// ═══════════════════════════════════════════════════════════
function setupKeyboard() {
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault(); analyze();
    }
    if (e.key === 'Escape') {
      document.getElementById('sidebar')?.classList.remove('open');
      document.getElementById('sb-overlay')?.classList.remove('show');
    }
  });
}

// ═══════════════════════════════════════════════════════════
// DOMAIN
// ═══════════════════════════════════════════════════════════
function buildDomainCards() {
  const grid = document.getElementById('domain-grid');
  if (!grid) return;
  grid.innerHTML = '';
  Object.entries(App.domains).forEach(([key, cfg]) => {
    const el = document.createElement('div');
    el.className = 'domain-card';
    el.id = 'dc-' + key;
    el.onclick = () => setDomain(key);
    el.innerHTML = `<div class="dc-icon">${cfg.icon}</div><div class="dc-label">${cfg.label}</div>`;
    grid.appendChild(el);
  });
}

function setDomain(key) {
  App.domain = key;
  document.querySelectorAll('.domain-card').forEach(c => c.classList.remove('active'));
  document.getElementById('dc-' + key)?.classList.add('active');
  buildSliders(key);
  refreshSuggestions(key);
}

// ═══════════════════════════════════════════════════════════
// SLIDERS
// ═══════════════════════════════════════════════════════════
function buildSliders(domain) {
  const cfg = App.domains[domain];
  if (!cfg) return;
  const list = document.getElementById('slider-list');
  if (!list) return;
  list.innerHTML = '';

  Object.entries(cfg.factors).forEach(([fk, fv]) => {
    const def = cfg.smart_defaults?.[fk] || 5;
    const row = document.createElement('div');
    row.className = 'slider-item';
    row.innerHTML = `
      <div class="slider-top">
        <span class="slider-ico">${fv.icon}</span>
        <span class="slider-name">${fv.label}</span>
        <span class="slider-tip-btn" title="${fv.tip}">ⓘ</span>
        <span class="slider-num" id="sv-${fk}">${def}</span>
      </div>
      <div class="range-wrap">
        <input type="range" min="1" max="10" value="${def}" id="sl-${fk}"
          oninput="onSlider('${fk}', this.value)"
          aria-label="${fv.label}"
          aria-valuemin="1" aria-valuemax="10" aria-valuenow="${def}"/>
      </div>
      <div class="slider-feedback" id="sf-${fk}">${FEEDBACK[def]}</div>
    `;
    // WHY: aria attributes make sliders accessible for screen readers
    list.appendChild(row);
    setTimeout(() => updateTrack(fk, def), 10);
  });
  doRealtime();
}

function onSlider(key, val) {
  val = parseInt(val);
  const numEl  = document.getElementById('sv-' + key);
  const feedEl = document.getElementById('sf-' + key);
  const slEl   = document.getElementById('sl-' + key);

  if (numEl)  numEl.textContent = val;
  if (feedEl) {
    feedEl.textContent = FEEDBACK[val] || '';
    feedEl.style.color = val >= 7 ? 'var(--green)' : val >= 5 ? 'var(--t3)' : 'var(--red)';
  }
  // WHY: Update aria-valuenow for screen readers
  if (slEl) slEl.setAttribute('aria-valuenow', val);

  updateTrack(key, val);
  doRealtime();
}

// WHY: CSS cannot fill range track dynamically — we do it via JS background gradient
function updateTrack(key, val) {
  const sl = document.getElementById('sl-' + key);
  if (!sl) return;
  const pct   = ((val - 1) / 9) * 100;
  const color = val >= 7 ? 'var(--green)' : val >= 5 ? 'var(--cyan)' : 'var(--red)';
  sl.style.background = `linear-gradient(to right, ${color} 0%, ${color} ${pct}%, var(--bg4) ${pct}%, var(--bg4) 100%)`;
}

function applySmartDefaults() {
  const defs = App.domains[App.domain]?.smart_defaults || {};
  Object.entries(defs).forEach(([k, v]) => {
    const sl = document.getElementById('sl-' + k);
    if (sl) { sl.value = v; onSlider(k, v); }
  });
  toast('✓ Smart defaults applied', 'green');
}

// ═══════════════════════════════════════════════════════════
// TITLE SUGGESTIONS (while typing)
// WHY: Reduces empty-page anxiety, speeds up demo inputs
// ═══════════════════════════════════════════════════════════
function setupTitleInput() {
  const inp = document.getElementById('inp-title');
  const box = document.getElementById('suggest-box');
  if (!inp || !box) return;

  inp.addEventListener('input', () => {
    const val   = inp.value.trim().toLowerCase();
    const pool  = SUGGESTIONS[App.domain] || [];
    const hits  = pool.filter(s => s.toLowerCase().includes(val));
    if (!val || !hits.length) { box.classList.remove('open'); return; }
    box.innerHTML = hits.map(h =>
      `<div class="suggest-item" role="option" tabindex="0"
        onclick="pickSuggest('${h.replace(/'/g, "\\'")}')">
        ${h}
      </div>`
    ).join('');
    box.classList.add('open');
  });

  // WHY: Delay so click registers before blur closes the box
  inp.addEventListener('blur', () => setTimeout(() => box.classList.remove('open'), 200));
}

function refreshSuggestions(domain) {
  const inp = document.getElementById('inp-title');
  if (inp) inp.placeholder = SUGGESTIONS[domain]?.[0] || 'Enter your decision…';
}

function pickSuggest(text) {
  const inp = document.getElementById('inp-title');
  if (inp) inp.value = text;
  document.getElementById('suggest-box')?.classList.remove('open');
}

// ═══════════════════════════════════════════════════════════
// REALTIME SCORING (debounced)
// WHY: Debounce = don't fire API on every keystroke.
// Wait 400ms after user stops moving slider → then call API.
// Prevents server overload, saves resources.
// ═══════════════════════════════════════════════════════════
function doRealtime() {
  clearTimeout(App.rtTimer);
  App.rtTimer = setTimeout(async () => {
    const answers = getAnswers();
    if (Object.keys(answers).length < 2) return;

    const dot = document.getElementById('rt-dot');
    const val = document.getElementById('rt-val');
    if (dot) dot.classList.add('live');

    try {
      const res = await fetch('/api/realtime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: App.domain, answers }),
      });
      const d = await res.json();
      if (d.probability && val) {
        val.textContent = Math.round(d.probability) + '%';
        val.classList.add('show');
        val.style.color = d.probability >= 65 ? 'var(--green)' : d.probability >= 45 ? 'var(--amber)' : 'var(--red)';
      }
    } catch (_) {/* silent — server might not be running yet */}
    finally { if (dot) dot.classList.remove('live'); }
  }, 400);
}

// ═══════════════════════════════════════════════════════════
// ANALYZE (main function)
// ═══════════════════════════════════════════════════════════
function getAnswers() {
  const answers = {};
  const cfg = App.domains[App.domain];
  if (!cfg) return answers;
  Object.keys(cfg.factors).forEach(k => {
    const el = document.getElementById('sl-' + k);
    if (el) answers[k] = parseFloat(el.value);
  });
  return answers;
}

async function analyze() {
  const title   = (document.getElementById('inp-title')?.value || '').trim() || 'Untitled Decision';
  const notes   = document.getElementById('inp-notes')?.value || '';
  const answers = getAnswers();

  showLoader();

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, domain: App.domain, answers, notes, session_id: App.sid }),
    });
    if (!res.ok) throw new Error('Server error');
    const data = await res.json();
    App.result  = data;
    App.history = [data, ...App.history.filter(h => h.id !== data.id)].slice(0, 15);
    renderResult(data);
    refreshHistory();
    showView('result');
    toast('✓ Analysis complete', 'green');
  } catch (e) {
    toast('⚠ Error — is Flask running on port 5000?', 'red');
  } finally {
    hideLoader();
  }
}

// ═══════════════════════════════════════════════════════════
// RENDER RESULT
// ═══════════════════════════════════════════════════════════
function renderResult(d) {
  App.wiDeltas = {};

  // Gauge ring animation
  const circum = 376.99; // 2 * PI * r (r=60)
  const offset = circum - (circum * d.probability / 100);
  const arc = document.getElementById('g-arc');
  if (arc) {
    arc.style.strokeDashoffset = offset;
    const col = d.probability >= 65 ? '#38bdf8' : d.probability >= 45 ? '#fbbf24' : '#f87171';
    arc.setAttribute('stroke', col);
  }
  setText('g-num', d.probability + '%');
  const gnum = document.getElementById('g-num');
  if (gnum) gnum.style.color = d.probability >= 65 ? 'var(--cyan)' : d.probability >= 45 ? 'var(--amber)' : 'var(--red)';

  // Header info
  setText('h-title',   d.title);
  setText('h-domain',  d.domain_icon + ' ' + d.domain_label);
  setText('h-conf',    d.confidence);
  setText('h-pct',     d.percentile);
  setText('h-risk',    d.risk_level);
  setClr('h-risk',     d.risk_level === 'Low' ? 'var(--green)' : d.risk_level === 'Medium' ? 'var(--amber)' : 'var(--red)');
  setText('s-prob',    d.probability + '%');
  setText('s-conf',    d.confidence + '%');
  setText('s-risk',    d.risk_level);
  setClr('s-prob', 'var(--cyan)');
  setClr('s-conf', 'var(--purple)');
  setClr('s-risk', d.risk_level === 'Low' ? 'var(--green)' : d.risk_level === 'Medium' ? 'var(--amber)' : 'var(--red)');

  // Verdict
  const vc = document.getElementById('verdict-chip');
  if (vc) { vc.textContent = '● ' + d.verdict; vc.className = 'verdict-chip vc-' + d.verdict_class; }
  setText('v-reason', d.verdict_reason);
  setText('res-id',   `ID: ${d.id}  ·  ${new Date(d.timestamp).toLocaleString()}`);

  // Bias
  const ba = document.getElementById('bias-zone');
  if (ba) ba.innerHTML = d.bias_flag
    ? '<div class="bias-alert">⚠️ <span><strong>Bias Alert:</strong> Extreme score range — validate with experts.</span></div>' : '';

  renderFactors(d);
  renderRadar(d);
  renderInsights(d.insights);
  renderProscons(d.pros_cons);
  renderScenarios(d.scenarios);
  renderRisks(d.risks);
  renderStrategies(d.strategies);
  renderTimeline(d.timeline);
  renderPMatrix(d.risks);
  buildWI(d);
}

function renderFactors(d) {
  const fl = document.getElementById('factor-list');
  if (!fl) return;
  fl.innerHTML = Object.entries(d.factor_labels).map(([k, label]) => {
    const v   = d.factor_scores[k] || 0;
    const ico = d.factor_icons?.[k] || '•';
    const pct = v * 10;
    const col = pct >= 70 ? 'var(--green)' : pct >= 45 ? 'var(--cyan)' : 'var(--red)';
    return `<div class="factor-row">
      <span class="f-ico">${ico}</span>
      <span class="f-name">${label}</span>
      <div class="f-track"><div class="f-bar" data-w="${pct}" style="background:${col}"></div></div>
      <span class="f-val" style="color:${col}">${v}</span>
    </div>`;
  }).join('');
  setTimeout(() => document.querySelectorAll('.f-bar').forEach(b => b.style.width = b.dataset.w + '%'), 80);
}

function renderRadar(d) {
  const ctx = document.getElementById('radar-canvas');
  if (!ctx) return;
  if (App.radarChart) { App.radarChart.destroy(); App.radarChart = null; }
  const labels = Object.values(d.factor_labels);
  const values = Object.values(d.factor_scores).map(v => v / 10);
  App.radarChart = new Chart(ctx, {
    type: 'radar',
    data: { labels, datasets: [{
      label: 'Score', data: values,
      backgroundColor: 'rgba(56,189,248,0.08)',
      borderColor: 'rgba(56,189,248,0.7)', borderWidth: 2,
      pointBackgroundColor: 'var(--purple)',
      pointBorderColor: 'transparent', pointRadius: 4,
      pointHoverRadius: 7,
    }]},
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { r: {
        min: 0, max: 10,
        grid: { color: 'rgba(255,255,255,0.05)' },
        angleLines: { color: 'rgba(255,255,255,0.05)' },
        ticks: { display: false },
        pointLabels: { color: 'rgba(255,255,255,0.4)', font: { size: 9, family: 'JetBrains Mono' } },
      }},
      plugins: { legend: { display: false },
        tooltip: { backgroundColor: 'rgba(9,13,26,0.95)', borderColor: 'rgba(56,189,248,0.3)', borderWidth: 1, titleColor: '#f1f5ff', bodyColor: '#8b9dc3' }
      },
      animation: { duration: 1200 },
    }
  });
}

function renderInsights(insights) {
  const il = document.getElementById('ins-list');
  if (!il) return;
  il.innerHTML = insights.map((ins, i) =>
    `<div class="ins-item"><span class="ins-n">0${i+1}</span><span>${ins}</span></div>`
  ).join('');
}

function renderProscons(pc) {
  const pl = document.getElementById('pros-list');
  const cl = document.getElementById('cons-list');
  if (pl) pl.innerHTML = pc.pros.map(p => `<div class="pc-item"><div class="pc-dot p"></div><span>${p}</span></div>`).join('');
  if (cl) cl.innerHTML = pc.cons.map(c => `<div class="pc-item"><div class="pc-dot c"></div><span>${c}</span></div>`).join('');
}

function renderScenarios(sc) {
  ['best','base','worst'].forEach(t => {
    const s = sc[t]; if (!s) return;
    setText(`sc-${t}-s`, s.score + '%');
    setText(`sc-${t}-c`, s.conditions);
    const bar = document.getElementById(`sc-${t}-b`);
    if (bar) {
      const col = t === 'best' ? 'var(--green)' : t === 'base' ? 'var(--cyan)' : 'var(--red)';
      bar.style.background = col;
      setTimeout(() => { bar.style.width = s.score + '%'; }, 100);
    }
  });
}

function renderRisks(risks) {
  const mk = r => `<div class="risk-card">
    <div class="risk-top">
      <span class="risk-name">${r.name}</span>
      <div class="risk-chips">
        <span class="chip ch-${r.severity[0]}">${r.severity}</span>
        <span class="risk-pct">${Math.round(r.likelihood*100)}%</span>
      </div>
    </div>
    <div class="risk-desc">${r.desc}</div>
    <div class="risk-mit">💡 ${r.mitigation}</div>
  </div>`;
  const none = '<div style="font-size:0.72rem;color:var(--t3);padding:8px">None in this category</div>';
  setHTML('risks-all',  risks.map(mk).join('') || none);
  setHTML('risks-high', risks.filter(r=>r.severity==='High').map(mk).join('') || none);
  setHTML('risks-med',  risks.filter(r=>r.severity==='Medium').map(mk).join('') || none);
  setHTML('risks-low',  risks.filter(r=>r.severity==='Low').map(mk).join('') || none);
}

function renderStrategies(strats) {
  const sl = document.getElementById('strat-list');
  if (!sl) return;
  sl.innerHTML = strats.map((s, i) => `
    <div class="strat-card">
      <span class="strat-num">0${i+1}</span>
      <div class="strat-body">
        <div class="strat-text">${s.text}</div>
        <div class="strat-meta">
          <span class="eff-badge">Effort: ${s.effort}</span>
          <span class="imp-val">↑ ${s.impact}</span>
        </div>
      </div>
    </div>`).join('');
}

function renderTimeline(tl) {
  const el = document.getElementById('timeline');
  if (!el) return;
  el.innerHTML = tl.map((t, i) => `
    <div class="tl-row">
      <div class="tl-dot" style="${i===0?'background:var(--cyan);':''}">${t.icon}</div>
      <div class="tl-body">
        <div class="tl-phase">${t.phase}</div>
        <div class="tl-dur">${t.duration}</div>
        <div class="tl-action">${t.action}</div>
      </div>
    </div>`).join('');
}

function renderPMatrix(risks) {
  const pm = document.getElementById('pm-grid');
  if (!pm) return;
  const m = { act:[], mon:[], wat:[], ign:[] };
  risks.forEach(r => {
    const h = r.likelihood > 0.5, s = r.severity === 'High';
    if (h && s) m.act.push(r.name); else if (h) m.mon.push(r.name);
    else if (s) m.wat.push(r.name); else m.ign.push(r.name);
  });
  const cells = [
    { k:'act', hd:'🔴 Act Now',       cls:'pm-act', sub:'High likelihood + High severity' },
    { k:'mon', hd:'🟡 Monitor',         cls:'pm-mon', sub:'High likelihood + Low severity'  },
    { k:'wat', hd:'🟣 Watch',           cls:'pm-wat', sub:'Low likelihood + High severity'  },
    { k:'ign', hd:'⚫ De-prioritize',   cls:'pm-ign', sub:'Low likelihood + Low severity'   },
  ];
  pm.innerHTML = cells.map(c => `
    <div class="pm-cell">
      <div class="pm-hd ${c.cls}">${c.hd}</div>
      <div class="pm-sub">${c.sub}</div>
      <div class="pm-items">
        ${(m[c.k]||[]).map(n=>`<div class="pm-item">→ ${n}</div>`).join('')||'<div class="pm-empty">None</div>'}
      </div>
    </div>`).join('');
}

// ═══════════════════════════════════════════════════════════
// WHAT-IF SIMULATION
// ═══════════════════════════════════════════════════════════
function buildWI(d) {
  const grid = document.getElementById('wi-grid');
  if (!grid) return;
  const factors = Object.entries(d.factor_labels).slice(0, 6);
  grid.innerHTML = factors.map(([k, label]) => `
    <div class="wi-card">
      <div class="wi-name">${label}</div>
      <div class="wi-ctrl">
        <button class="wi-btn" onclick="doWI('${k}',-1)" aria-label="Decrease ${label}">−</button>
        <span class="wi-delta" id="wd-${k}">Δ 0</span>
        <button class="wi-btn" onclick="doWI('${k}',+1)" aria-label="Increase ${label}">+</button>
      </div>
      <div class="wi-res" id="wr-${k}">Adjust to simulate</div>
    </div>`).join('');
}

async function doWI(factor, d) {
  App.wiDeltas[factor] = (App.wiDeltas[factor] || 0) + d;
  const delta = App.wiDeltas[factor];
  setText('wd-' + factor, `Δ ${delta > 0 ? '+' : ''}${delta}`);
  try {
    const res = await fetch('/api/whatif', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_score: App.result.probability, delta }),
    });
    const r = await res.json();
    const el = document.getElementById('wr-' + factor);
    if (el) {
      const cls = r.impact >= 0 ? 'wi-pos' : 'wi-neg';
      el.innerHTML = `${r.original}% → <span class="${cls}">${r.simulated}% (${r.impact>0?'+':''}${r.impact}%)</span>`;
    }
  } catch (_) {}
}

function resetWI() {
  App.wiDeltas = {};
  document.querySelectorAll('[id^="wd-"]').forEach(e => e.textContent = 'Δ 0');
  document.querySelectorAll('[id^="wr-"]').forEach(e => e.textContent = 'Adjust to simulate');
  toast('What-If reset', 'cyan');
}

// ═══════════════════════════════════════════════════════════
// HISTORY
// ═══════════════════════════════════════════════════════════
function refreshHistory() {
  const list = document.getElementById('hist-scroll');
  if (!list) return;
  if (!App.history.length) { list.innerHTML = '<div style="font-size:0.7rem;color:var(--t3)">No analyses yet</div>'; return; }
  list.innerHTML = App.history.map(h => {
    const cfg = App.domains[h.domain];
    const col = h.probability >= 65 ? 'var(--green)' : h.probability >= 45 ? 'var(--amber)' : 'var(--red)';
    const isCur = App.result?.id === h.id;
    const isSel = App.cmpSelected.has(h.id);
    return `<div class="hist-item ${isCur?'active':''} ${isSel?'border-cyan':''}" id="hi-${h.id}"
      onclick="${App.cmpMode ? `toggleCmp('${h.id}')` : `loadHist('${h.id}')`}">
      <span class="hist-ico">${cfg?.icon||'📋'}</span>
      <div class="hist-body">
        <div class="hist-name">${h.title}</div>
        <div class="hist-meta">${h.domain_label} · ${new Date(h.timestamp).toLocaleDateString()}</div>
      </div>
      <span class="hist-score" style="color:${col}">${h.probability}%</span>
    </div>`;
  }).join('');
}

function loadHist(id) {
  const item = App.history.find(h => h.id === id);
  if (!item) return;
  App.result = item;
  renderResult(item);
  showView('result');
  if (window.innerWidth < 769) document.getElementById('sidebar')?.classList.remove('open');
}

// ═══════════════════════════════════════════════════════════
// COMPARE
// ═══════════════════════════════════════════════════════════
function toggleCmpMode() {
  App.cmpMode = !App.cmpMode;
  App.cmpSelected.clear();
  document.getElementById('btn-compare')?.classList.toggle('active', App.cmpMode);
  refreshHistory();
  updateCmpBtn();
  toast(App.cmpMode ? 'Select 2–3 analyses to compare' : 'Compare mode off', 'cyan');
}

function toggleCmp(id) {
  if (App.cmpSelected.has(id)) App.cmpSelected.delete(id);
  else if (App.cmpSelected.size < 3) App.cmpSelected.add(id);
  else { toast('Max 3 decisions', 'warn'); return; }
  refreshHistory(); updateCmpBtn();
}

function updateCmpBtn() {
  const btn = document.getElementById('btn-cmp-run');
  if (!btn) return;
  btn.style.display = App.cmpSelected.size >= 2 ? 'block' : 'none';
  btn.textContent = `⚖ Compare (${App.cmpSelected.size})`;
}

function runCompare() {
  const items = App.history.filter(h => App.cmpSelected.has(h.id));
  if (items.length < 2) { toast('Select at least 2 analyses', 'warn'); return; }
  renderCompare(items);
  showView('compare');
}

function renderCompare(items) {
  const wrap = document.getElementById('cmp-wrap');
  if (!wrap) return;
  const COLS = ['var(--cyan)', 'var(--green)', 'var(--purple)'];
  // WHY: Dynamic columns based on count
  wrap.style.gridTemplateColumns = `repeat(${Math.min(items.length, window.innerWidth < 600 ? 1 : items.length)}, 1fr)`;
  wrap.innerHTML = items.map((d, i) => {
    const col = COLS[i % COLS.length];
    const bars = Object.entries(d.factor_labels).map(([k, label]) => {
      const v = d.factor_scores[k] || 0;
      return `<div class="cmp-row">
        <span class="cmp-lbl">${label}</span>
        <div class="cmp-trk"><div class="cmp-fl" style="background:${col};width:${v*10}%"></div></div>
        <span class="cmp-vl" style="color:${col}">${v}</span>
      </div>`;
    }).join('');
    return `<div class="cmp-card" style="border-color:${col}33">
      <div class="verdict-chip vc-${d.verdict_class}" style="font-size:0.6rem;padding:3px 10px">● ${d.verdict}</div>
      <div class="cmp-title">${d.domain_icon} ${d.title}</div>
      <div class="cmp-stats">
        <div><div class="cmp-sv" style="color:${col}">${d.probability}%</div><div class="cmp-sl">Prob</div></div>
        <div><div class="cmp-sv" style="color:var(--t2)">${d.confidence}%</div><div class="cmp-sl">Conf</div></div>
        <div><div class="cmp-sv" style="color:var(--amber)">${d.percentile}th</div><div class="cmp-sl">Pctl</div></div>
      </div>
      <div class="cmp-bars">${bars}</div>
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════════════════
// TABS
// ═══════════════════════════════════════════════════════════
function switchTab(btn, panelId) {
  const card = btn.closest('.card') || document;
  card.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('on'));
  card.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById(panelId)?.classList.add('on');
}

// ═══════════════════════════════════════════════════════════
// VIEWS
// ═══════════════════════════════════════════════════════════
function showView(v) {
  document.getElementById('empty-state').style.display  = v==='empty'   ? 'flex'  : 'none';
  document.getElementById('result-view').style.display  = v==='result'  ? 'block' : 'none';
  document.getElementById('compare-view').style.display = v==='compare' ? 'block' : 'none';
  const bb = document.getElementById('btn-back');
  if (bb) bb.style.display = v==='compare' ? 'flex' : 'none';
}

function newSession() { App.result = null; showView('empty'); }

// ═══════════════════════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════════════════════
function exportJSON() {
  if (!App.result) return;
  dl(new Blob([JSON.stringify(App.result, null, 2)], { type: 'application/json' }), `DecisionIQ-${App.result.id}.json`);
  toast('JSON exported ✓', 'green');
}

function exportReport() {
  if (!App.result) return;
  const r = App.result;
  const lines = [
    `DecisionIQ Premium Report`, `ID: ${r.id}`,
    `Date: ${new Date(r.timestamp).toLocaleString()}`,
    '─'.repeat(55),
    `Decision  : ${r.title}`,
    `Domain    : ${r.domain_label}`,
    `Verdict   : ${r.verdict}`,
    `Reason    : ${r.verdict_reason}`,
    '', 'SCORES',
    `  Probability : ${r.probability}%`,
    `  Confidence  : ${r.confidence}%`,
    `  Risk Level  : ${r.risk_level}`,
    `  Percentile  : ${r.percentile}th`,
    '', 'FACTORS',
    ...Object.entries(r.factor_labels).map(([k,v]) => `  ${v.padEnd(22)}: ${r.factor_scores[k]}/10`),
    '', 'SCENARIOS',
    `  Best  : ${r.scenarios.best.score}%  — ${r.scenarios.best.conditions}`,
    `  Base  : ${r.scenarios.base.score}%  — ${r.scenarios.base.conditions}`,
    `  Worst : ${r.scenarios.worst.score}% — ${r.scenarios.worst.conditions}`,
    '', 'PROS', ...r.pros_cons.pros.map(p=>`  ✓ ${p}`),
    '', 'CONS', ...r.pros_cons.cons.map(c=>`  ✗ ${c}`),
    '', 'RISKS', ...r.risks.map(rk=>`  [${rk.severity}] ${rk.name} — ${Math.round(rk.likelihood*100)}% likely\n    ${rk.mitigation}`),
    '', 'STRATEGIES', ...r.strategies.map((s,i)=>`  ${i+1}. ${s.text} (Effort:${s.effort})`),
    '', 'TIMELINE', ...r.timeline.map(t=>`  ${t.phase} (${t.duration}): ${t.action}`),
    '', 'AI INSIGHTS', ...r.insights.map(ins=>`  • ${ins.replace(/<[^>]+>/g,'')}`),
    '', `Notes: ${r.notes||'None'}`,
  ];
  dl(new Blob([lines.join('\n')], { type: 'text/plain' }), `DecisionIQ-${r.id}.txt`);
  toast('Report exported ✓', 'green');
}

function dl(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
}

// ═══════════════════════════════════════════════════════════
// LOADER
// ═══════════════════════════════════════════════════════════
function showLoader() {
  document.getElementById('loader')?.classList.add('show');
  const go = document.getElementById('btn-go');
  if (go) { go.classList.add('loading'); document.getElementById('btn-go-txt').textContent = 'Analyzing…'; }
  let mi = 0; App.loaderStep = 0;
  App.loaderTick = setInterval(() => {
    setText('l-msg', LOADER_MSGS[mi % LOADER_MSGS.length]); mi++;
    document.querySelectorAll('.l-dot').forEach((d, i) => d.classList.toggle('on', i <= App.loaderStep));
    App.loaderStep = (App.loaderStep + 1) % 5;
  }, 600);
}

function hideLoader() {
  clearInterval(App.loaderTick);
  document.getElementById('loader')?.classList.remove('show');
  const go = document.getElementById('btn-go');
  if (go) { go.classList.remove('loading'); document.getElementById('btn-go-txt').textContent = 'Analyze Decision'; }
}

// ═══════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════
let toastT;
function toast(msg, type = 'cyan') {
  const el = document.getElementById('toast');
  if (!el) return;
  const cols = { cyan: 'var(--cyan)', green: 'var(--green)', red: 'var(--red)', warn: 'var(--amber)' };
  el.innerHTML = `<span style="color:${cols[type]||cols.cyan}">●</span> ${msg}`;
  el.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(() => el.classList.remove('show'), 2800);
}

// ── UTILS ──
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function setHTML(id, val) { const el = document.getElementById(id); if (el) el.innerHTML = val; }
function setClr(id, val)  { const el = document.getElementById(id); if (el) el.style.color = val; }
