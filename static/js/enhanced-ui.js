/**
 * Enhanced UI Components for Risklytics
 * Provides advanced UI functionality and JSON visualization
 */

// Initialize JSON Viewer instances
let jsonViewers = {};

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeComponents();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize JSON viewers for any pre-existing data
    initializeJsonViewers();
    
    // Initialize charts if needed
    if (typeof renderCharts === 'function') {
        renderCharts();
    }
    
    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }
});

// Initialize all UI components
function initializeComponents() {
    // Initialize dropdowns
    initializeDropdowns();
    
    // Initialize tabs
    initializeTabs();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize modals
    initializeModals();
    
    // Initialize collapsible sections
    initializeCollapsibles();
}

// Set up global event listeners
function setupEventListeners() {
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // JSON export buttons
    document.querySelectorAll('.export-json-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const containerId = this.getAttribute('data-container');
            exportJsonData(containerId);
        });
    });
    
    // Copy to clipboard buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const textId = this.getAttribute('data-copy-target');
            copyToClipboard(textId);
        });
    });
    
    // Form submission handling
    const forms = document.querySelectorAll('form[data-ajax="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', handleAjaxForm);
    });
}

// Initialize JSON viewers
function initializeJsonViewers() {
    // Find all JSON containers
    document.querySelectorAll('[data-json-container]').forEach(container => {
        const id = container.id;
        const dataAttr = container.getAttribute('data-json-content');
        
        // Try to get JSON data
        let jsonData;
        try {
            // First try to get from data attribute
            if (dataAttr) {
                jsonData = JSON.parse(dataAttr);
            } 
            // Then try to get from the container's text content
            else if (container.textContent.trim()) {
                jsonData = JSON.parse(container.textContent.trim());
                // Clear the container
                container.textContent = '';
            }
            
            // If we have JSON data, initialize the viewer
            if (jsonData) {
                const viewer = new JSONViewer({
                    collapsed: container.hasAttribute('data-collapsed'),
                    withQuotes: container.hasAttribute('data-with-quotes'),
                    withLinks: !container.hasAttribute('data-no-links')
                });
                
                viewer.render(jsonData, container);
                jsonViewers[id] = viewer;
                
                // Add toolbar if needed
                if (container.hasAttribute('data-with-toolbar')) {
                    addJsonToolbar(container, id, jsonData);
                }
            }
        } catch (e) {
            console.error('Failed to parse JSON for container', id, e);
            container.innerHTML = `<div class="p-4 text-danger-500">Invalid JSON data: ${e.message}</div>`;
        }
    });
}

// Add toolbar to JSON viewer
function addJsonToolbar(container, id, jsonData) {
    // Create toolbar wrapper
    const toolbar = document.createElement('div');
    toolbar.className = 'toolbar';
    
    // Add title
    const title = document.createElement('div');
    title.className = 'toolbar-title';
    title.textContent = container.getAttribute('data-title') || 'JSON Data';
    toolbar.appendChild(title);
    
    // Add actions
    const actions = document.createElement('div');
    actions.className = 'toolbar-actions';
    
    // Add expand/collapse button
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'toolbar-btn';
    toggleBtn.textContent = 'Expand All';
    toggleBtn.addEventListener('click', () => {
        const isExpanded = toggleBtn.textContent === 'Collapse All';
        toggleJsonView(container, !isExpanded);
        toggleBtn.textContent = isExpanded ? 'Expand All' : 'Collapse All';
    });
    actions.appendChild(toggleBtn);
    
    // Add copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'toolbar-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', () => {
        copyJsonToClipboard(jsonData);
    });
    actions.appendChild(copyBtn);
    
    // Add export button
    const exportBtn = document.createElement('button');
    exportBtn.className = 'toolbar-btn';
    exportBtn.textContent = 'Export';
    exportBtn.addEventListener('click', () => {
        exportJsonData(id, jsonData);
    });
    actions.appendChild(exportBtn);
    
    toolbar.appendChild(actions);
    
    // Insert toolbar at the beginning of the container
    container.parentNode.insertBefore(toolbar, container);
}

// Toggle JSON view expansion
function toggleJsonView(container, expand) {
    const toggles = container.querySelectorAll('.json-viewer-toggle');
    toggles.forEach(toggle => {
        const content = toggle.parentElement.nextElementSibling;
        if (expand && content.style.display === 'none') {
            content.style.display = 'block';
            toggle.textContent = '▼';
        } else if (!expand && content.style.display !== 'none') {
            content.style.display = 'none';
            toggle.textContent = '▶';
        }
    });
}

// Copy JSON to clipboard
function copyJsonToClipboard(jsonData) {
    const jsonString = typeof jsonData === 'string' 
        ? jsonData 
        : JSON.stringify(jsonData, null, 2);
    
    navigator.clipboard.writeText(jsonString)
        .then(() => {
            showToast('JSON copied to clipboard', 'success');
        })
        .catch(err => {
            showToast('Failed to copy: ' + err, 'error');
        });
}

// Export JSON data to file
function exportJsonData(id, jsonData) {
    // If jsonData is not provided, try to get it from the viewers
    if (!jsonData && jsonViewers[id]) {
        const container = document.getElementById(id);
        if (container) {
            try {
                jsonData = JSON.parse(container.getAttribute('data-json-content') || container.textContent);
            } catch (e) {
                console.error('Failed to parse JSON for export', e);
                showToast('Failed to export JSON: Invalid data', 'error');
                return;
            }
        }
    }
    
    if (!jsonData) {
        showToast('No data to export', 'error');
        return;
    }
    
    const jsonString = JSON.stringify(jsonData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${id}_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('JSON exported successfully', 'success');
}

// Initialize dropdown menus
function initializeDropdowns() {
    document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
        const trigger = dropdown.querySelector('[data-dropdown-trigger]');
        const menu = dropdown.querySelector('[data-dropdown-menu]');
        
        if (trigger && menu) {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const isOpen = menu.classList.contains('block');
                
                // Close all other dropdowns
                document.querySelectorAll('[data-dropdown-menu].block').forEach(openMenu => {
                    if (openMenu !== menu) {
                        openMenu.classList.remove('block');
                        openMenu.classList.add('hidden');
                    }
                });
                
                // Toggle this dropdown
                menu.classList.toggle('hidden', isOpen);
                menu.classList.toggle('block', !isOpen);
            });
            
            // Close when clicking outside
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target)) {
                    menu.classList.add('hidden');
                    menu.classList.remove('block');
                }
            });
        }
    });
}

// Initialize tabs
function initializeTabs() {
    document.querySelectorAll('[data-tabs]').forEach(tabContainer => {
        const tabs = tabContainer.querySelectorAll('[data-tab]');
        const panels = tabContainer.querySelectorAll('[data-tab-panel]');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-tab');
                
                // Update active tab
                tabs.forEach(t => {
                    t.classList.toggle('active', t === tab);
                });
                
                // Show target panel, hide others
                panels.forEach(panel => {
                    const panelId = panel.getAttribute('data-tab-panel');
                    panel.classList.toggle('hidden', panelId !== target);
                });
            });
        });
    });
}

// Initialize tooltips
function initializeTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip hidden absolute z-50 bg-gray-800 text-white text-xs rounded py-1 px-2 max-w-xs';
        tooltip.textContent = element.getAttribute('data-tooltip');
        document.body.appendChild(tooltip);
        
        element.addEventListener('mouseenter', () => {
            const rect = element.getBoundingClientRect();
            tooltip.classList.remove('hidden');
            tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
        });
        
        element.addEventListener('mouseleave', () => {
            tooltip.classList.add('hidden');
        });
    });
}

// Initialize modals
function initializeModals() {
    document.querySelectorAll('[data-modal-trigger]').forEach(trigger => {
        const modalId = trigger.getAttribute('data-modal-trigger');
        const modal = document.getElementById(modalId);
        
        if (modal) {
            const closeButtons = modal.querySelectorAll('[data-modal-close]');
            
            trigger.addEventListener('click', () => {
                modal.classList.remove('hidden');
                document.body.classList.add('overflow-hidden');
            });
            
            closeButtons.forEach(button => {
                button.addEventListener('click', () => {
                    modal.classList.add('hidden');
                    document.body.classList.remove('overflow-hidden');
                });
            });
            
            // Close when clicking outside the modal content
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                    document.body.classList.remove('overflow-hidden');
                }
            });
        }
    });
}

// Initialize collapsible sections
function initializeCollapsibles() {
    document.querySelectorAll('[data-collapsible]').forEach(collapsible => {
        const trigger = collapsible.querySelector('[data-collapsible-trigger]');
        const content = collapsible.querySelector('[data-collapsible-content]');
        
        if (trigger && content) {
            // Set initial state
            const isOpen = !collapsible.hasAttribute('data-collapsed');
            content.classList.toggle('hidden', !isOpen);
            
            trigger.addEventListener('click', () => {
                const isCurrentlyOpen = !content.classList.contains('hidden');
                content.classList.toggle('hidden');
                
                // Update icon if present
                const icon = trigger.querySelector('[data-collapsible-icon]');
                if (icon) {
                    icon.textContent = isCurrentlyOpen ? '+' : '-';
                }
            });
        }
    });
}

// Toggle theme between light and dark
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');
    
    html.classList.toggle('dark', !isDark);
    html.classList.toggle('light', isDark);
    
    // Save preference
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    
    // Update any theme indicators
    const themeIndicators = document.querySelectorAll('[data-theme-indicator]');
    themeIndicators.forEach(indicator => {
        indicator.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    });
}

// Handle AJAX form submissions
function handleAjaxForm(e) {
    e.preventDefault();
    
    const form = e.target;
    const url = form.action;
    const method = form.method.toUpperCase();
    const formData = new FormData(form);
    
    // Show loading state
    form.classList.add('loading');
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.originalText = submitBtn.textContent;
        submitBtn.textContent = 'Processing...';
    }
    
    // Convert FormData to JSON if needed
    let body;
    if (form.getAttribute('data-format') === 'json') {
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });
        body = JSON.stringify(jsonData);
    } else {
        body = formData;
    }
    
    // Make the request
    fetch(url, {
        method: method,
        body: body,
        headers: form.getAttribute('data-format') === 'json' 
            ? { 'Content-Type': 'application/json' } 
            : {},
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Handle success
        const successEvent = new CustomEvent('form:success', { detail: data });
        form.dispatchEvent(successEvent);
        
        // Show success message if provided
        if (data.message) {
            showToast(data.message, 'success');
        }
        
        // Reset form if needed
        if (form.hasAttribute('data-reset-on-success')) {
            form.reset();
        }
        
        // Redirect if needed
        if (data.redirect) {
            window.location.href = data.redirect;
        }
        
        // Update content if needed
        if (data.updateContent && data.targetId) {
            const target = document.getElementById(data.targetId);
            if (target) {
                target.innerHTML = data.updateContent;
            }
        }
        
        // Update JSON viewer if needed
        if (data.jsonData && data.jsonContainerId) {
            updateJsonViewer(data.jsonContainerId, data.jsonData);
        }
    })
    .catch(error => {
        // Handle error
        console.error('Form submission error:', error);
        
        const errorEvent = new CustomEvent('form:error', { detail: error });
        form.dispatchEvent(errorEvent);
        
        showToast(`Error: ${error.message}`, 'error');
    })
    .finally(() => {
        // Reset loading state
        form.classList.remove('loading');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = submitBtn.dataset.originalText;
        }
    });
}

// Update JSON viewer with new data
function updateJsonViewer(containerId, jsonData) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Store the JSON data as an attribute
    container.setAttribute('data-json-content', JSON.stringify(jsonData));
    
    // Clear the container
    container.innerHTML = '';
    
    // Create a new viewer
    const viewer = new JSONViewer({
        collapsed: container.hasAttribute('data-collapsed'),
        withQuotes: container.hasAttribute('data-with-quotes'),
        withLinks: !container.hasAttribute('data-no-links')
    });
    
    viewer.render(jsonData, container);
    jsonViewers[containerId] = viewer;
}

// Copy text to clipboard
function copyToClipboard(targetId) {
    const target = document.getElementById(targetId);
    if (!target) return;
    
    const text = target.innerText || target.textContent;
    
    navigator.clipboard.writeText(text)
        .then(() => {
            showToast('Copied to clipboard', 'success');
        })
        .catch(err => {
            showToast('Failed to copy: ' + err, 'error');
        });
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        // Create container if it doesn't exist
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        document.body.appendChild(newContainer);
        return showToast(message, type); // Retry
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Add icon based on type
    const iconName = {
        'success': 'check-circle',
        'error': 'alert-circle',
        'warning': 'alert-triangle',
        'info': 'info'
    }[type] || 'info';
    
    const icon = document.createElement('i');
    icon.setAttribute('data-lucide', iconName);
    toast.appendChild(icon);
    
    // Add message
    const messageElem = document.createElement('span');
    messageElem.textContent = message;
    toast.appendChild(messageElem);
    
    container.appendChild(toast);
    
    // Initialize the icon
    if (window.lucide) {
        lucide.createIcons({
            icons: {
                [iconName]: toast.querySelector(`[data-lucide="${iconName}"]`)
            }
        });
    }
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 4000);
}

// Format date strings
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format numbers with commas
function formatNumber(num) {
    if (num === null || num === undefined) return '';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Truncate text with ellipsis
function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Debounce function for performance
function debounce(func, wait = 300) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Export functions for external use
window.risklytics = {
    showToast,
    formatDate,
    formatNumber,
    truncateText,
    updateJsonViewer,
    toggleTheme,
    copyToClipboard,
    exportJsonData
};
