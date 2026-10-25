/**
 * BrandVerify - Clean Client-Side Logic
 * Modules: AuthUI, BrandManager, ReviewDiffController, Toast
 * Strict Black, Grey & White Aesthetic with Newspaper-Style Monochrome PFP
 */

// ==========================================================================
// 1. Auth UI & Session State (Handles Log In / Sign Up / Newspaper PFP)
// ==========================================================================
// Empty = same origin (page served by FastAPI). Set window.BV_API_BASE before this script to override.
const API_BASE_URL = window.BV_API_BASE || "";

async function apiRequest(path, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${path}`,
        options
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.detail || `Request failed: ${response.status}`
        );
    }

    return data;
}
const AuthUI = {
  currentTab: 'login',

  init() {
    this.updateNavbarAuthState();

    // Close PFP dropdown on outside click
    document.addEventListener('click', (e) => {
      const pfpWrapper = document.querySelector('.user-pfp-wrapper');
      const dropdown = document.getElementById('pfp-dropdown-menu');
      if (dropdown && dropdown.classList.contains('active')) {
        if (!pfpWrapper || !pfpWrapper.contains(e.target)) {
          dropdown.classList.remove('active');
        }
      }
    });
  },

  isSignedIn() {
    return localStorage.getItem('bv_signed_in') === 'true';
  },

  updateNavbarAuthState() {
    const guestActions = document.getElementById('nav-guest-actions');
    const userProfile = document.getElementById('nav-user-profile');
    const userEmailSpan = document.getElementById('nav-user-email');
    const savedEmail = localStorage.getItem('bv_user_email') || 'alex@brandverify.ai';

    if (this.isSignedIn()) {
      if (guestActions) guestActions.style.display = 'none';
      if (userProfile) {
        userProfile.style.display = 'flex';
        if (userEmailSpan) userEmailSpan.textContent = savedEmail;
      }
    } else {
      if (guestActions) guestActions.style.display = 'flex';
      if (userProfile) userProfile.style.display = 'none';
    }
  },

  togglePfpMenu(e) {
    if (e) e.stopPropagation();
    const dropdown = document.getElementById('pfp-dropdown-menu');
    if (dropdown) {
      dropdown.classList.toggle('active');
    }
  },

  handleGetStartedClick(e) {
    if (e) e.preventDefault();
    if (this.isSignedIn()) {
      window.location.href = 'dashboard.html';
    } else {
      this.openSignInModal('login');
    }
  },

  openSignInModal(tab = 'login') {
    const modal = document.getElementById('sign-in-modal');
    if (modal) {
      modal.classList.add('active');
      this.switchAuthTab(tab);
    } else {
      window.location.href = 'login.html';
    }
  },

  closeSignInModal() {
    const modal = document.getElementById('sign-in-modal');
    if (modal) modal.classList.remove('active');
  },

  switchAuthTab(tab) {
    this.currentTab = tab;
    const loginBtn = document.getElementById('tab-btn-login');
    const signupBtn = document.getElementById('tab-btn-signup');
    const title = document.getElementById('auth-modal-title');
    const submitBtn = document.getElementById('auth-submit-btn');

    if (tab === 'signup') {
      if (signupBtn) { signupBtn.className = 'btn btn-white btn-sm'; signupBtn.style.flex = '1'; }
      if (loginBtn) { loginBtn.className = 'btn btn-secondary btn-sm'; loginBtn.style.flex = '1'; loginBtn.style.border = 'none'; }
      if (title) title.textContent = 'Create BrandVerify Account';
      if (submitBtn) submitBtn.textContent = 'Sign Up & Continue';
    } else {
      if (loginBtn) { loginBtn.className = 'btn btn-white btn-sm'; loginBtn.style.flex = '1'; }
      if (signupBtn) { signupBtn.className = 'btn btn-secondary btn-sm'; signupBtn.style.flex = '1'; signupBtn.style.border = 'none'; }
      if (title) title.textContent = 'Log In to BrandVerify';
      if (submitBtn) submitBtn.textContent = 'Log In';
    }
  },

  handleSignInSubmit(e) {
    if (e) e.preventDefault();
    const emailInput = document.getElementById('signin-email') || document.getElementById('login-email');
    const email = emailInput ? emailInput.value : 'alex@brandverify.ai';

    localStorage.setItem('bv_signed_in', 'true');
    localStorage.setItem('bv_user_email', email);

    Toast.show(this.currentTab === 'signup' ? 'Account created successfully!' : 'Logged in successfully!', 'success');
    this.closeSignInModal();
    this.updateNavbarAuthState();

    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 400);
  },

  skipSignIn() {
    localStorage.removeItem('bv_signed_in');
    Toast.show('Continuing as guest reviewer.', 'info');
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 200);
  },

  signOut() {
    localStorage.removeItem('bv_signed_in');
    localStorage.removeItem('bv_user_email');
    this.updateNavbarAuthState();
    Toast.show('Logged out.', 'info');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 300);
  }
};

// ==========================================================================
// 2. Brand Manager (Monochromatic Neutral Grey Palettes)
// ==========================================================================
const DEFAULT_BRANDS = {
  'acme-tech': {
    id: 'acme-tech',
    name: 'Acme Global Technologies',
    initials: 'AT',
    bg: 'linear-gradient(135deg, #27272a, #3f3f46)',
    industry: 'Enterprise Cloud & SaaS',
    rulebook: 'FTC Tech & Cloud Claims v3.2',
    rulebookText: 'Prohibited terms: guaranteed 100% bug-free, zero downtime, infinitely scalable. Mandatory disclaimer: Benchmark claims audited by CloudMetrics Labs Q3 2026.',
    palettes: '#ffffff (Primary Light), #a1a1aa (Subtle Zinc), #18181b (Deep Noir)',
    sampleCopy: 'BrandVerify CloudScale engine is guaranteed to be 10X faster than any competitor on the market with zero downtime. Upgrade today to eliminate all latency across your multi-tenant asset pipeline.',
    rulebookAssets: [
      { icon: '📄', name: 'Acme_FTC_CloudClaims_v3.2.pdf', meta: '42 Claim Rules Indexed', badge: 'Active' },
      { icon: '🖼️', name: 'Acme_Primary_Vector_Logo.svg', meta: 'Clear space minimum 32px', badge: 'Active' },
      { icon: '🎨', name: 'Acme_Cloud_Palette.json', meta: '3 Approved Swatches (ΔE < 2.5)', badge: 'Active' },
      { icon: '⚖️', name: 'Cloud_SLA_Safe_Harbor.docx', meta: 'Mandatory Uptime Substantiations', badge: 'Active' },
      { icon: '📝', name: 'Benchmark_Duration_Rules.txt', meta: 'Speed claims require >= 2s display', badge: 'Active' }
    ],
    recentScan: {
      id: 'BV-8492',
      title: 'CloudScale Engine Q4 Launch Copy',
      score: 68,
      statusClass: 'badge-fail',
      statusText: 'Action Required (68% Score)',
      originalCopy: 'BrandVerify CloudScale engine is <span class="diff-del">guaranteed to be 10X faster than any competitor on the market</span> with <span class="diff-del">zero downtime</span>. Upgrade today to eliminate all latency across your multi-tenant asset pipeline.',
      suggestedCopy: 'BrandVerify CloudScale engine is <span class="diff-ins">engineered to deliver up to 10X faster benchmark processing</span> according to verified Q3 internal lab benchmarks. Seamlessly integrate your multi-tenant asset pipeline with <span class="diff-ins">guaranteed compliance logging</span>.',
      footnote: 'Audited Footnote: Benchmark claims audited by CloudMetrics Labs Q3 2026. Individual performance may vary.',
      flags: [
        { type: 'critical', label: 'Critical Claim Flag', text: '"guaranteed to be 10X faster" lacks benchmark audit reference.' },
        { type: 'warning', label: 'Warning Flag', text: '"zero downtime" is an absolute SLA guarantee prohibited by rulebook.' }
      ]
    }
  },
  'luxe-fashion': {
    id: 'luxe-fashion',
    name: 'Luxe & Co. Haute Couture',
    initials: 'LC',
    bg: 'linear-gradient(135deg, #18181b, #27272a)',
    industry: 'Luxury Fashion & Retail',
    rulebook: 'EU Green Claims Directive v2.8',
    rulebookText: 'Mandatory disclaimer: 100% GOTS certified organic silk. Prohibited: zero-impact claims without LCA audit.',
    palettes: '#ffffff (Pure White), #d4d4d8 (Silver Silk), #121215 (Obsidian)',
    sampleCopy: 'Our luxury silk collection has zero impact on the environment and is 100% eco-friendly. Indulge in guilt-free pure haute couture handcrafted in Paris.',
    rulebookAssets: [
      { icon: '📄', name: 'EU_Green_Claims_Directive_v2.8.pdf', meta: '36 Sustainability Rules Indexed', badge: 'Active' },
      { icon: '🖼️', name: 'Luxe_Haute_Couture_Emblem.svg', meta: 'Minimum 48px exclusion zone', badge: 'Active' },
      { icon: '🎨', name: 'Luxe_Monochrome_Silk_Palette.json', meta: 'Approved Swatches (#ffffff, #d4d4d8, #121215)', badge: 'Active' },
      { icon: '⚖️', name: 'Organic_Textile_LCA_Policy.docx', meta: 'GOTS & OEKO-TEX Standard 100', badge: 'Active' },
      { icon: '📝', name: 'Recycled_Packaging_Rules.txt', meta: 'Carbon neutrality claims prohibited without certificate', badge: 'Active' }
    ],
    recentScan: {
      id: 'BV-9104',
      title: 'Autumn Runway - Zero Impact Silk Ad',
      score: 72,
      statusClass: 'badge-fail',
      statusText: 'Review Required (72% Score)',
      originalCopy: 'Our luxury silk collection has <span class="diff-del">zero impact on the environment</span> and is <span class="diff-del">100% eco-friendly</span>. Indulge in guilt-free pure haute couture handcrafted in Paris.',
      suggestedCopy: 'Our luxury silk collection is <span class="diff-ins">crafted from 100% GOTS-certified organic silk</span> with <span class="diff-ins">45% verified reduction in water consumption</span> compared to standard milling.',
      footnote: 'Verified under EU Green Claims Directive (LCA Life-Cycle Assessment audit #2026-EU-441).',
      flags: [
        { type: 'critical', label: 'Critical Green Claim', text: '"zero impact on the environment" is an unverified absolute environmental claim.' },
        { type: 'warning', label: 'Warning Flag', text: '"100% eco-friendly" requires verified life-cycle carbon accounting.' }
      ]
    }
  },
  'apex-finance': {
    id: 'apex-finance',
    name: 'Apex Financial Partners',
    initials: 'AF',
    bg: 'linear-gradient(135deg, #3f3f46, #52525b)',
    industry: 'Asset Management & FinTech',
    rulebook: 'SEC Disclosure Rule 10b-5 & FINRA 2210',
    rulebookText: 'Mandatory safe harbor disclaimer on all performance charts. Prohibited: guaranteed returns.',
    palettes: '#f4f4f5 (Fine Pewter), #71717a (Charcoal), #09090b (Dark Void)',
    sampleCopy: 'Apex AlphaFund yields a guaranteed 14% annual return with zero risk to principal. Maximize your portfolio yields with automated wealth compounding.',
    rulebookAssets: [
      { icon: '📄', name: 'SEC_Rule_10b5_FINRA_2210_Compliance.pdf', meta: '58 Financial Claim Rules Indexed', badge: 'Active' },
      { icon: '🖼️', name: 'Apex_Partners_Monochrome_Lockup.svg', meta: 'Minimum 40px safe zone', badge: 'Active' },
      { icon: '🎨', name: 'Apex_Pewter_Palette.json', meta: 'Approved Swatches (#f4f4f5, #71717a, #09090b)', badge: 'Active' },
      { icon: '⚖️', name: 'FINRA_Safe_Harbor_Disclaimers.docx', meta: 'Mandatory past-performance risk disclaimer', badge: 'Active' },
      { icon: '📝', name: 'Broker_Dealer_Ad_Rules.txt', meta: 'Fixed return claims strictly barred', badge: 'Active' }
    ],
    recentScan: {
      id: 'BV-7321',
      title: 'AlphaFund Yield Growth Social Ad',
      score: 55,
      statusClass: 'badge-fail',
      statusText: 'Action Required (55% Score)',
      originalCopy: 'Apex AlphaFund yields a <span class="diff-del">guaranteed 14% annual return</span> with <span class="diff-del">zero risk to principal</span>. Maximize your portfolio yields with automated wealth compounding.',
      suggestedCopy: 'Apex AlphaFund targets <span class="diff-ins">historical 14% annualized performance</span> across diversified fixed-income assets. <span class="diff-ins">Capital at risk; past performance is no guarantee of future returns</span>.',
      footnote: 'Securities offered through Apex Capital Brokerage. Member FINRA/SIPC. Not FDIC insured.',
      flags: [
        { type: 'critical', label: 'Critical Securities Flag', text: '"guaranteed 14% annual return" violates SEC Rule 10b-5 and FINRA Rule 2210.' },
        { type: 'critical', label: 'Critical Risk Flag', text: '"zero risk to principal" is deceptive in securities marketing.' }
      ]
    }
  },
  'pulse-health': {
    id: 'pulse-health',
    name: 'Pulse BioHealth & Nutrition',
    initials: 'PB',
    bg: 'linear-gradient(135deg, #27272a, #18181b)',
    industry: 'Clinical Biotechnology',
    rulebook: 'FDA Dietary Health Claims v4.1',
    rulebookText: 'Mandatory FDA disclaimer: These statements have not been evaluated by the FDA.',
    palettes: '#ffffff (Clinical White), #a1a1aa (Mid Grey), #18181b (Deep Midnight)',
    sampleCopy: 'NutriBoost is clinically proven to cure chronic fatigue and permanently reverse cellular aging in just 14 days.',
    rulebookAssets: [
      { icon: '📄', name: 'FDA_21CFR_Dietary_Supplement_Rules.pdf', meta: '64 Health Claim Rules Indexed', badge: 'Active' },
      { icon: '🖼️', name: 'Pulse_BioHealth_Verified_Badge.svg', meta: 'Mandatory packaging certification badge', badge: 'Active' },
      { icon: '🎨', name: 'Pulse_Clinical_Palette.json', meta: 'Approved Swatches (#ffffff, #a1a1aa, #18181b)', badge: 'Active' },
      { icon: '⚖️', name: 'DSHEA_Disclaimer_Mandates.docx', meta: 'Section 403(r)(6) statutory notice', badge: 'Active' },
      { icon: '📝', name: 'Clinical_Trial_Citations.txt', meta: 'Double-blind human trial references required', badge: 'Active' }
    ],
    recentScan: {
      id: 'BV-6839',
      title: 'NutriBoost Vitality Serum Commercial Copy',
      score: 60,
      statusClass: 'badge-fail',
      statusText: 'Action Required (60% Score)',
      originalCopy: 'NutriBoost is <span class="diff-del">clinically proven to cure chronic fatigue</span> and <span class="diff-del">permanently reverse cellular aging</span> in just 14 days.',
      suggestedCopy: 'NutriBoost is <span class="diff-ins">formulated to support cellular energy metabolism</span> based on preliminary double-blind clinical evaluations. <span class="diff-ins">These statements have not been evaluated by the FDA</span>.',
      footnote: 'This product is not intended to diagnose, treat, cure, or prevent any disease.',
      flags: [
        { type: 'critical', label: 'Critical Medical Claim', text: '"clinically proven to cure" makes an unauthorized disease treatment claim under FDA rules.' },
        { type: 'critical', label: 'Mandatory Footnote Missing', text: 'Missing required FDA DSHEA statutory disclaimer.' }
      ]
    }
  }
};

const BrandManager = {
  currentBrandId: 'acme-tech',
  brandToDelete: null,

  getBrands() {
    const stored = localStorage.getItem('bv_brand_data');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (Object.keys(parsed).length > 0) {
          // Merge with DEFAULT_BRANDS so new fields (rulebookAssets, recentScan, sampleCopy) are populated
          let updated = false;
          Object.keys(DEFAULT_BRANDS).forEach(k => {
            if (!parsed[k]) {
              parsed[k] = DEFAULT_BRANDS[k];
              updated = true;
            } else if (!parsed[k].rulebookAssets || !parsed[k].recentScan) {
              parsed[k] = { ...DEFAULT_BRANDS[k], ...parsed[k], rulebookAssets: DEFAULT_BRANDS[k].rulebookAssets, recentScan: DEFAULT_BRANDS[k].recentScan, sampleCopy: DEFAULT_BRANDS[k].sampleCopy };
              updated = true;
            }
          });
          if (updated) {
            localStorage.setItem('bv_brand_data', JSON.stringify(parsed));
          }
          return parsed;
        }
      } catch (err) {
        console.error('Error reading brands from storage', err);
      }
    }
    // Seed default brands
    localStorage.setItem('bv_brand_data', JSON.stringify(DEFAULT_BRANDS));
    return { ...DEFAULT_BRANDS };
  },

  saveBrands(brands) {
    localStorage.setItem('bv_brand_data', JSON.stringify(brands));
  },

  getFirstBrandId() {
    const brands = this.getBrands();
    const keys = Object.keys(brands);
    return keys.length > 0 ? keys[0] : null;
  },

  loadBrandPage(requestedId) {
    const brands = this.getBrands();
    const keys = Object.keys(brands);

    // If no brands exist at all, prompt user to create one
    if (keys.length === 0) {
      this.openAddBrandModal();
      Toast.show('No brand selected. Please create a brand profile to continue.', 'info');
      return;
    }

    // Alias normalization
    let targetId = requestedId;
    if (targetId === 'apex-fin' && brands['apex-finance']) targetId = 'apex-finance';
    if (targetId === 'apex-finance' && !brands['apex-finance'] && brands['apex-fin']) targetId = 'apex-fin';

    const brandId = (targetId && brands[targetId]) ? targetId : keys[0];
    this.currentBrandId = brandId;
    const data = brands[brandId];

    // Populate Brand Switcher Header Dropdown
    const selectEl = document.getElementById('brand-page-select');
    if (selectEl) {
      selectEl.innerHTML = '';
      keys.forEach(key => {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = brands[key].name;
        if (key === brandId) opt.selected = true;
        selectEl.appendChild(opt);
      });
    }

    // Update Brand Context Header
    const avatarEl = document.getElementById('brand-page-avatar');
    const nameEl = document.getElementById('brand-page-name');
    const industryEl = document.getElementById('brand-page-industry');
    const rulebookEl = document.getElementById('brand-page-rulebook');

    if (avatarEl) {
      avatarEl.textContent = data.initials || 'BV';
      avatarEl.style.background = data.bg || 'linear-gradient(135deg, #27272a, #3f3f46)';
    }
    if (nameEl) nameEl.textContent = data.name;
    if (industryEl) {
      industryEl.innerHTML = `${data.industry} • Active Rulebook: <strong style="color: #fff;">${data.rulebook}</strong>`;
    }
    if (rulebookEl) rulebookEl.textContent = data.rulebook;

    // 1. Dynamically Render Brand Rulebook Assets & Index
    const rulebookList = document.getElementById('rulebook-items-list');
    if (rulebookList && data.rulebookAssets) {
      rulebookList.innerHTML = '';
      data.rulebookAssets.forEach(item => {
        const row = document.createElement('div');
        row.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);';
        row.innerHTML = `
          <span>${item.icon} <strong>${item.name}</strong> — <em style="color:var(--text-muted);font-size:0.8rem;">${item.meta}</em></span>
          <span class="badge badge-pass">${item.badge}</span>
        `;
        rulebookList.appendChild(row);
      });
    }

    // 2. Dynamically Render Recent Scans & Side-by-Side Diff Comparison
    if (data.recentScan) {
      const scan = data.recentScan;
      const scanTitleEl = document.querySelector('#section-recent h3');
      const scanIdEl = document.querySelector('#section-recent .mono');
      const scanBadgeEl = document.querySelector('#section-recent .badge');
      const origPane = document.getElementById('original-copy-pane');
      const aiPane = document.getElementById('ai-suggested-pane');

      if (scanTitleEl) scanTitleEl.textContent = scan.title;
      if (scanIdEl) scanIdEl.textContent = `ID: ${scan.id}`;
      if (scanBadgeEl) {
        scanBadgeEl.className = `badge ${scan.statusClass || 'badge-fail'}`;
        scanBadgeEl.innerHTML = `<span class="badge-dot"></span>${scan.statusText}`;
      }

      if (origPane) {
        origPane.innerHTML = `
          <div style="font-weight: 700; color: #cbd5e1; font-size: 0.82rem; margin-bottom: 8px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            Original Submitted Copy
          </div>
          <p style="color: #cbd5e1;">${scan.originalCopy}</p>
        `;
      }

      if (aiPane) {
        aiPane.innerHTML = `
          <div style="font-weight: 700; color: #86efac; font-size: 0.82rem; margin-bottom: 8px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            AI Recommended Compliant Copy
          </div>
          <p style="color: #ffffff;">${scan.suggestedCopy}</p>
          <div style="margin-top: 10px; font-size: 0.76rem; color: #94a3b8; border-top: 1px solid var(--border-subtle); padding-top: 6px;">
            ${scan.footnote || ''}
          </div>
        `;
      }

      // Update callout flag boxes
      const flagsContainer = document.querySelector('#section-recent .diff-container + div');
      if (flagsContainer && scan.flags) {
        flagsContainer.innerHTML = '';
        scan.flags.forEach(f => {
          const isCrit = f.type === 'critical';
          const box = document.createElement('div');
          box.style.cssText = isCrit
            ? 'background: var(--review-red-bg); border-left: 3px solid var(--review-red); padding: 10px 14px; border-radius: 4px;'
            : 'background: var(--review-yellow-bg); border-left: 3px solid var(--review-yellow); padding: 10px 14px; border-radius: 4px;';
          box.innerHTML = `<strong style="color: ${isCrit ? 'var(--review-red)' : 'var(--review-yellow)'};">${f.label}:</strong> ${f.text}`;
          flagsContainer.appendChild(box);
        });
      }
    }

    // 3. Update Text Checker sample copy to match brand
    const copyInput = document.getElementById('copy-text-input');
    if (copyInput && data.sampleCopy) {
      copyInput.value = data.sampleCopy;
    }
  },

  switchActiveBrand(brandId) {
    if (!brandId) return;
    this.currentBrandId = brandId;
    const url = new URL(window.location);
    url.searchParams.set('id', brandId);
    window.history.replaceState({}, '', url);
    this.loadBrandPage(brandId);
    Toast.show(`Switched active brand to ${document.getElementById('brand-page-name')?.textContent || brandId}`, 'info');
  },

  // Main 3-section navigation (Rule Book, Compliance Checker, Recent)
  showMainSection(sectionName) {
    const validSections = ['checker', 'rulebook', 'recent'];
    validSections.forEach(sec => {
      const btn = document.getElementById(`sec-btn-${sec}`);
      const panel = document.getElementById(`section-${sec}`);
      if (btn) btn.classList.toggle('active', sec === sectionName);
      if (panel) panel.classList.toggle('active', sec === sectionName);
    });
  },

  // Sub-tab switching inside Compliance Checker (Text, Document, Post & Image, Audio, Video)
  switchCheckerType(type) {
    const types = ['text', 'doc', 'image', 'audio', 'video'];
    types.forEach(t => {
      const btn = document.getElementById(`subtab-btn-${t}`);
      const panel = document.getElementById(`tab-${t}`);
      if (btn) btn.classList.toggle('active', t === type);
      if (panel) panel.classList.toggle('active', t === type);
    });
    this.showMainSection('checker');
  },

  switchCheckerTab(tabId) {
    if (tabId === 'tab-rulebooks' || tabId === 'rulebook') {
      this.showMainSection('rulebook');
    } else {
      const cleanType = tabId.replace('tab-', '');
      this.switchCheckerType(cleanType);
    }
  },

  promptDeleteBrand(brandId, brandName) {
    this.brandToDelete = brandId;
    const modal = document.getElementById('delete-brand-modal');
    const warningText = document.getElementById('delete-brand-warning-text');
    if (warningText) {
      warningText.innerHTML = `Are you sure you want to permanently delete <strong>"${brandName}"</strong>?`;
    }
    if (modal) modal.classList.add('active');
  },

  closeDeleteModal() {
    this.brandToDelete = null;
    const modal = document.getElementById('delete-brand-modal');
    if (modal) modal.classList.remove('active');
  },

  executeDeleteBrand() {
    if (!this.brandToDelete) return;
    const brands = this.getBrands();
    const deletedName = brands[this.brandToDelete]?.name || 'Brand';
    delete brands[this.brandToDelete];
    this.saveBrands(brands);

    const card = document.getElementById(`card-${this.brandToDelete}`);
    if (card) {
      card.style.opacity = '0';
      card.style.transform = 'scale(0.95)';
      card.style.transition = 'all 0.3s ease';
      setTimeout(() => card.remove(), 300);
    }

    this.closeDeleteModal();
    Toast.show(`Brand "${deletedName}" deleted.`, 'info');

    if (window.location.pathname.includes('brand.html')) {
      const firstId = this.getFirstBrandId();
      if (firstId) {
        this.switchActiveBrand(firstId);
      } else {
        window.location.href = 'dashboard.html';
      }
    }
  },

  handleRulebookFiles(e) {
    const files = e.target.files;
    if (!files.length) return;

    const list = document.getElementById('rulebook-items-list');
    if (list) {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const item = document.createElement('div');
        item.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:rgba(255,255,255,0.03); border-radius:6px; border:1px solid rgba(255,255,255,0.08);';
        item.innerHTML = `
          <span>📁 <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB) — <em style="color:var(--text-muted);font-size:0.8rem;">Indexed</em></span>
          <span class="badge badge-brand">Active</span>
        `;
        list.prepend(item);
      }
    }
    Toast.show(`${files.length} guideline asset(s) uploaded and indexed!`, 'success');
  },



async runCheck(e, type) {
  if (e) e.preventDefault();

  const form = e.currentTarget || e.target;

  // Keep the other checker tabs unchanged for now.
  if (type !== 'Text Copy') {
    if (typeof CheckerAPI !== 'undefined') {
      return CheckerAPI.run(form, type, this.currentBrandId || 'acme-tech');
    }
    Toast.show(`${type} checker integration is not connected yet.`, 'info');
    return;
  }

  const title = form.querySelector('input[type="text"]')?.value.trim() || '';
  const targetChannel = form.querySelector('select')?.value || '';
  const customRule = form.querySelector('.custom-rule-input')?.value.trim() || '';
  const rawText = form.querySelector('textarea.form-textarea')?.value.trim() || '';

  if (!title || !rawText) {
    Toast.show('Enter a title and text to scan.', 'error');
    return;
  }

  const button = form.querySelector('button[type="submit"]');
  const oldButtonText = button?.textContent || '';

  if (button) {
    button.disabled = true;
    button.textContent = 'Scanning...';
  }

  Toast.show('Running compliance scan...', 'info');

  try {
    const response = await fetch('/api/v1/verify/text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_id: this.currentBrandId || 'acme-tech',
        content_type: 'text',
        title,
        target_channel: targetChannel,
        custom_rule: customRule || null,
        raw_text: rawText
      })
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }

    // Update the original copy pane.
    const originalPane = document.getElementById('original-copy-pane');
    if (originalPane) {
      originalPane.replaceChildren();

      const heading = document.createElement('div');
      heading.className = 'diff-pane-heading';
      heading.textContent = 'Original Submitted Copy';

      const paragraph = document.createElement('p');
      paragraph.style.color = '#cbd5e1';
      paragraph.style.whiteSpace = 'pre-wrap';
      paragraph.textContent = result.diff?.original_text || rawText;

      originalPane.append(heading, paragraph);
    }

    // Show the rule-based recommended text.
    const suggestedPane = document.getElementById('ai-suggested-pane');
    if (suggestedPane) {
      suggestedPane.replaceChildren();

      const heading = document.createElement('div');
      heading.style.cssText =
        'font-weight:700;color:#86efac;font-size:.82rem;margin-bottom:8px;';
      heading.textContent = 'Recommended Copy (Rule-Based)';

      const paragraph = document.createElement('p');
      paragraph.style.cssText = 'color:#fff;white-space:pre-wrap;line-height:1.7;';
      paragraph.textContent =
        result.diff?.recommended_text || 'No revised copy returned.';

      suggestedPane.append(heading, paragraph);
    }

    // Create or update a section for the AI explanation and findings.
    let resultsPanel = document.getElementById('live-scan-results');

    if (!resultsPanel) {
      resultsPanel = document.createElement('div');
      resultsPanel.id = 'live-scan-results';
      resultsPanel.style.cssText =
        'background:#090a0f;border:1px solid var(--border-subtle);' +
        'border-radius:12px;padding:20px;margin:20px 0;';

      const recentSection = document.getElementById('section-recent');
      const recentCard = recentSection?.querySelector('.card');

      if (recentCard) {
        recentCard.prepend(resultsPanel);
      }
    }

    if (resultsPanel) {
      resultsPanel.replaceChildren();

      const heading = document.createElement('h3');
      heading.textContent = 'Latest Compliance Scan';
      heading.style.marginBottom = '12px';

      const summary = document.createElement('p');
      summary.style.marginBottom = '12px';
      summary.textContent =
        `Status: ${result.overall_status} | Score: ${result.compliance_score}/100 | ` +
        `Findings: ${result.flags.length}`;

      const aiHeading = document.createElement('h4');
      aiHeading.textContent = 'AI Explanation';
      aiHeading.style.margin = '16px 0 8px';

      const explanation = document.createElement('p');
      explanation.style.cssText =
        'white-space:pre-wrap;line-height:1.7;color:#cbd5e1;';
      explanation.textContent =
        result.ai_explanation || 'No AI explanation was returned.';

      const flagsHeading = document.createElement('h4');
      flagsHeading.textContent = 'Detected Findings';
      flagsHeading.style.margin = '18px 0 8px';

      const flagsList = document.createElement('ul');
      flagsList.style.paddingLeft = '22px';

      for (const flag of result.flags || []) {
        const item = document.createElement('li');
        item.style.marginBottom = '12px';

        const titleLine = document.createElement('strong');
        titleLine.textContent =
          `[${String(flag.severity).toUpperCase()}] ${flag.title}`;

        const details = document.createElement('p');
        details.style.cssText =
          'color:#cbd5e1;margin:4px 0;line-height:1.5;';
        details.textContent =
          `${flag.description} Recommended fix: ${flag.recommended_fix}`;

        item.append(titleLine, details);
        flagsList.appendChild(item);
      }

      resultsPanel.append(
        heading,
        summary,
        aiHeading,
        explanation,
        flagsHeading,
        flagsList
      );
    }

    // Add the real scan to the recent-scans table.
    const tbody = document.getElementById('recent-scans-tbody');

    if (tbody) {
      const row = document.createElement('tr');
      row.style.borderBottom = '1px solid var(--border-subtle)';

      const titleCell = document.createElement('td');
      titleCell.style.padding = '14px 18px';
      titleCell.textContent = `${result.title} (${result.scan_id})`;

      const channelCell = document.createElement('td');
      channelCell.style.padding = '14px';
      channelCell.textContent = result.target_channel;

      const scoreCell = document.createElement('td');
      scoreCell.style.padding = '14px';
      scoreCell.textContent = `${result.compliance_score}/100`;

      const actionCell = document.createElement('td');
      actionCell.style.padding = '14px 18px';
      actionCell.style.textAlign = 'right';
      actionCell.textContent = result.overall_status;

      row.append(titleCell, channelCell, scoreCell, actionCell);
      tbody.prepend(row);
    }

    this.showMainSection('recent');

    resultsPanel?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });

    Toast.show('Real compliance results loaded!', 'success');

    console.log('BrandVerify scan result:', result);

  } catch (error) {
    console.error('Text scan failed:', error);
    Toast.show(
      `Scan failed: ${error.message}. Check the backend terminal.`,
      'error'
    );
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = oldButtonText;
    }
  }
},



  openAddBrandModal() {
    const modal = document.getElementById('add-brand-modal');
    if (modal) modal.classList.add('active');
  },

  closeAddBrandModal() {
    const modal = document.getElementById('add-brand-modal');
    if (modal) modal.classList.remove('active');
  },

  addNewBrand(e) {
    if (e) e.preventDefault();
    const name = document.getElementById('new-brand-name')?.value;
    const industry = document.getElementById('new-brand-industry')?.value;
    const rulebook = document.getElementById('new-brand-rulebook')?.value || 'Standard Governance v1.0';

    if (!name) return;

    const brandKey = 'brand-' + Date.now();
    const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

    const brands = this.getBrands();
    brands[brandKey] = {
      id: brandKey,
      name: name,
      initials: initials,
      bg: 'linear-gradient(135deg, #27272a, #3f3f46)',
      industry: industry,
      rulebook: rulebook,
      rulebookText: 'Custom brand guidelines.',
      palettes: '#ffffff, #a1a1aa, #121215'
    };
    this.saveBrands(brands);

    const container = document.getElementById('managed-brands-container');
    const addCard = document.querySelector('.brand-add-card');

    if (container && addCard) {
      const newCard = document.createElement('div');
      newCard.className = 'brand-card';
      newCard.id = `card-${brandKey}`;
      newCard.innerHTML = `
        <div class="brand-card-header">
          <div class="brand-avatar-box" style="background: linear-gradient(135deg, #27272a, #3f3f46);">
            ${initials}
          </div>
          <div>
            <div class="brand-card-title">${name}</div>
            <div class="brand-card-industry">${industry}</div>
          </div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <a href="brand.html?id=${brandKey}" class="btn btn-white btn-sm" style="flex: 1;">
            Manage Brand →
          </a>
          <button type="button" class="btn-icon-danger" onclick="BrandManager.promptDeleteBrand('${brandKey}', '${name}')" title="Delete Brand" aria-label="Delete Brand">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
          </button>
        </div>
      `;
      container.insertBefore(newCard, addCard);
    }

    this.closeAddBrandModal();
    Toast.show(`Brand "${name}" added to managed brands!`, 'success');

    if (window.location.pathname.includes('brand.html')) {
      this.switchActiveBrand(brandKey);
    }
  }
};

// ==========================================================================
// 3. Review Diff Controller (Muted Green/Red/Yellow in Review Checker)
// ==========================================================================
const ReviewDiffController = {
  isEditing: false,

  acceptSuggestions() {
    const originalPane = document.getElementById('original-copy-pane');
    if (originalPane) {
      originalPane.innerHTML = `
        <div style="font-weight: 700; color: var(--review-green); font-size: 0.82rem; margin-bottom: 8px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
          ✓ Revisions Accepted
        </div>
        <p style="color: #ffffff; line-height: 1.8;">
          BrandVerify CloudScale engine is <strong>engineered to deliver up to 10X faster benchmark processing</strong> according to verified Q3 internal lab benchmarks. Seamlessly integrate your multi-tenant asset pipeline with <strong>guaranteed compliance logging</strong>.
        </p>
        <div style="margin-top: 10px; font-size: 0.76rem; color: #a1a1aa; border-top: 1px solid var(--border-subtle); padding-top: 6px;">
          Audited Footnote: <em>Benchmark claims audited by CloudMetrics Labs Q3 2026. Individual performance may vary.</em>
        </div>
      `;
    }
    const scoreMetric = document.getElementById('compliance-score-metric');
    if (scoreMetric) {
      scoreMetric.textContent = '98/100';
      scoreMetric.className = 'review-score-pass';
    }
    Toast.show('AI recommendations accepted! Score updated to 98/100.', 'success');
  },

  toggleInlineEdit() {
    this.isEditing = !this.isEditing;
    const pane = document.getElementById('original-copy-pane');
    const btn = document.getElementById('btn-edit-copy');

    if (pane) {
      pane.contentEditable = this.isEditing ? 'true' : 'false';
      pane.style.outline = this.isEditing ? '2px dashed #ffffff' : 'none';
      if (btn) btn.textContent = this.isEditing ? 'Save Changes' : 'Edit Copy';
      Toast.show(this.isEditing ? 'Inline edit enabled. Edit directly in pane.' : 'Changes saved.', 'info');
    }
  },

  openOverrideModal() {
    const modal = document.getElementById('override-modal');
    if (modal) modal.classList.add('active');
  },

  saveOverride() {
    const modal = document.getElementById('override-modal');
    if (modal) modal.classList.remove('active');
    Toast.show('Override rationale logged to audit vault.', 'info');
  },

  executeOneClickApproval() {
    const modal = document.getElementById('approval-success-modal');
    if (modal) modal.classList.add('active');
  }
};

// ==========================================================================
// 4. Toast Notifications (Monochromatic Pure White Dot)
// ==========================================================================
const Toast = {
  container: null,

  show(message, type = 'info') {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    const dot = document.createElement('span');
    dot.style.cssText = 'color:#ffffff; font-size:0.75rem;';
    dot.textContent = '●';
    const msg = document.createElement('span');
    msg.textContent = message;
    toast.append(dot, msg);
    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
};

// Bootstrap
document.addEventListener('DOMContentLoaded', () => {
  AuthUI.init();
});

const imageForm = document.getElementById("imageScanForm");

if (imageForm) {
    imageForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const file = document.getElementById("imageFile").files[0];
        const colors = document
            .getElementById("approvedColors")
            .value
            .split(",")
            .map(color => color.trim())
            .filter(Boolean);

        const status = document.getElementById("scanStatus");
        const results = document.getElementById("scanResults");

        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("brand_id", "brand_demo");
        formData.append("approved_colors", JSON.stringify(colors));

        status.textContent = "Scanning image...";
        results.replaceChildren();

        try {
            const data = await apiRequest("/api/images/scan", {
                method: "POST",
                body: formData
            });

            status.textContent = "Scan completed.";

            // Display the returned data safely.
            const output = document.createElement("pre");
            output.textContent = JSON.stringify(data, null, 2);
            results.appendChild(output);

        } catch (error) {
            status.textContent = `Scan failed: ${error.message}`;
        }
    });
}

// ==========================================================================
// 5. Audio & Video Compliance Scan Handlers
// ==========================================================================

// Audio Scan Form Handler
const audioForm = document.getElementById("audioScanForm");
if (audioForm) {
    audioForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const fileInput = document.getElementById("audioFile");
        const status = document.getElementById("audioScanStatus") || document.getElementById("scanStatus");
        const results = document.getElementById("audioScanResults") || document.getElementById("scanResults");

        if (!fileInput || !fileInput.files[0]) {
            Toast.show("Please select an audio file.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("target_lufs", "-24.0");
        formData.append("tolerance_lu", "1.0");

        if (status) status.textContent = "Transcribing audio and measuring loudness...";
        if (results) results.replaceChildren();

        try {
            const data = await apiRequest("/api/media/audio/scan", {
                method: "POST",
                body: formData
            });

            if (status) status.textContent = `Audio scan completed (Status: ${data.overall_status}).`;
            Toast.show("Audio compliance check successful!", "success");

            const output = document.createElement("pre");
            output.textContent = JSON.stringify(data, null, 2);
            if (results) results.appendChild(output);

        } catch (error) {
            if (status) status.textContent = `Audio scan failed: ${error.message}`;
            Toast.show(`Audio scan failed: ${error.message}`, "error");
        }
    });
}

// Video Ad Scan Form Handler
const videoForm = document.getElementById("videoScanForm");
if (videoForm) {
    videoForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const fileInput = document.getElementById("videoFile");
        const disclaimerInput = document.getElementById("requiredDisclaimer");
        const status = document.getElementById("videoScanStatus") || document.getElementById("scanStatus");
        const results = document.getElementById("videoScanResults") || document.getElementById("scanResults");

        if (!fileInput || !fileInput.files[0]) {
            Toast.show("Please select a video file.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("required_disclaimer", disclaimerInput ? disclaimerInput.value : "Terms apply");
        formData.append("target_lufs", "-24.0");
        formData.append("tolerance_lu", "1.0");

        if (status) status.textContent = "Analyzing video frames, scene cuts, OCR, and audio track...";
        if (results) results.replaceChildren();

        try {
            const data = await apiRequest("/api/media/video/scan", {
                method: "POST",
                body: formData
            });

            if (status) status.textContent = `Video ad scan completed (Overall Status: ${data.overall_status}).`;
            Toast.show("Video ad compliance check successful!", "success");

            const output = document.createElement("pre");
            output.textContent = JSON.stringify(data, null, 2);
            if (results) results.appendChild(output);

        } catch (error) {
            if (status) status.textContent = `Video scan failed: ${error.message}`;
            Toast.show(`Video scan failed: ${error.message}`, "error");
        }
    });
}