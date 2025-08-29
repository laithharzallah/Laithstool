// Global variables for charts
let barChart, sparkChart;

// Safe numeric formatter
function formatNum(value, digits = 3) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(digits) : '—';
}

// Toast notification system
function toast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const toastEl = document.createElement('div');
    
    // Set toast content and styling
    toastEl.className = 'toast';
    toastEl.textContent = msg;
    
    // Add type-specific styling
    if (type === 'error') {
        toastEl.style.background = 'var(--danger-500)';
        toastEl.style.color = 'white';
    } else if (type === 'success') {
        toastEl.style.background = 'var(--success-500)';
        toastEl.style.color = 'white';
    } else if (type === 'warn') {
        toastEl.style.background = 'var(--warn-500)';
        toastEl.style.color = 'white';
    }
    
    // Add to container
    container.appendChild(toastEl);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (toastEl.parentNode) {
            toastEl.parentNode.removeChild(toastEl);
        }
    }, 3000);
}

// Safe setters
function setTextById(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// Skeleton loading states
function showSkeleton(on) {
    const skeleton = document.getElementById('skeleton');
    const resultsWrap = document.getElementById('resultsWrap');
    const resultsEmpty = document.getElementById('resultsEmpty');
    
    if (on) {
        if (skeleton) skeleton.classList.remove('hidden');
        if (resultsWrap) resultsWrap.classList.add('hidden');
        if (resultsEmpty) resultsEmpty.classList.add('hidden');
    } else {
        if (skeleton) skeleton.classList.add('hidden');
        if (resultsWrap) resultsWrap.classList.remove('hidden');
        if (resultsEmpty) resultsEmpty.classList.add('hidden');
    }
}

// Chart initialization
function ensureCharts() {
    if (!barChart) {
        const barElement = document.getElementById('risk-bar');
        if (barElement) {
            barChart = echarts.init(barElement, null, { renderer: 'svg' });
        }
    }
    
    if (!sparkChart) {
        const sparkElement = document.getElementById('sparkline');
        if (sparkElement) {
            sparkChart = echarts.init(sparkElement, null, { renderer: 'svg' });
        }
    }
}

// Render risk breakdown bar chart
function renderRiskBar({ adverse_media, pep, sanctions, overall_risk }) {
    ensureCharts();
    
    if (!barChart) return;
    
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'var(--bg-2)',
            borderColor: 'var(--border-1)',
            textStyle: {
                color: 'var(--text-0)'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['Overall', 'Adverse Media', 'PEP', 'Sanctions'],
            axisLabel: {
                color: 'var(--text-1)',
                fontSize: 12
            },
            axisLine: {
                lineStyle: {
                    color: 'var(--border-1)'
                }
            }
        },
        yAxis: {
            type: 'value',
            max: 1,
            axisLabel: {
                color: 'var(--text-1)',
                fontSize: 12
            },
            axisLine: {
                lineStyle: {
                    color: 'var(--border-1)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'var(--border-0)'
                }
            }
        },
        series: [{
            type: 'bar',
            data: [overall_risk, adverse_media, pep, sanctions],
            itemStyle: {
                color: function(params) {
                    const colors = ['var(--brand-500)', 'var(--warn-500)', 'var(--accent-500)', 'var(--danger-500)'];
                    return colors[params.dataIndex] || 'var(--brand-500)';
                }
            },
            barWidth: '60%',
            borderRadius: [4, 4, 0, 0]
        }]
    };
    
    barChart.setOption(option);
}

// Render sparkline trend chart
function renderSparkline() {
    ensureCharts();
    
    if (!sparkChart) return;
    
    // Generate sample trend data
    const points = Array.from({ length: 30 }, (_, i) => [i, Math.random() * 0.6 + 0.2]);
    
    const option = {
        backgroundColor: 'transparent',
        grid: {
            left: 0,
            right: 0,
            top: 0,
            bottom: 0
        },
        xAxis: {
            type: 'value',
            show: false
        },
        yAxis: {
            type: 'value',
            show: false,
            max: 1
        },
        series: [{
            type: 'line',
            data: points,
            smooth: true,
            symbol: 'none',
            lineStyle: {
                color: 'var(--brand-500)',
                width: 2
            },
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [{
                        offset: 0,
                        color: 'rgba(62, 166, 255, 0.3)'
                    }, {
                        offset: 1,
                        color: 'rgba(62, 166, 255, 0.05)'
                    }]
                }
            }
        }]
    };
    
    sparkChart.setOption(option);
}

// Render company screening results
function renderCompanyResults(data) {
    // Hide empty state and show results
    const re = document.getElementById('resultsEmpty');
    const rw = document.getElementById('resultsWrap');
    if (re) re.classList.add('hidden');
    if (rw) rw.classList.remove('hidden');
    
    // Extract metrics
    const m = data.metrics || {};
    const juris = (data.entity && data.entity.country) ? [data.entity.country] : [];
    
    // Update KPI tiles
    setTextById('kpi-overall', formatNum(m.overall_risk, 3));
    setTextById('kpi-sanc', formatNum(m.sanctions, 3));
    setTextById('kpi-pep', formatNum(m.pep, 3));
    setTextById('kpi-adv', formatNum(m.adverse_media, 3));
    
    // Update secondary KPIs
    setTextById('kpi-matches', m.matches ?? '—');
    setTextById('kpi-alerts', m.alerts ?? '—');
    setTextById('kpi-last', data.ts ? new Date(data.ts).toLocaleString() : '—');
    setTextById('kpi-juris', juris.join(', ') || '—');
    
    // Update AI commentary
    const ai = data.ai_summary || {};
    setTextById('ai-comment', (ai.commentary || 'No AI commentary available.'));
    
    // Update provider status
    updateProviderStatus(data.providers);
    
    // Render charts
    renderRiskBar({
        adverse_media: m.adverse_media ?? 0,
        pep: m.pep ?? 0,
        sanctions: m.sanctions ?? 0,
        overall_risk: m.overall_risk ?? 0
    });
    renderSparkline();

    // Render web results if present (supports both adapted and raw backend fields)
    try {
        const ws = data.web_search || data.categorized_results || {};
        const cat = ws.categorized_results || ws;
        const ci = (cat.company_info) || {};
        const execs = Array.isArray(cat.executives) ? cat.executives : [];
        const adv = Array.isArray(cat.adverse_media) ? cat.adverse_media : [];

        const ciEl = document.getElementById('web-company-info');
        if (ciEl) {
            const website = ci.website || '—';
            const name = ci.legal_name || '—';
            const industry = ci.industry || '—';
            const founded = ci.founded_year || '—';
            ciEl.innerHTML = `
                <div><strong>Name:</strong> ${name}</div>
                <div><strong>Website:</strong> <a href="${website}" target="_blank" rel="noopener">${website}</a></div>
                <div><strong>Industry:</strong> ${industry}</div>
                <div><strong>Founded:</strong> ${founded}</div>
            `;
        }

        const exEl = document.getElementById('web-executives');
        if (exEl) {
            if (execs.length === 0) exEl.textContent = '—'; else {
                exEl.innerHTML = execs.slice(0, 6).map(e => {
                    const n = e.name || 'Unknown';
                    const p = e.position || '—';
                    const u = e.source_url || e.url || '';
                    return `<div><strong>${n}</strong> — ${p}${u ? ` • <a href="${u}" target="_blank" rel="noopener">source</a>` : ''}</div>`;
                }).join('');
            }
        }

        const adEl = document.getElementById('web-adverse');
        if (adEl) {
            if (adv.length === 0) adEl.textContent = '—'; else {
                adEl.innerHTML = adv.slice(0, 6).map(a => {
                    const h = a.headline || a.title || '—';
                    const s = a.source || a.source_name || '';
                    const d = a.date || a.published_date || '';
                    const u = a.source_url || a.url || '';
                    return `<div><strong>${h}</strong><div class="text-xs">${[s,d].filter(Boolean).join(' • ')}${u ? ` • <a href="${u}" target="_blank" rel="noopener">source</a>` : ''}</div></div>`;
                }).join('');
            }
        }
    } catch (e) {
        console.warn('web results render skipped:', e);
    }
}

// Render individual screening results
function renderIndividualResults(data) {
    // Hide empty state and show results
    const re = document.getElementById('resultsEmpty');
    const rw = document.getElementById('resultsWrap');
    if (re) re.classList.add('hidden');
    if (rw) rw.classList.remove('hidden');
    
    // Extract metrics
    const m = data.metrics || {};
    
    // Update KPI tiles
    setTextById('kpi-overall', formatNum(m.overall_risk, 3));
    setTextById('kpi-sanc', formatNum(m.sanctions, 3));
    setTextById('kpi-pep', formatNum(m.pep, 3));
    setTextById('kpi-adv', formatNum(m.adverse_media, 3));
    
    // Update secondary KPIs
    setTextById('kpi-matches', m.matches ?? '—');
    setTextById('kpi-alerts', m.alerts ?? '—');
    setTextById('kpi-last', data.ts ? new Date(data.ts).toLocaleString() : '—');
    setTextById('kpi-juris', (data.person && data.person.nationality) || '—');
    
    // Update AI commentary
    setTextById('ai-comment', 'Individual screening completed. Review results above.');
    
    // Render charts
    renderRiskBar({
        adverse_media: m.adverse_media ?? 0,
        pep: m.pep ?? 0,
        sanctions: m.sanctions ?? 0,
        overall_risk: m.overall_risk ?? 0
    });
    renderSparkline();
}

// Update provider status indicators
function updateProviderStatus(providers) {
    const openaiStatus = document.getElementById('status-openai');
    const dilisenseStatus = document.getElementById('status-dilisense');
    if (!providers) return;
    if (openaiStatus) {
        const ok = (typeof providers === 'object' && providers.openai === true) ||
                   (Array.isArray(providers) && providers.includes('openai'));
        openaiStatus.style.background = ok ? 'var(--success-500)' : 'var(--danger-500)';
    }
    if (dilisenseStatus) {
        const ok = (typeof providers === 'object' && providers.dilisense === true) ||
                   (Array.isArray(providers) && providers.includes('dilisense'));
        dilisenseStatus.style.background = ok ? 'var(--success-500)' : 'var(--danger-500)';
    }
}

// Export report functionality
async function exportReport() {
    try {
        const response = await fetch('/api/export/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: Date.now(),
                type: 'screening_report'
            })
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `risklytics_report_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        toast('Report exported successfully', 'success');
        
    } catch (error) {
        toast('Export failed: ' + error.message, 'error');
    }
}

// Handle window resize for charts
window.addEventListener('resize', () => {
    if (barChart) {
        barChart.resize();
    }
    if (sparkChart) {
        sparkChart.resize();
    }
});

// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure elements are rendered
    setTimeout(() => {
        ensureCharts();
    }, 100);
});
