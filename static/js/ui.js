// Global variables for charts
let barChart, sparkChart;

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

// Skeleton loading states
function showSkeleton(on) {
    const skeleton = document.getElementById('skeleton');
    const resultsWrap = document.getElementById('resultsWrap');
    const resultsEmpty = document.getElementById('resultsEmpty');
    
    if (on) {
        skeleton.classList.remove('hidden');
        resultsWrap.classList.add('hidden');
        resultsEmpty.classList.add('hidden');
    } else {
        skeleton.classList.add('hidden');
        resultsWrap.classList.remove('hidden');
        resultsEmpty.classList.add('hidden');
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
    document.getElementById('resultsEmpty').classList.add('hidden');
    document.getElementById('resultsWrap').classList.remove('hidden');
    
    // Extract metrics
    const m = data.metrics || {};
    const juris = (data.entity && data.entity.country) ? [data.entity.country] : [];
    
    // Update KPI tiles
    document.getElementById('kpi-overall').textContent = (m.overall_risk ?? '—').toFixed(3);
    document.getElementById('kpi-sanc').textContent = (m.sanctions ?? '—').toFixed(3);
    document.getElementById('kpi-pep').textContent = (m.pep ?? '—').toFixed(3);
    document.getElementById('kpi-adv').textContent = (m.adverse_media ?? '—').toFixed(3);
    
    // Update secondary KPIs
    document.getElementById('kpi-matches').textContent = m.matches ?? '—';
    document.getElementById('kpi-alerts').textContent = m.alerts ?? '—';
    document.getElementById('kpi-last').textContent = data.ts ? new Date(data.ts).toLocaleString() : '—';
    document.getElementById('kpi-juris').textContent = juris.join(', ') || '—';
    
    // Update AI commentary
    const ai = data.ai_summary || {};
    document.getElementById('ai-comment').textContent = (ai.commentary || 'No AI commentary available.');
    
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
}

// Render individual screening results
function renderIndividualResults(data) {
    // Hide empty state and show results
    document.getElementById('resultsEmpty').classList.add('hidden');
    document.getElementById('resultsWrap').classList.remove('hidden');
    
    // Extract metrics
    const m = data.metrics || {};
    
    // Update KPI tiles
    document.getElementById('kpi-overall').textContent = (m.overall_risk ?? '—').toFixed(3);
    document.getElementById('kpi-sanc').textContent = (m.sanctions ?? '—').toFixed(3);
    document.getElementById('kpi-pep').textContent = (m.pep ?? '—').toFixed(3);
    document.getElementById('kpi-adv').textContent = (m.adverse_media ?? '—').toFixed(3);
    
    // Update secondary KPIs
    document.getElementById('kpi-matches').textContent = m.matches ?? '—';
    document.getElementById('kpi-alerts').textContent = m.alerts ?? '—';
    document.getElementById('kpi-last').textContent = data.ts ? new Date(data.ts).toLocaleString() : '—';
    document.getElementById('kpi-juris').textContent = (data.person && data.person.nationality) || '—';
    
    // Update AI commentary
    document.getElementById('ai-comment').textContent = 'Individual screening completed. Review results above.';
    
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
    
    if (openaiStatus) {
        openaiStatus.style.background = providers.openai ? 'var(--success-500)' : 'var(--danger-500)';
    }
    
    if (dilisenseStatus) {
        dilisenseStatus.style.background = providers.dilisense ? 'var(--success-500)' : 'var(--danger-500)';
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
