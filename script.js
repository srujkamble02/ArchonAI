document.addEventListener('DOMContentLoaded', () => {
  // --- STATE ---
  let lastBackendData = null;

  // --- UI ELEMENTS ---
  const topNavBtns = document.querySelectorAll('.top-nav-btn');
  const viewSections = document.querySelectorAll('.view-section');
  const sideNavLinks = document.querySelectorAll('.sidebar-link');
  const outputTabs = document.querySelectorAll('.output-panel .tab');
  const tabPanes = document.querySelectorAll('.tab-pane');
  
  // Inputs
  const projectDescInput = document.getElementById('project-desc');
  const scaleOverrideInput = document.getElementById('scale-override');
  const cloudProviderInput = document.getElementById('cloud-provider');
  const apiKeyInput = document.getElementById('api-key');
  const quickExamplesSelect = document.getElementById('quick-examples');
  
  // Buttons
  const topGenerateBtn = document.getElementById('top-generate-btn');
  const generateBtn = document.querySelector('.input-panel .btn-primary'); // Side generate btn if exists
  const exportDropdownBtn = document.getElementById('export-dropdown-btn');
  const exportMenu = document.getElementById('export-menu');

  // Export dropdown toggle
  if (exportDropdownBtn && exportMenu) {
    exportDropdownBtn.addEventListener('click', () => {
      exportMenu.style.display = exportMenu.style.display === 'none' ? 'block' : 'none';
    });
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.export-dropdown')) exportMenu.style.display = 'none';
    });
  }
  
  // Output Containers
  const diagramContainer = document.getElementById('diagram-container');
  const architectureTypeEl = document.getElementById('architecture-type');
  const architectureReasonEl = document.getElementById('architecture-reason');
  const costTotalEl = document.getElementById('cost-total');
  const costBasisEl = document.getElementById('cost-basis');
  const costGridEl = document.getElementById('cost-grid');
  const failuresListEl = document.getElementById('failures-list');
  const explanationContentEl = document.getElementById('explanation-content');

  // Terminal
  const terminalInput = document.getElementById('terminal-input');
  const terminalOutput = document.getElementById('terminal-output');

  // Deployment
  const btnMockDeploy = document.getElementById('btn-mock-deploy');
  const deployProgressBar = document.getElementById('deploy-progress-bar');
  const deployProgressText = document.getElementById('deploy-progress-text');
  const deployLogs = document.getElementById('deploy-logs');
  const deployStatus = document.getElementById('deploy-status');
  const deployHealth = document.getElementById('deploy-health');

  // History
  const historyGrid = document.getElementById('history-grid');
  const btnClearHistory = document.getElementById('btn-clear-history');

  // Workforce
  const workforceContainer = document.getElementById('workforce-container');
  const btnAddRole = document.getElementById('btn-add-role');
  const workforceTotalPreview = document.getElementById('workforce-total-preview');
  const workforceTotalValue = document.getElementById('workforce-total-value');
  const workforceCurrency = document.getElementById('workforce-currency');

  // --- UTILS ---
  const formatMoney = (val) => formatINR(val);

  const formatINR = (val) => '₹' + new Intl.NumberFormat('en-IN').format(Math.round(Number(val) || 0));
  const formatCurrency = (val) => formatINR(val);

  const showToast = (message, isError = false) => {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.style.borderLeftColor = isError ? '#ef4444' : 'var(--success)';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
  };

  // --- WORKFORCE ROLES ---
  const ROLE_OPTIONS = [
    "Project Manager", "Software Developers", "Backend Developers", "Frontend Developers",
    "Full Stack Developers", "AI/ML Engineers", "DevOps Engineers", "Cloud Engineers",
    "UI/UX Designers", "QA Engineers", "Testers", "Security Engineers",
    "Data Engineers", "Database Administrators", "Other"
  ];

  const PERIOD_OPTIONS = [
    { value: "hourly", label: "Hourly" },
    { value: "daily", label: "Daily" },
    { value: "monthly", label: "Monthly" },
    { value: "yearly", label: "Yearly" },
  ];

  function addWorkforceRow(defaults = {}) {
    const row = document.createElement('div');
    row.className = 'workforce-row';
    row.innerHTML = `
      <select class="wf-role" title="Role">
        ${ROLE_OPTIONS.map(r => `<option value="${r}" ${defaults.role === r ? 'selected' : ''}>${r}</option>`).join('')}
      </select>
      <input type="number" class="wf-count" placeholder="Qty" min="0" value="${defaults.count || ''}" title="Number of employees">
      <input type="number" class="wf-wage" placeholder="Wage" min="0" value="${defaults.wage || ''}" title="Wage per employee">
      <select class="wf-period" title="Period">
        ${PERIOD_OPTIONS.map(p => `<option value="${p.value}" ${defaults.period === p.value ? 'selected' : ''}>${p.label}</option>`).join('')}
      </select>
      <button type="button" class="btn-remove-role" title="Remove role">✕</button>
    `;

    // Remove button
    row.querySelector('.btn-remove-role').addEventListener('click', () => {
      row.remove();
      updateWorkforcePreview();
    });

    // Live preview on change
    ['wf-count', 'wf-wage', 'wf-period'].forEach(cls => {
      const el = row.querySelector('.' + cls);
      el.addEventListener('input', updateWorkforcePreview);
      el.addEventListener('change', updateWorkforcePreview);
    });

    workforceContainer.appendChild(row);
    updateWorkforcePreview();
  }

  function updateWorkforcePreview() {
    const rows = workforceContainer.querySelectorAll('.workforce-row');
    if (rows.length === 0) {
      workforceTotalPreview.style.display = 'none';
      return;
    }

    let total = 0;
    rows.forEach(row => {
      const count = parseInt(row.querySelector('.wf-count').value) || 0;
      const wage = parseFloat(row.querySelector('.wf-wage').value) || 0;
      const period = row.querySelector('.wf-period').value;

      let monthly = wage;
      if (period === 'hourly') monthly = wage * 8 * 22;
      else if (period === 'daily') monthly = wage * 22;
      else if (period === 'yearly') monthly = wage / 12;

      total += monthly * count;
    });

    workforceTotalPreview.style.display = 'block';
    workforceTotalValue.textContent = formatINR(total);
  }

  if (btnAddRole) {
    btnAddRole.addEventListener('click', () => addWorkforceRow({ period: 'monthly' }));
  }

  if (workforceCurrency) {
    workforceCurrency.addEventListener('change', updateWorkforcePreview);
  }

  function getWorkforceConfig() {
    const rows = workforceContainer.querySelectorAll('.workforce-row');
    const config = [];
    rows.forEach(row => {
      const role = row.querySelector('.wf-role').value;
      const count = parseInt(row.querySelector('.wf-count').value) || 0;
      const wage = parseFloat(row.querySelector('.wf-wage').value) || 0;
      const period = row.querySelector('.wf-period').value;
      if (count > 0 && wage > 0) {
        config.push({ role, count, wage, period });
      }
    });
    return config;
  }

  // --- VIEW ROUTING ---
  function switchView(viewName) {
    topNavBtns.forEach(btn => {
      if (btn.getAttribute('data-view') === viewName) btn.classList.add('active');
      else btn.classList.remove('active');
    });

    viewSections.forEach(section => {
      if (section.id === `view-${viewName}`) {
        section.style.display = 'flex';
      } else {
        section.style.display = 'none';
      }
    });

    if (viewName === 'history') {
      loadHistory();
    }
  }

  topNavBtns.forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.getAttribute('data-view')));
  });

  // --- TAB ROUTING ---
  function switchTab(tabTarget) {
    switchView('generator');

    outputTabs.forEach(t => {
      if (t.getAttribute('data-tab') === tabTarget) t.classList.add('active');
      else t.classList.remove('active');
    });

    tabPanes.forEach(p => {
      if (p.id === `tab-${tabTarget}`) p.style.display = 'flex';
      else p.style.display = 'none';
    });

    sideNavLinks.forEach(l => {
      if (l.getAttribute('data-target') === tabTarget) l.classList.add('active');
      else l.classList.remove('active');
    });
  }

  sideNavLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(link.getAttribute('data-target'));
    });
  });

  outputTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      switchTab(tab.getAttribute('data-tab'));
    });
  });

  // Quick Examples Handling
  if (quickExamplesSelect) {
    quickExamplesSelect.addEventListener('change', (e) => {
      if (e.target.value) projectDescInput.value = e.target.value;
    });
  }

  // --- GENERATION PIPELINE ---
  async function runPipeline() {
    const projectDesc = projectDescInput.value.trim();
    if (!projectDesc) {
      showToast("Please enter a project description.", true);
      return;
    }
    
    // UI State Loading
    const originalText = topGenerateBtn ? topGenerateBtn.textContent : 'Generate';
    if (topGenerateBtn) { topGenerateBtn.textContent = 'Generating...'; topGenerateBtn.disabled = true; }
    if (generateBtn) { generateBtn.textContent = 'Generating...'; generateBtn.disabled = true; }
    
    diagramContainer.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;"><div class="dot" style="margin-bottom:1rem;width:12px;height:12px;"></div><p style="color:var(--primary);">Running architecture pipeline...</p></div>';
    
    try {
      const workforceConfig = getWorkforceConfig();
      const response = await fetch('http://localhost:8000/generate-architecture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_description: projectDesc,
          scale_override: scaleOverrideInput.value || null,
          cloud_provider: cloudProviderInput.value,
          anthropic_api_key: apiKeyInput.value || null,
          workforce_config: workforceConfig.length > 0 ? workforceConfig : null,
          workforce_currency: 'INR',
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      data.original_description = projectDesc;
      data.scale_override = scaleOverrideInput.value || 'Auto-detect';
      data.cloud_provider = cloudProviderInput.value || 'AWS';
      lastBackendData = data;
      
      if (exportDropdownBtn) {
        exportDropdownBtn.disabled = false;
        exportDropdownBtn.style.opacity = '1';
        exportDropdownBtn.style.cursor = 'pointer';
        exportDropdownBtn.classList.add('glow-effect');
      }
      
      populateUI(data);
      saveToHistory({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        description: projectDesc,
        data: data
      });
      
      showToast(`Architecture generated in ${data.elapsed_ms || 120}ms`);
      switchTab('diagram');
      
    } catch (error) {
      console.error("Error generating architecture:", error);
      diagramContainer.innerHTML = `<p style="color: #ef4444;">Error: ${error.message}</p>`;
      architectureTypeEl.textContent = 'Error';
      architectureReasonEl.textContent = 'Failed to generate architecture.';
      showToast(`Failed: ${error.message}`, true);
    } finally {
      if (topGenerateBtn) { topGenerateBtn.textContent = originalText; topGenerateBtn.disabled = false; }
      if (generateBtn) { generateBtn.textContent = originalText; generateBtn.disabled = false; }
    }
  }

  if (topGenerateBtn) topGenerateBtn.addEventListener('click', runPipeline);
  if (generateBtn) generateBtn.addEventListener('click', runPipeline);

  // --- POPULATE UI ---
  function populateUI(data) {
    if (!data) return;

    // 1. Architecture & Blueprint
    if (data.architecture) {
      architectureTypeEl.textContent = data.architecture.architecture || 'Unknown Architecture';
      architectureReasonEl.textContent = data.architecture.reason || 'No specific rationale provided.';

      const stackEl = document.getElementById('blueprint-stack');
      const intEl = document.getElementById('blueprint-integrations');
      const secEl = document.getElementById('blueprint-security');
      
      if (data.architecture.components && stackEl) {
        stackEl.innerHTML = `
          <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
            <tr style="border-bottom: 1px solid var(--border-light); color: var(--primary);">
              <th style="padding: 0.8rem; text-align: left;">Layer</th>
              <th style="padding: 0.8rem; text-align: left;">Technology</th>
              <th style="padding: 0.8rem; text-align: left;">Role</th>
            </tr>
            ${data.architecture.components.map(c => `
              <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 0.8rem; font-weight: 600; color: var(--text-main);">${c.layer}</td>
                <td style="padding: 0.8rem; font-family: 'JetBrains Mono', monospace; color: var(--secondary);">${c.tech}</td>
                <td style="padding: 0.8rem; color: var(--text-muted);">${c.role}</td>
              </tr>
            `).join('')}
          </table>
        `;
      }
      
      if (data.architecture.integrations && intEl) intEl.innerHTML = data.architecture.integrations.map(i => `<li style="margin-bottom:0.4rem;"><strong>${i.name}</strong>: <span style="color:var(--text-muted);">${i.purpose}</span></li>`).join('');
      if (data.architecture.security && secEl) secEl.innerHTML = data.architecture.security.map(s => `<li style="margin-bottom:0.4rem; color:var(--text-muted);">${s}</li>`).join('');
    }
    
    // 2. Jenkins / DevOps Pipeline
    populateJenkins(data);
    
    // 3. Cost
    if (data.cost) {
      costTotalEl.textContent = formatMoney(data.cost.total_monthly);
      costBasisEl.textContent = data.cost.note || '';
      
      const costItems = [
        { label: 'Compute', val: data.cost.compute },
        { label: 'Database', val: data.cost.database },
        { label: 'Storage', val: data.cost.storage },
        { label: 'Messaging', val: data.cost.messaging },
        { label: 'Networking', val: data.cost.networking },
        { label: 'Monitoring', val: data.cost.monitoring }
      ];
      
      if (data.cost.ai_serving > 0) costItems.push({ label: 'AI Serving', val: data.cost.ai_serving });
      if (data.cost.iot > 0) costItems.push({ label: 'IoT', val: data.cost.iot });
      
      costGridEl.innerHTML = costItems.map(c => `
        <div class="cost-card-mini">
          <div class="val">${formatMoney(c.val)}</div>
          <div class="lbl">${c.label}</div>
        </div>
      `).join('');
    }

    // Workforce Cost
    populateWorkforceCost(data);

    // Total Cost
    populateTotalCost(data);
    
    // 4. Failures (enhanced with solutions)
    populateFailures(data);

    // 5. Explanation
    if (data.explanation) {
      explanationContentEl.innerHTML = `<p>${data.explanation.replace(/\n/g, '<br>')}</p>`;
    } else {
      explanationContentEl.innerHTML = '<p style="color: var(--text-muted)">No explanation returned. Did you provide an Anthropic API Key?</p>';
    }

    // 6. Diagram
    if (data.diagrams && data.diagrams.svg) {
      diagramContainer.innerHTML = data.diagrams.svg;
      const svgElement = diagramContainer.querySelector('svg');
      if (svgElement) {
        svgElement.style.width = '100%';
        svgElement.style.height = 'auto';
        svgElement.style.maxHeight = '100%';
      }
    } else if (data.diagrams && data.diagrams.mermaid) {
      diagramContainer.innerHTML = `<pre style="text-align:left; font-size: 12px; font-family: monospace; overflow: auto; padding: 1rem; width: 100%; height: 100%; color: var(--text-main);">${data.diagrams.mermaid}</pre>`;
    } else {
      diagramContainer.innerHTML = '<p>No diagram generated.</p>';
    }

    // 7. Recommendations
    populateRecommendations(data);
  }

  // --- JENKINS POPULATION ---
  function populateJenkins(data) {
    const jenkins = data.jenkins_pipeline;
    if (!jenkins) return;

    // Justification
    const justEl = document.getElementById('jenkins-justification');
    if (justEl && jenkins.justification) {
      justEl.innerHTML = `
        <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:0.5rem;">${jenkins.justification.summary}</p>
        <div style="font-size:0.8rem; color:var(--text-muted);">
          <strong style="color:var(--text-main);">Deployment Target:</strong> ${jenkins.deployment_target || 'N/A'}
          <span style="margin:0 0.5rem;">|</span>
          <strong style="color:var(--text-main);">Language:</strong> ${jenkins.primary_language || 'N/A'}
          <span style="margin:0 0.5rem;">|</span>
          <strong style="color:var(--text-main);">Docker:</strong> ${jenkins.uses_docker ? '✔' : '✘'}
          <span style="margin:0 0.5rem;">|</span>
          <strong style="color:var(--text-main);">Kubernetes:</strong> ${jenkins.uses_kubernetes ? '✔' : '✘'}
        </div>
      `;
    }

    // Stages
    const stagesEl = document.getElementById('jenkins-stages');
    if (stagesEl && jenkins.stages) {
      stagesEl.innerHTML = jenkins.stages.map((s, i) => `
        <div class="jenkins-stage">
          <div class="jenkins-stage-number">${i + 1}</div>
          <div class="jenkins-stage-content">
            <div class="jenkins-stage-name">${s.name}</div>
            <div class="jenkins-stage-desc">${s.description}</div>
            <div class="jenkins-stage-tools">
              ${(s.tools || []).map(t => `<span class="jenkins-tool-chip">${t}</span>`).join('')}
            </div>
          </div>
        </div>
      `).join('');
    }

    // Jenkinsfile
    const codeEl = document.getElementById('jenkinsfile-code');
    if (codeEl && jenkins.jenkinsfile) {
      codeEl.textContent = jenkins.jenkinsfile;
    }

    // Copy button
    const copyBtn = document.getElementById('btn-copy-jenkinsfile');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(jenkins.jenkinsfile || '').then(() => {
          copyBtn.textContent = 'Copied!';
          setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
        });
      });
    }

    // Rollback
    const rollbackEl = document.getElementById('jenkins-rollback');
    if (rollbackEl && jenkins.rollback_strategy) {
      rollbackEl.innerHTML = jenkins.rollback_strategy.map(r => `
        <div class="rollback-item">
          <div class="rollback-method">${r.method}</div>
          <div class="rollback-desc">${r.description}</div>
          <div class="rollback-rto">RTO: ${r.rto}</div>
        </div>
      `).join('');
    }

    // Monitoring
    const monEl = document.getElementById('jenkins-monitoring');
    if (monEl && jenkins.monitoring) {
      const m = jenkins.monitoring;
      monEl.innerHTML = `
        <div style="margin-bottom:0.8rem;">
          <strong style="color:var(--text-main); font-size:0.8rem;">Health Checks</strong>
          <ul style="padding-left:1rem; margin-top:0.3rem; font-size:0.8rem; color:var(--text-muted);">
            ${(m.health_checks || []).map(h => `<li>${h}</li>`).join('')}
          </ul>
        </div>
        <div style="margin-bottom:0.8rem;">
          <strong style="color:var(--text-main); font-size:0.8rem;">Alerting</strong>
          <ul style="padding-left:1rem; margin-top:0.3rem; font-size:0.8rem; color:var(--text-muted);">
            ${(m.alerting || []).map(a => `<li>${a}</li>`).join('')}
          </ul>
        </div>
        <div style="font-size:0.75rem; color:var(--success); margin-top:0.5rem;">
          <strong>Auto-Rollback:</strong> ${m.auto_rollback_trigger || 'N/A'}
        </div>
      `;
    }

    // Alternatives
    const altEl = document.getElementById('jenkins-alternatives');
    if (altEl && jenkins.alternatives) {
      altEl.innerHTML = jenkins.alternatives.map(alt => `
        <div class="rec-option-card alternative" style="margin-bottom:0.8rem;">
          <div class="rec-option-name">${alt.name}</div>
          <div class="rec-option-desc">${alt.category || ''}</div>
          <div class="rec-pros-cons">
            <div class="pros">
              <strong style="color:#10b981; font-size:0.72rem;">✔ Advantages</strong>
              <ul>${(alt.advantages || []).map(a => `<li>${a}</li>`).join('')}</ul>
            </div>
            <div class="cons">
              <strong style="color:#f87171; font-size:0.72rem;">✘ Disadvantages</strong>
              <ul>${(alt.disadvantages || []).map(d => `<li>${d}</li>`).join('')}</ul>
            </div>
          </div>
          <div class="rec-meta" style="margin-top:0.5rem;">
            <span class="rec-meta-chip">Cost: ${alt.estimated_cost || 'N/A'}</span>
            <span class="rec-meta-chip">Best for: ${alt.best_for || 'N/A'}</span>
          </div>
        </div>
      `).join('');
    }
  }

  // --- WORKFORCE COST POPULATION ---
  function populateWorkforceCost(data) {
    const wfSection = document.getElementById('workforce-cost-section');
    const wfBreakdown = document.getElementById('workforce-cost-breakdown');
    if (!wfSection || !wfBreakdown) return;

    const wf = data.workforce_cost;
    if (!wf || !wf.configured) {
      wfSection.style.display = 'none';
      return;
    }

    wfSection.style.display = 'block';
    wfBreakdown.innerHTML = `
      <p style="font-size:0.82rem; color:var(--text-muted); margin-bottom:0.5rem;">${wf.summary || ''}</p>
      <table class="wf-cost-table">
        <thead>
          <tr>
            <th>Role</th>
            <th>Count</th>
            <th>Wage</th>
            <th>Period</th>
            <th>Monthly/Employee</th>
            <th>Monthly Total</th>
          </tr>
        </thead>
        <tbody>
          ${wf.roles.filter(r => r.count > 0).map(r => `
            <tr>
              <td>${r.role}</td>
              <td>${r.count}</td>
              <td>${formatINR(r.wage)}</td>
              <td style="text-transform:capitalize;">${r.period}</td>
              <td>${formatINR(r.monthly_per_employee)}</td>
              <td style="color:var(--primary); font-weight:600;">${formatINR(r.monthly_total)}</td>
            </tr>
          `).join('')}
          <tr class="total-row">
            <td colspan="4"><strong>Total Workforce Cost</strong></td>
            <td>${wf.total_employees || 0} employees</td>
            <td>${formatINR(wf.total_monthly)}/mo</td>
          </tr>
        </tbody>
      </table>
      <p style="font-size:0.7rem; color:var(--text-muted); margin-top:0.5rem;">
        Yearly estimate: <strong>${formatINR(wf.total_yearly)}</strong>
      </p>
    `;
  }

  // --- TOTAL COST POPULATION ---
  function populateTotalCost(data) {
    const section = document.getElementById('total-cost-section');
    const breakdown = document.getElementById('total-cost-breakdown');
    if (!section || !breakdown) return;

    const tc = data.total_cost;
    if (!tc) { section.style.display = 'none'; return; }

    section.style.display = 'block';

    const infra = tc.infrastructure_cost || {};
    const wf = tc.workforce_cost || {};
    const combined = tc.combined || {};

    breakdown.innerHTML = `
      <div class="total-cost-grid">
        <div class="total-cost-card">
          <div class="tc-label">Infrastructure (Monthly)</div>
          <div class="tc-value">${formatMoney(infra.monthly)}</div>
        </div>
        <div class="total-cost-card">
          <div class="tc-label">Workforce (Monthly)</div>
          <div class="tc-value">${formatINR(wf.monthly)}</div>
        </div>
        ${combined.monthly !== undefined ? `
        <div class="total-cost-card grand-total">
          <div class="tc-label">Combined Monthly</div>
          <div class="tc-value">${formatINR(combined.monthly)}</div>
        </div>
        ` : `
        <div class="total-cost-card">
          <div class="tc-label">Note</div>
          <div style="font-size:0.75rem; color:var(--text-muted); padding:0.3rem;">${combined.note || 'Combined after centralized INR conversion.'}</div>
        </div>
        `}
      </div>
    `;
  }

  // --- ENHANCED FAILURES POPULATION ---
  function populateFailures(data) {
    if (!data.failures || data.failures.length === 0) {
      failuresListEl.innerHTML = '<p style="color: var(--text-muted)">No major failure scenarios detected.</p>';
      return;
    }

    // Best strategy summary
    const bestStrategyEl = document.getElementById('best-strategy-summary');
    const bestStrategyContent = document.getElementById('best-strategy-content');
    if (bestStrategyEl && bestStrategyContent) {
      const strategies = data.failures
        .filter(f => f.best_strategy)
        .map(f => `<strong>${f.scenario}:</strong> ${f.best_strategy.strategy}`)
        .slice(0, 3);
      
      if (strategies.length > 0) {
        bestStrategyEl.style.display = 'block';
        bestStrategyContent.innerHTML = strategies.map(s => `<p style="font-size:0.82rem; color:var(--text-muted); margin-bottom:0.4rem;">${s}</p>`).join('');
      }
    }

    failuresListEl.innerHTML = data.failures.map((f, idx) => {
      const impact = (f.impact || 'medium').toLowerCase();
      const solutions = f.solutions || [];
      const containerId = `solutions-${idx}`;

      let solutionsHtml = '';
      if (solutions.length > 0) {
        solutionsHtml = `
          <button class="failure-solutions-toggle" onclick="document.getElementById('${containerId}').classList.toggle('open'); this.textContent = this.textContent.includes('Show') ? 'Hide ${solutions.length} Solutions ▴' : 'Show ${solutions.length} Solutions ▾';">
            Show ${solutions.length} Solutions ▾
          </button>
          <div id="${containerId}" class="failure-solutions-container">
            ${solutions.map(s => {
              const rankClass = s.rank <= 2 ? 'top' : s.rank <= 4 ? 'mid' : 'low';
              return `
                <div class="solution-card">
                  <div class="solution-rank ${rankClass}">#${s.rank}</div>
                  <div>
                    <div class="solution-name">${s.name} ${s.recommendation_status === 'Recommended' ? '<span class="solution-chip recommended-chip">Recommended</span>' : ''}</div>
                    <div class="solution-desc">${s.description}</div>
                    <div class="solution-meta">
                      <span class="solution-chip effectiveness">Effectiveness: ${s.recovery_effectiveness}</span>
                      <span class="solution-chip complexity">Complexity: ${s.complexity}</span>
                      <span class="solution-chip cost">Cost: ${s.cost_impact}</span>
                    </div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `;
      }

      return `
        <div class="failure-item ${impact}">
          <div class="failure-item-header">
            <div class="failure-item-title">${f.scenario}</div>
            <div class="failure-badge">${f.impact}</div>
          </div>
          <p><strong>Trigger:</strong> ${f.trigger || 'N/A'}</p>
          <p><strong>Mitigation:</strong> ${f.mitigation}</p>
          ${f.detection ? `<p><strong>Detection:</strong> ${f.detection}</p>` : ''}
          ${f.best_strategy ? `<p style="color:var(--success); font-size:0.8rem; margin-top:0.4rem;"><strong>Best Strategy:</strong> ${f.best_strategy.strategy}</p>` : ''}
          ${solutionsHtml}
        </div>
      `;
    }).join('');
  }

  // --- RECOMMENDATIONS POPULATION ---
  function populateRecommendations(data) {
    const recs = data.recommendations;
    if (!recs) return;

    // Archon summary
    const summaryEl = document.getElementById('rec-summary-content');
    if (summaryEl && recs.archon_recommendation) {
      summaryEl.innerHTML = `<p style="font-size:0.85rem; color:var(--text-main); line-height:1.6;">${recs.archon_recommendation.summary || ''}</p>`;
    }

    // Architecture options
    renderOptionCards('rec-architecture-options', recs.architecture_options, (opt) => `
      <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.3rem;"><strong>Reason:</strong> ${opt.reason || ''}</p>
      <div class="rec-meta">
        <span class="rec-meta-chip">Cost: ${opt.estimated_cost || 'N/A'}</span>
        <span class="rec-meta-chip">Scalability: ${opt.scalability || 'N/A'}</span>
        <span class="rec-meta-chip">Complexity: ${opt.complexity || 'N/A'}</span>
      </div>
    `);

    // Tech stack options
    renderOptionCards('rec-techstack-options', recs.tech_stack_options, (opt) => `
      <div style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.4rem;">
        ${opt.frontend ? `<strong>Frontend:</strong> ${opt.frontend}<br>` : ''}
        ${opt.backend ? `<strong>Backend:</strong> ${opt.backend}<br>` : ''}
        ${opt.database ? `<strong>Database:</strong> ${opt.database}<br>` : ''}
        ${opt.ai_ml ? `<strong>AI/ML:</strong> ${opt.ai_ml}<br>` : ''}
      </div>
      <p style="font-size:0.75rem; color:var(--text-muted);"><strong>Reason:</strong> ${opt.reason || ''}</p>
    `);

    // Database options
    renderOptionCards('rec-database-options', recs.database_options, (opt) => `
      <div style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.3rem;">
        <strong>Type:</strong> ${opt.type || 'N/A'}
      </div>
      <div class="rec-meta">
        <span class="rec-meta-chip">Best for: ${opt.best_for || 'N/A'}</span>
        <span class="rec-meta-chip">Scalability: ${opt.scalability || 'N/A'}</span>
      </div>
    `);

    // Cloud options
    renderOptionCards('rec-cloud-options', recs.cloud_options, (opt) => `
      <p style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.3rem;">
        <strong>Key Services:</strong> ${opt.key_services || 'N/A'}
      </p>
      <p style="font-size:0.72rem; color:var(--text-muted);">
        <strong>Best for:</strong> ${opt.best_for || 'N/A'}
      </p>
    `);

    // DevOps options
    renderOptionCards('rec-devops-options', recs.devops_options, (opt) => `
      <div class="rec-meta">
        <span class="rec-meta-chip">Cost: ${opt.estimated_cost || 'N/A'}</span>
        <span class="rec-meta-chip">Scalability: ${opt.scalability || 'N/A'}</span>
        <span class="rec-meta-chip">Complexity: ${opt.complexity || 'N/A'}</span>
      </div>
    `);
  }

  function renderOptionCards(containerId, options, extraHtmlFn) {
    const container = document.getElementById(containerId);
    if (!container || !options || options.length === 0) return;

    container.innerHTML = options.map(opt => {
      const labelClass = (opt.label || '').toLowerCase();
      return `
        <div class="rec-option-card ${labelClass}">
          <span class="rec-badge ${labelClass}">Option ${opt.option_number} — ${opt.label}</span>
          <div class="rec-option-name">${opt.name}</div>
          <div class="rec-option-desc">${opt.description || ''}</div>
          ${(opt.advantages || opt.disadvantages) ? `
          <div class="rec-pros-cons">
            ${opt.advantages ? `<div class="pros"><strong style="color:#10b981; font-size:0.72rem;">✔ Advantages</strong><ul>${opt.advantages.map(a => `<li>${a}</li>`).join('')}</ul></div>` : ''}
            ${opt.disadvantages ? `<div class="cons"><strong style="color:#f87171; font-size:0.72rem;">✘ Disadvantages</strong><ul>${opt.disadvantages.map(d => `<li>${d}</li>`).join('')}</ul></div>` : ''}
          </div>` : ''}
          ${extraHtmlFn ? extraHtmlFn(opt) : ''}
        </div>
      `;
    }).join('');
  }

  // --- TERMINAL SYSTEM ---
  function appendTerminal(text, color="var(--text-main)", isCommand=false) {
    const div = document.createElement('div');
    div.style.color = color;
    div.innerHTML = isCommand ? `<span style="color:var(--primary);"> guest@archon:~$</span> ${text}` : text;
    terminalOutput.appendChild(div);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
  }

  async function simulateTerminalTyping(lines, color="var(--text-muted)") {
    for (const line of lines) {
      await new Promise(r => setTimeout(r, 200 + Math.random() * 300));
      appendTerminal(line, color);
    }
  }

  if (terminalInput) {
    terminalInput.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        const cmd = terminalInput.value.trim();
        if (!cmd) return;
        terminalInput.value = '';
        appendTerminal(cmd, "var(--text-bright)", true);
        
        if (cmd === 'help') {
          appendTerminal("Available commands: <br>- help: Show this message<br>- clear: Clear terminal<br>- archon build --prompt \"...\": Generate architecture<br>- archon status: Show system status", "var(--secondary)");
        } else if (cmd === 'clear') {
          terminalOutput.innerHTML = '';
        } else if (cmd === 'archon status') {
          appendTerminal("Engine v2.0.4 - Status: OPTIMAL. Uptime: 24h 12m. Connected to localhost:8000.", "var(--success)");
        } else if (cmd.startsWith('archon build')) {
          appendTerminal("Initiating build pipeline...", "var(--primary)");
          await simulateTerminalTyping([
            "[1/4] Parsing requirements...",
            "[2/4] Generating component stack...",
            "[3/4] Rendering diagram...",
            "[4/4] Estimating cost..."
          ]);
          projectDescInput.value = cmd.replace('archon build', '').replace('--prompt', '').replace(/"/g, '').trim() || "Terminal build test";
          await runPipeline();
          appendTerminal(`Build complete. Total monthly cost: ${costTotalEl.textContent}. Switch to Core Engine view to see diagrams.`, "var(--success)");
        } else {
          appendTerminal(`Command not found: ${cmd}. Type 'help' for available commands.`, "#ef4444");
        }
      }
    });
  }

  // --- DEPLOYMENT DASHBOARD ---
  if (btnMockDeploy) {
    btnMockDeploy.addEventListener('click', async () => {
      btnMockDeploy.disabled = true;
      deployStatus.textContent = 'DEPLOYING';
      deployStatus.style.color = '#eab308'; // Yellow
      deployHealth.textContent = 'PROVISIONING';
      deployHealth.style.color = '#eab308';
      
      deployLogs.innerHTML = '> Starting deployment sequence...<br>';
      
      const steps = [
        { progress: 20, log: "> Allocating cloud resources (VPCs, Subnets)..." },
        { progress: 40, log: "> Provisioning Kubernetes cluster..." },
        { progress: 60, log: "> Pulling Docker images from registry..." },
        { progress: 80, log: "> Applying Helm charts..." },
        { progress: 95, log: "> Running health checks..." },
        { progress: 100, log: "> Deployment successful. Traffic routing to new instances." }
      ];

      for (const step of steps) {
        await new Promise(r => setTimeout(r, 1000 + Math.random() * 800));
        deployProgressBar.style.width = `${step.progress}%`;
        deployProgressText.textContent = `Deploying... ${step.progress}%`;
        deployLogs.innerHTML += `${step.log}<br>`;
        deployLogs.scrollTop = deployLogs.scrollHeight;
      }

      deployStatus.textContent = 'SUCCESS';
      deployStatus.style.color = 'var(--success)';
      deployHealth.textContent = 'HEALTHY';
      deployHealth.style.color = 'var(--success)';
      btnMockDeploy.textContent = 'Deployed';
      showToast("Deployment successful!");
    });
  }

  // --- HISTORY SYSTEM ---
  function saveToHistory(entry) {
    let history = JSON.parse(localStorage.getItem('archon_history') || '[]');
    history.unshift(entry); // Add to beginning
    if (history.length > 20) history = history.slice(0, 20); // Keep last 20
    localStorage.setItem('archon_history', JSON.stringify(history));
    if (document.getElementById('view-history').style.display === 'flex') loadHistory();
  }

  function loadHistory() {
    if (!historyGrid) return;
    const history = JSON.parse(localStorage.getItem('archon_history') || '[]');
    
    if (history.length === 0) {
      historyGrid.innerHTML = '<p style="color: var(--text-muted);">No history found. Generate an architecture first.</p>';
      return;
    }
    
    historyGrid.innerHTML = history.map(item => {
      const date = new Date(item.timestamp).toLocaleString();
      const cost = item.data?.cost?.total_monthly ? formatINR(item.data.cost.total_monthly) : 'N/A';
      return `
        <div class="history-card" data-id="${item.id}">
          <h3>${item.data?.architecture?.architecture || 'Architecture Build'}</h3>
          <p>${item.description || 'No description'}</p>
          <div class="history-meta">
            <span>${date}</span>
            <span>${cost}/mo</span>
          </div>
        </div>
      `;
    }).join('');

    // Add click listeners
    document.querySelectorAll('.history-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-id');
        const item = history.find(h => h.id === id);
        if (item) {
          projectDescInput.value = item.description;
          lastBackendData = item.data;
          populateUI(item.data);
          if (exportDropdownBtn) {
            exportDropdownBtn.disabled = false;
            exportDropdownBtn.style.opacity = '1';
          }
          switchView('generator');
          showToast('Loaded architecture from history');
        }
      });
    });
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener('click', () => {
      localStorage.removeItem('archon_history');
      loadHistory();
      showToast('History cleared');
    });
  }

  // --- EXPORT SYSTEM ---
  window.exportDiagram = function(type) {
    if (!lastBackendData || !lastBackendData.diagrams || !lastBackendData.diagrams.svg) {
      showToast("No diagram available to export", true);
      return;
    }
    const svgStr = lastBackendData.diagrams.svg;
    
    if (type === 'svg') {
      const blob = new Blob([svgStr], { type: 'image/svg+xml' });
      triggerDownload(blob, `architecture_${Date.now()}.svg`);
    } else if (type === 'png') {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      const svg = new Blob([svgStr], {type: 'image/svg+xml;charset=utf-8'});
      const url = URL.createObjectURL(svg);
      
      img.onload = function() {
        canvas.width = img.width * 2; // High res
        canvas.height = img.height * 2;
        ctx.scale(2, 2);
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        canvas.toBlob(blob => {
          triggerDownload(blob, `architecture_${Date.now()}.png`);
        });
      };
      img.src = url;
    } else if (type === 'pdf') {
      if (typeof window.jspdf === 'undefined') {
        return showToast("PDF generation library not loaded yet", true);
      }
      try {
        const doc = new window.jspdf.jsPDF();
        doc.setFontSize(16);
        doc.text("Architecture Diagram", 10, 15);
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        const svg = new Blob([svgStr], {type: 'image/svg+xml;charset=utf-8'});
        const url = URL.createObjectURL(svg);
        
        img.onload = function() {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0);
          URL.revokeObjectURL(url);
          
          const imgData = canvas.toDataURL('image/png');
          const pdfWidth = doc.internal.pageSize.getWidth() - 20;
          const ratio = canvas.width / canvas.height;
          const pdfHeight = pdfWidth / ratio;
          
          doc.addImage(imgData, 'PNG', 10, 25, pdfWidth, pdfHeight);
          doc.save(`architecture_${Date.now()}.pdf`);
          showToast(`Downloaded architecture_${Date.now()}.pdf`);
        };
        img.src = url;
      } catch(e) {
        showToast("Error generating PDF", true);
        console.error(e);
      }
    }
  };

  window.exportReport = function(format) {
    if (!lastBackendData) {
      showToast("No report data to export", true);
      return;
    }
    
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(lastBackendData, null, 2)], { type: 'application/json' });
      triggerDownload(blob, `report_${Date.now()}.json`);
    } else if (format === 'html') {
      const html = buildFullHtmlReport(lastBackendData);
      const blob = new Blob([html], { type: 'text/html' });
      triggerDownload(blob, `archon_report_${Date.now()}.html`);
    } else if (format === 'md') {
      const md = buildMarkdownReport(lastBackendData);
      const blob = new Blob([md], { type: 'text/markdown' });
      triggerDownload(blob, `archon_report_${Date.now()}.md`);
    } else if (format === 'pdf') {
      if (typeof window.jspdf === 'undefined') return showToast("PDF library not loaded", true);
      try {
        const doc = new window.jspdf.jsPDF();
        let y = 15;
        doc.setFontSize(20);
        doc.text("AI System Architecture Report", 10, y); y += 15;
        
        if (lastBackendData.architecture) {
          doc.setFontSize(14); doc.setFont(undefined, 'bold');
          doc.text("Architecture Decision:", 10, y); y += 8;
          doc.setFontSize(12); doc.setFont(undefined, 'normal');
          doc.text(lastBackendData.architecture.architecture, 10, y); y += 8;
          const lines = doc.splitTextToSize(lastBackendData.architecture.reason || '', 180);
          doc.text(lines, 10, y); y += (lines.length * 6) + 10;
        }
        
        if (lastBackendData.cost) {
          doc.setFontSize(14); doc.setFont(undefined, 'bold');
          doc.text("Cost Breakdown:", 10, y); y += 8;
          doc.setFontSize(12); doc.setFont(undefined, 'normal');
          doc.text(`${formatINR(lastBackendData.cost.total_monthly)} / month`, 10, y); y += 10;
        }

        // Workforce cost
        if (lastBackendData.workforce_cost && lastBackendData.workforce_cost.configured) {
          const wf = lastBackendData.workforce_cost;
          if (y > 240) { doc.addPage(); y = 20; }
          doc.setFontSize(14); doc.setFont(undefined, 'bold');
          doc.text("Workforce Cost:", 10, y); y += 8;
          doc.setFontSize(10); doc.setFont(undefined, 'normal');
          doc.text(`${formatINR(wf.total_monthly)} / month (${wf.total_employees} employees)`, 10, y); y += 10;
        }

        // Jenkins
        if (lastBackendData.jenkins_pipeline) {
          if (y > 240) { doc.addPage(); y = 20; }
          doc.setFontSize(14); doc.setFont(undefined, 'bold');
          doc.text("Jenkins CI/CD Pipeline:", 10, y); y += 8;
          doc.setFontSize(10); doc.setFont(undefined, 'normal');
          (lastBackendData.jenkins_pipeline.stages || []).forEach(s => {
            if (y > 270) { doc.addPage(); y = 20; }
            doc.text(`• ${s.name}`, 10, y); y += 5;
          });
          y += 5;
        }

        if (lastBackendData.failures && lastBackendData.failures.length > 0) {
          if (y > 250) { doc.addPage(); y = 20; }
          doc.setFontSize(14); doc.setFont(undefined, 'bold');
          doc.text("Failure Analysis:", 10, y); y += 8;
          doc.setFontSize(10); doc.setFont(undefined, 'normal');
          lastBackendData.failures.forEach(f => {
            if (y > 270) { doc.addPage(); y = 20; }
            doc.setFont(undefined, 'bold');
            doc.text(`${f.scenario} (${f.impact})`, 10, y); y += 5;
            doc.setFont(undefined, 'normal');
            const ml = doc.splitTextToSize(f.mitigation || '', 180);
            doc.text(ml, 10, y); y += (ml.length * 5) + 5;
          });
        }
        
        doc.save(`archon_report_${Date.now()}.pdf`);
        showToast(`Downloaded report PDF`);
      } catch(e) {
        showToast("Error generating PDF", true);
        console.error(e);
      }
    }
  };

  function buildMarkdownReport(data) {
    let md = `# Archon AI — System Architecture Report\n\n`;
    md += `Generated: ${new Date().toLocaleString()}\n\n`;

    if (data.architecture) {
      md += `## Architecture Decision\n**${data.architecture.architecture}**\n\n${data.architecture.reason}\n\n`;
    }

    // Recommendations
    if (data.recommendations) {
      md += `## Recommendations\n\n`;
      if (data.recommendations.archon_recommendation) {
        md += `${data.recommendations.archon_recommendation.summary}\n\n`;
      }
      if (data.recommendations.architecture_options) {
        md += `### Architecture Options\n`;
        data.recommendations.architecture_options.forEach(o => {
          md += `- **${o.name}** (${o.label}): ${o.description || ''}\n`;
        });
        md += `\n`;
      }
    }

    if (data.cost) {
      md += `## Infrastructure Cost\n**Total Monthly:** ${formatINR(data.cost.total_monthly)}\n_${data.cost.note || ''}_\n\n`;
    }

    if (data.workforce_cost && data.workforce_cost.configured) {
      const wf = data.workforce_cost;
      md += `## Workforce Cost\n**Total Monthly:** ${formatINR(wf.total_monthly)} (${wf.total_employees} employees)\n\n`;
      md += `| Role | Count | Monthly Total |\n|------|-------|---------------|\n`;
      wf.roles.filter(r => r.count > 0).forEach(r => {
        md += `| ${r.role} | ${r.count} | ${formatINR(r.monthly_total)} |\n`;
      });
      md += `\n`;
    }

    if (data.jenkins_pipeline) {
      md += `## Jenkins CI/CD Pipeline\n`;
      (data.jenkins_pipeline.stages || []).forEach((s, i) => {
        md += `${i + 1}. **${s.name}**: ${s.description}\n`;
      });
      md += `\n`;
    }

    if (data.failures && data.failures.length > 0) {
      md += `## Failure Analysis\n`;
      data.failures.forEach(f => {
        md += `### ${f.scenario} (${f.impact})\n`;
        md += `- **Trigger:** ${f.trigger || 'N/A'}\n`;
        md += `- **Mitigation:** ${f.mitigation}\n`;
        if (f.best_strategy) md += `- **Best Strategy:** ${f.best_strategy.strategy}\n`;
        if (f.solutions && f.solutions.length > 0) {
          md += `\n**Solutions:**\n`;
          f.solutions.forEach(s => {
            md += `  ${s.rank}. **${s.name}** — ${s.description} (Effectiveness: ${s.recovery_effectiveness}, Complexity: ${s.complexity})\n`;
          });
        }
        md += `\n`;
      });
    }

    return md;
  }

  function buildFullHtmlReport(data) {
    const inp = data.input || {};
    const f   = data.features || {};
    const a   = data.architecture || {};
    const c   = data.cost || {};
    const archName = a.architecture || 'Unknown';
    const fmt = v => formatINR(v);

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archon AI — System Design Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap');
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',sans-serif;background:#0a0c10;color:#f0f4f8;padding:2rem;line-height:1.7;font-size:15px}
  .container{max-width:960px;margin:0 auto}
  h1{font-size:2rem;color:#00e5ff;margin-bottom:.25rem}
  h2{font-size:1.2rem;color:#00e5ff;margin:0 0 1rem;padding-bottom:.4rem;border-bottom:1px solid rgba(0,229,255,.2)}
  h3{font-size:.95rem;color:#8b9bb4;margin:1rem 0 .5rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
  .meta{color:#8b9bb4;font-size:.85rem;margin-bottom:2rem}
  .section{background:rgba(16,20,30,.8);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:1.5rem;margin-bottom:1.5rem}
  .section.accent-blue{border-left:3px solid #00e5ff}
  .section.accent-purple{border-left:3px solid #8b5cf6}
  .section.accent-green{border-left:3px solid #10b981}
  .section.accent-red{border-left:3px solid #ef4444}
  .section.accent-orange{border-left:3px solid #f97316}
  table{width:100%;border-collapse:collapse;font-size:.875rem;margin-top:.5rem}
  th{padding:.6rem .8rem;text-align:left;color:#8b9bb4;border-bottom:1px solid rgba(255,255,255,.1);font-weight:600}
  td{padding:.6rem .8rem;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:top}
  code{font-family:'JetBrains Mono',monospace;color:#00e5ff;font-size:.82rem;background:rgba(0,229,255,.08);padding:.1rem .3rem;border-radius:3px}
  ul{margin-left:1.2rem} li{margin-bottom:.35rem;color:#c8d3e0}
  .cost-total{font-family:'JetBrains Mono',monospace;font-size:1.8rem;color:#00e5ff;font-weight:700}
  pre{background:#05070a;padding:1rem;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:.8rem;color:#a78bfa;overflow-x:auto;white-space:pre-wrap;word-break:break-word;border:1px solid rgba(139,92,246,.3)}
  .badge{display:inline-block;padding:.15rem .55rem;border-radius:12px;font-size:.72rem;font-weight:600;text-transform:uppercase}
  .badge-rec{background:rgba(0,229,255,.15);color:#00e5ff;border:1px solid rgba(0,229,255,.3)}
  .badge-alt{background:rgba(139,92,246,.15);color:#a78bfa;border:1px solid rgba(139,92,246,.3)}
</style>
</head>
<body>
<div class="container">
  <h1>⚡ Archon AI — System Design Report</h1>
  <p class="meta">Generated ${new Date().toLocaleString()} | Cloud: ${inp.cloud_provider || 'AWS'} | Pipeline: rule-based + optional LLM</p>

  <div class="section accent-blue">
    <h2>1. Architecture Decision</h2>
    <p><strong style="color:#00e5ff;font-size:1.1rem">${archName}</strong></p>
    <p style="margin-top:0.5rem;color:#c8d3e0">${a.reason || ''}</p>
  </div>

  ${data.recommendations ? `
  <div class="section accent-purple">
    <h2>2. Multi-Option Recommendations</h2>
    ${data.recommendations.archon_recommendation ? `<p style="color:#c8d3e0;margin-bottom:1rem">${data.recommendations.archon_recommendation.summary}</p>` : ''}
    ${(data.recommendations.architecture_options || []).map(o => `
      <div style="background:rgba(0,0,0,.2);border-radius:6px;padding:1rem;margin-bottom:.5rem;border-left:3px solid ${o.label==='Recommended'?'#00e5ff':'#8b5cf6'}">
        <span class="badge ${o.label==='Recommended'?'badge-rec':'badge-alt'}">${o.label}</span>
        <strong style="color:#f0f4f8;display:block;margin:.3rem 0">${o.name}</strong>
        <p style="color:#8b9bb4;font-size:.85rem">${o.description || ''}</p>
      </div>
    `).join('')}
  </div>` : ''}

  <div class="section accent-green">
    <h2>3. Infrastructure Cost</h2>
    <div class="cost-total">${fmt(c.total_monthly)} <span style="font-size:1rem;color:#8b9bb4">/ month</span></div>
    ${(c.breakdown || []).map(b => `<p style="font-size:.85rem;color:#c8d3e0">• ${b.label}: <code>${fmt(b.cost)}</code> — ${b.description}</p>`).join('')}
  </div>

  ${data.workforce_cost && data.workforce_cost.configured ? `
  <div class="section accent-orange">
    <h2>4. Workforce / HR Cost</h2>
    <p style="color:#c8d3e0;margin-bottom:.5rem">${data.workforce_cost.summary}</p>
    <table>
      <tr><th>Role</th><th>Count</th><th>Monthly/Employee</th><th>Monthly Total</th></tr>
      ${data.workforce_cost.roles.filter(r=>r.count>0).map(r => `
        <tr><td>${r.role}</td><td>${r.count}</td><td>${formatINR(r.monthly_per_employee)}</td><td style="color:#00e5ff;font-weight:600">${formatINR(r.monthly_total)}</td></tr>
      `).join('')}
      <tr style="border-top:2px solid rgba(0,229,255,.3)"><td colspan="3"><strong>Total</strong></td><td style="color:#00e5ff;font-weight:700">${formatINR(data.workforce_cost.total_monthly)}/mo</td></tr>
    </table>
  </div>` : ''}

  ${data.jenkins_pipeline ? `
  <div class="section accent-purple">
    <h2>5. Jenkins CI/CD Pipeline</h2>
    <p style="color:#c8d3e0;margin-bottom:.5rem">${data.jenkins_pipeline.justification?.summary || ''}</p>
    <h3>Pipeline Stages</h3>
    <ol style="margin-left:1.2rem">
      ${(data.jenkins_pipeline.stages || []).map(s => `<li style="margin-bottom:.4rem"><strong style="color:#f0f4f8">${s.name}</strong><br><span style="color:#8b9bb4;font-size:.82rem">${s.description}</span></li>`).join('')}
    </ol>
    <h3>Generated Jenkinsfile</h3>
    <pre>${data.jenkins_pipeline.jenkinsfile || ''}</pre>
  </div>` : ''}

  <div class="section accent-red">
    <h2>6. Failure Analysis & Recovery</h2>
    ${(data.failures || []).map(fail => `
      <div style="background:rgba(0,0,0,.2);border-left:3px solid ${fail.impact==='Critical'?'#ef4444':fail.impact==='High'?'#f97316':'#eab308'};border-radius:0 6px 6px 0;padding:1rem;margin-bottom:.75rem">
        <strong style="color:#f0f4f8">${fail.scenario}</strong> <span class="badge" style="background:rgba(255,255,255,.05);color:#8b9bb4;margin-left:.5rem">${fail.impact}</span>
        <p style="font-size:.85rem;color:#8b9bb4;margin-top:.3rem"><strong>Mitigation:</strong> ${fail.mitigation}</p>
        ${fail.best_strategy ? `<p style="font-size:.82rem;color:#10b981;margin-top:.3rem"><strong>Best Strategy:</strong> ${fail.best_strategy.strategy}</p>` : ''}
        ${(fail.solutions || []).length > 0 ? `
          <h3 style="margin-top:.8rem">Recovery Solutions (Ranked)</h3>
          <table>
            <tr><th>#</th><th>Solution</th><th>Effectiveness</th><th>Complexity</th><th>Status</th></tr>
            ${fail.solutions.map(s => `
              <tr>
                <td>${s.rank}</td>
                <td><strong style="color:#f0f4f8">${s.name}</strong><br><span style="color:#8b9bb4;font-size:.8rem">${s.description}</span></td>
                <td style="color:#10b981">${s.recovery_effectiveness}</td>
                <td style="color:#eab308">${s.complexity}</td>
                <td>${s.recommendation_status === 'Recommended' ? '<span style="color:#00e5ff">✔ Recommended</span>' : '<span style="color:#8b9bb4">Optional</span>'}</td>
              </tr>
            `).join('')}
          </table>
        ` : ''}
      </div>
    `).join('')}
  </div>

  ${data.explanation ? `
  <div class="section accent-blue">
    <h2>7. AI Explanation</h2>
    <p style="color:#c8d3e0;line-height:1.7">${data.explanation.replace(/\n/g, '<br>')}</p>
  </div>` : ''}

  <hr style="border:none;border-top:1px solid rgba(255,255,255,.06);margin:2rem 0">
  <p style="text-align:center;color:#6b7280;font-size:.8rem">Generated by <strong>Archon AI</strong> — rule-based architecture engine | For reference only.</p>
</div>
</body>
</html>`;
  }

  window.exportSection = function(section, format) {
    if (!lastBackendData) {
      showToast("No data available to export", true);
      return;
    }
    
    if (section === 'cost' && format === 'csv') {
      if (!lastBackendData.cost) return showToast("No cost data", true);
      let csv = "Component,Monthly Cost (INR)\n";
      csv += `Compute,${formatINR(lastBackendData.cost.compute)}\n`;
      csv += `Database,${formatINR(lastBackendData.cost.database)}\n`;
      csv += `Storage,${formatINR(lastBackendData.cost.storage)}\n`;
      csv += `Messaging,${formatINR(lastBackendData.cost.messaging)}\n`;
      csv += `Networking,${formatINR(lastBackendData.cost.networking)}\n`;
      csv += `Monitoring,${formatINR(lastBackendData.cost.monitoring)}\n`;
      csv += `Total,${formatINR(lastBackendData.cost.total_monthly)}\n`;
      
      if (lastBackendData.workforce_cost && lastBackendData.workforce_cost.configured) {
        csv += `\nWorkforce Cost\nRole,Count,Monthly Total (INR)\n`;
        lastBackendData.workforce_cost.roles.filter(r => r.count > 0).forEach(r => {
          csv += `${r.role},${r.count},${formatINR(r.monthly_total)}\n`;
        });
        csv += `Total Workforce,,${formatINR(lastBackendData.workforce_cost.total_monthly)}\n`;
      }

      const blob = new Blob([csv], { type: 'text/csv' });
      triggerDownload(blob, `cost_report_${Date.now()}.csv`);
    } else if (section === 'failures' && format === 'txt') {
      if (!lastBackendData.failures || !lastBackendData.failures.length) return showToast("No failure data", true);
      let txt = "FAILURE LOGS & MITIGATION\n=========================\n\n";
      lastBackendData.failures.forEach(f => {
        txt += `SCENARIO: ${f.scenario}\n`;
        txt += `IMPACT: ${f.impact}\n`;
        txt += `MITIGATION: ${f.mitigation}\n`;
        if (f.best_strategy) txt += `BEST STRATEGY: ${f.best_strategy.strategy}\n`;
        if (f.solutions && f.solutions.length > 0) {
          txt += `SOLUTIONS:\n`;
          f.solutions.forEach(s => {
            txt += `  #${s.rank} ${s.name} (${s.recovery_effectiveness}) — ${s.description}\n`;
          });
        }
        txt += `-------------------------\n`;
      });
      const blob = new Blob([txt], { type: 'text/plain' });
      triggerDownload(blob, `failures_${Date.now()}.txt`);
    } else if (section === 'explanation' && format === 'md') {
      if (!lastBackendData.explanation) return showToast("No explanation data", true);
      const md = `# AI Explanation\n\n${lastBackendData.explanation}`;
      const blob = new Blob([md], { type: 'text/markdown' });
      triggerDownload(blob, `explanation_${Date.now()}.md`);
    }
  };

  function triggerDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${filename}`);
  }

});
