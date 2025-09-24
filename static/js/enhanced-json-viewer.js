/**
 * Enhanced JSON Viewer with Tables and Visualization
 * 
 * This component provides a professional visualization of JSON data
 * with support for tables, charts, and structured views.
 */

class EnhancedJsonViewer {
    constructor(options = {}) {
        this.options = {
            container: null,
            data: null,
            theme: 'dark',
            expandLevel: 1,
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.options.container) {
            console.error('Container element is required');
            return;
        }
        
        this.render();
    }
    
    render() {
        const container = this.options.container;
        container.innerHTML = '';
        
        if (!this.options.data) {
            container.innerHTML = '<div class="json-viewer-error">No data available</div>';
            return;
        }
        
        // Add theme class to container
        container.classList.add(`json-viewer-${this.options.theme}`);
        
        // Create the main structure
        const mainElement = document.createElement('div');
        mainElement.className = 'json-viewer-main';
        
        // Process the data based on its type
        if (this.isCompanyData(this.options.data)) {
            mainElement.appendChild(this.renderCompanyData(this.options.data));
        } else if (this.isIndividualData(this.options.data)) {
            mainElement.appendChild(this.renderIndividualData(this.options.data));
        } else if (this.isDartData(this.options.data)) {
            mainElement.appendChild(this.renderDartData(this.options.data));
        } else {
            // Generic JSON rendering
            mainElement.appendChild(this.renderGenericJson(this.options.data));
        }
        
        container.appendChild(mainElement);
    }
    
    isCompanyData(data) {
        // Check if the data has company-specific fields
        return data && data.company_name && data.executives;
    }
    
    isIndividualData(data) {
        // Check if the data has individual-specific fields
        return data && data.name && data.pep_status !== undefined;
    }
    
    isDartData(data) {
        // Check if the data has DART-specific fields
        return data && data.registry_id && data.documents;
    }
    
    renderCompanyData(data) {
        const fragment = document.createDocumentFragment();
        
        // Create company header
        const header = document.createElement('div');
        header.className = 'json-viewer-header';
        
        const companyName = document.createElement('h2');
        companyName.textContent = data.company_name;
        header.appendChild(companyName);
        
        const riskBadge = document.createElement('div');
        riskBadge.className = `risk-badge risk-${data.overall_risk_level.toLowerCase()}`;
        riskBadge.textContent = data.overall_risk_level;
        header.appendChild(riskBadge);
        
        fragment.appendChild(header);
        
        // Create company summary
        const summary = document.createElement('div');
        summary.className = 'json-viewer-summary';
        
        const summaryTable = document.createElement('table');
        summaryTable.className = 'json-viewer-table';
        
        const summaryRows = [
            { label: 'Country', value: data.country || 'N/A' },
            { label: 'Industry', value: data.industry || 'N/A' },
            { label: 'Founded', value: data.founded_year || 'N/A' },
            { label: 'Headquarters', value: data.headquarters || 'N/A' },
            { label: 'Website', value: data.website || 'N/A' }
        ];
        
        summaryRows.forEach(row => {
            const tr = document.createElement('tr');
            
            const th = document.createElement('th');
            th.textContent = row.label;
            tr.appendChild(th);
            
            const td = document.createElement('td');
            td.textContent = row.value;
            tr.appendChild(td);
            
            summaryTable.appendChild(tr);
        });
        
        summary.appendChild(summaryTable);
        fragment.appendChild(summary);
        
        // Create risk metrics
        if (data.metrics) {
            const metrics = document.createElement('div');
            metrics.className = 'json-viewer-metrics';
            
            const metricsTitle = document.createElement('h3');
            metricsTitle.textContent = 'Risk Metrics';
            metrics.appendChild(metricsTitle);
            
            const metricsContainer = document.createElement('div');
            metricsContainer.className = 'metrics-container';
            
            const createMetricCard = (label, value, type) => {
                const card = document.createElement('div');
                card.className = `metric-card ${type}`;
                
                const valueElement = document.createElement('div');
                valueElement.className = 'metric-value';
                valueElement.textContent = value;
                card.appendChild(valueElement);
                
                const labelElement = document.createElement('div');
                labelElement.className = 'metric-label';
                labelElement.textContent = label;
                card.appendChild(labelElement);
                
                return card;
            };
            
            metricsContainer.appendChild(createMetricCard('Sanctions', data.metrics.sanctions || 0, 'sanctions'));
            metricsContainer.appendChild(createMetricCard('Adverse Media', data.metrics.adverse_media || 0, 'adverse-media'));
            metricsContainer.appendChild(createMetricCard('Alerts', data.metrics.alerts || 0, 'alerts'));
            
            metrics.appendChild(metricsContainer);
            fragment.appendChild(metrics);
        }
        
        // Create executives section
        if (data.executives && data.executives.length > 0) {
            const executives = document.createElement('div');
            executives.className = 'json-viewer-section';
            
            const executivesTitle = document.createElement('h3');
            executivesTitle.textContent = 'Key Executives';
            executives.appendChild(executivesTitle);
            
            const executivesTable = document.createElement('table');
            executivesTable.className = 'json-viewer-table';
            
            // Create header row
            const headerRow = document.createElement('tr');
            ['Name', 'Position', 'Risk Level'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            executivesTable.appendChild(headerRow);
            
            // Create data rows
            data.executives.forEach(exec => {
                const tr = document.createElement('tr');
                
                const nameTd = document.createElement('td');
                nameTd.textContent = exec.name;
                tr.appendChild(nameTd);
                
                const positionTd = document.createElement('td');
                positionTd.textContent = exec.position;
                tr.appendChild(positionTd);
                
                const riskTd = document.createElement('td');
                const riskSpan = document.createElement('span');
                riskSpan.className = `risk-indicator risk-${exec.risk_level.toLowerCase()}`;
                riskSpan.textContent = exec.risk_level;
                riskTd.appendChild(riskSpan);
                tr.appendChild(riskTd);
                
                executivesTable.appendChild(tr);
            });
            
            executives.appendChild(executivesTable);
            fragment.appendChild(executives);
        }
        
        // Create risk assessment section
        if (data.risk_assessment) {
            const riskAssessment = document.createElement('div');
            riskAssessment.className = 'json-viewer-section';
            
            const riskTitle = document.createElement('h3');
            riskTitle.textContent = 'Risk Assessment';
            riskAssessment.appendChild(riskTitle);
            
            const riskText = document.createElement('p');
            riskText.textContent = data.risk_assessment;
            riskAssessment.appendChild(riskText);
            
            fragment.appendChild(riskAssessment);
        }
        
        // Create ownership structure if available from real data
        if (data.real_data && data.real_data.ownership_structure) {
            const ownership = document.createElement('div');
            ownership.className = 'json-viewer-section';
            
            const ownershipTitle = document.createElement('h3');
            ownershipTitle.textContent = 'Ownership Structure';
            ownership.appendChild(ownershipTitle);
            
            const ownershipTable = document.createElement('table');
            ownershipTable.className = 'json-viewer-table';
            
            // Create header row
            const headerRow = document.createElement('tr');
            ['Shareholder', 'Ownership'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            ownershipTable.appendChild(headerRow);
            
            // Create data rows
            data.real_data.ownership_structure.forEach(owner => {
                const tr = document.createElement('tr');
                
                const nameTd = document.createElement('td');
                nameTd.textContent = owner.name;
                tr.appendChild(nameTd);
                
                const percentageTd = document.createElement('td');
                percentageTd.textContent = owner.percentage;
                tr.appendChild(percentageTd);
                
                ownershipTable.appendChild(tr);
            });
            
            ownership.appendChild(ownershipTable);
            fragment.appendChild(ownership);
        }
        
        return fragment;
    }
    
    renderIndividualData(data) {
        const fragment = document.createDocumentFragment();
        
        // Create individual header
        const header = document.createElement('div');
        header.className = 'json-viewer-header';
        
        const name = document.createElement('h2');
        name.textContent = data.name;
        header.appendChild(name);
        
        const riskBadge = document.createElement('div');
        riskBadge.className = `risk-badge risk-${data.overall_risk_level.toLowerCase()}`;
        riskBadge.textContent = data.overall_risk_level;
        header.appendChild(riskBadge);
        
        fragment.appendChild(header);
        
        // Create individual summary
        const summary = document.createElement('div');
        summary.className = 'json-viewer-summary';
        
        const summaryTable = document.createElement('table');
        summaryTable.className = 'json-viewer-table';
        
        const summaryRows = [
            { label: 'Country', value: data.country || 'N/A' },
            { label: 'Date of Birth', value: data.date_of_birth || 'N/A' },
            { label: 'PEP Status', value: data.pep_status ? 'Yes' : 'No' }
        ];
        
        summaryRows.forEach(row => {
            const tr = document.createElement('tr');
            
            const th = document.createElement('th');
            th.textContent = row.label;
            tr.appendChild(th);
            
            const td = document.createElement('td');
            td.textContent = row.value;
            tr.appendChild(td);
            
            summaryTable.appendChild(tr);
        });
        
        summary.appendChild(summaryTable);
        fragment.appendChild(summary);
        
        // Create PEP details if available
        if (data.pep_status && data.pep_details) {
            const pepDetails = document.createElement('div');
            pepDetails.className = 'json-viewer-section';
            
            const pepTitle = document.createElement('h3');
            pepTitle.textContent = 'PEP Details';
            pepDetails.appendChild(pepTitle);
            
            const pepTable = document.createElement('table');
            pepTable.className = 'json-viewer-table';
            
            const pepRows = [
                { label: 'Position', value: data.pep_details.position || 'N/A' },
                { label: 'Country', value: data.pep_details.country || 'N/A' },
                { label: 'Since', value: data.pep_details.since || 'N/A' },
                { label: 'Source', value: data.pep_details.source || 'N/A' }
            ];
            
            pepRows.forEach(row => {
                const tr = document.createElement('tr');
                
                const th = document.createElement('th');
                th.textContent = row.label;
                tr.appendChild(th);
                
                const td = document.createElement('td');
                td.textContent = row.value;
                tr.appendChild(td);
                
                pepTable.appendChild(tr);
            });
            
            pepDetails.appendChild(pepTable);
            fragment.appendChild(pepDetails);
        }
        
        // Create risk metrics
        if (data.metrics) {
            const metrics = document.createElement('div');
            metrics.className = 'json-viewer-metrics';
            
            const metricsTitle = document.createElement('h3');
            metricsTitle.textContent = 'Risk Metrics';
            metrics.appendChild(metricsTitle);
            
            const metricsContainer = document.createElement('div');
            metricsContainer.className = 'metrics-container';
            
            const createMetricCard = (label, value, type) => {
                const card = document.createElement('div');
                card.className = `metric-card ${type}`;
                
                const valueElement = document.createElement('div');
                valueElement.className = 'metric-value';
                valueElement.textContent = value;
                card.appendChild(valueElement);
                
                const labelElement = document.createElement('div');
                labelElement.className = 'metric-label';
                labelElement.textContent = label;
                card.appendChild(labelElement);
                
                return card;
            };
            
            metricsContainer.appendChild(createMetricCard('Sanctions', data.metrics.sanctions || 0, 'sanctions'));
            metricsContainer.appendChild(createMetricCard('PEP Score', (data.metrics.pep * 100).toFixed(0) + '%', 'pep'));
            metricsContainer.appendChild(createMetricCard('Adverse Media', data.metrics.adverse_media || 0, 'adverse-media'));
            
            metrics.appendChild(metricsContainer);
            fragment.appendChild(metrics);
        }
        
        // Create aliases section if available
        if (data.aliases && data.aliases.length > 0) {
            const aliases = document.createElement('div');
            aliases.className = 'json-viewer-section';
            
            const aliasesTitle = document.createElement('h3');
            aliasesTitle.textContent = 'Known Aliases';
            aliases.appendChild(aliasesTitle);
            
            const aliasList = document.createElement('ul');
            aliasList.className = 'json-viewer-list';
            
            data.aliases.forEach(alias => {
                const li = document.createElement('li');
                li.textContent = alias;
                aliasList.appendChild(li);
            });
            
            aliases.appendChild(aliasList);
            fragment.appendChild(aliases);
        }
        
        // Create risk assessment section
        if (data.risk_assessment) {
            const riskAssessment = document.createElement('div');
            riskAssessment.className = 'json-viewer-section';
            
            const riskTitle = document.createElement('h3');
            riskTitle.textContent = 'Risk Assessment';
            riskAssessment.appendChild(riskTitle);
            
            const riskText = document.createElement('p');
            riskText.textContent = data.risk_assessment;
            riskAssessment.appendChild(riskText);
            
            fragment.appendChild(riskAssessment);
        }
        
        // Create professional details if available from real data
        if (data.real_data) {
            const professional = document.createElement('div');
            professional.className = 'json-viewer-section';
            
            const professionalTitle = document.createElement('h3');
            professionalTitle.textContent = 'Professional Background';
            professional.appendChild(professionalTitle);
            
            const professionalTable = document.createElement('table');
            professionalTable.className = 'json-viewer-table';
            
            const professionalRows = [
                { label: 'Current Position', value: data.real_data.current_position || 'N/A' },
                { label: 'Organization', value: data.real_data.organization || 'N/A' },
                { label: 'Education', value: data.real_data.education || 'N/A' }
            ];
            
            professionalRows.forEach(row => {
                const tr = document.createElement('tr');
                
                const th = document.createElement('th');
                th.textContent = row.label;
                tr.appendChild(th);
                
                const td = document.createElement('td');
                td.textContent = row.value;
                tr.appendChild(td);
                
                professionalTable.appendChild(tr);
            });
            
            professional.appendChild(professionalTable);
            
            // Add professional summary if available
            if (data.real_data.professional_summary) {
                const summaryTitle = document.createElement('h4');
                summaryTitle.textContent = 'Professional Summary';
                professional.appendChild(summaryTitle);
                
                const summaryText = document.createElement('p');
                summaryText.textContent = data.real_data.professional_summary;
                professional.appendChild(summaryText);
            }
            
            fragment.appendChild(professional);
        }
        
        return fragment;
    }
    
    renderDartData(data) {
        const fragment = document.createDocumentFragment();
        
        // Create DART header
        const header = document.createElement('div');
        header.className = 'json-viewer-header';
        
        const companyName = document.createElement('h2');
        companyName.textContent = data.company_name;
        header.appendChild(companyName);
        
        const registryBadge = document.createElement('div');
        registryBadge.className = 'registry-badge';
        registryBadge.textContent = `Registry ID: ${data.registry_id}`;
        header.appendChild(registryBadge);
        
        fragment.appendChild(header);
        
        // Create company summary
        const summary = document.createElement('div');
        summary.className = 'json-viewer-summary';
        
        const summaryTable = document.createElement('table');
        summaryTable.className = 'json-viewer-table';
        
        const summaryRows = [
            { label: 'Country', value: data.country || 'N/A' },
            { label: 'Registration Date', value: data.registration_date || 'N/A' },
            { label: 'Status', value: data.status || 'N/A' },
            { label: 'Industry', value: `${data.industry_name} (${data.industry_code})` || 'N/A' },
            { label: 'Address', value: data.address || 'N/A' },
            { label: 'Representative', value: data.representative || 'N/A' },
            { label: 'Capital', value: data.capital || 'N/A' }
        ];
        
        summaryRows.forEach(row => {
            const tr = document.createElement('tr');
            
            const th = document.createElement('th');
            th.textContent = row.label;
            tr.appendChild(th);
            
            const td = document.createElement('td');
            td.textContent = row.value;
            tr.appendChild(td);
            
            summaryTable.appendChild(tr);
        });
        
        summary.appendChild(summaryTable);
        fragment.appendChild(summary);
        
        // Create financial summary
        if (data.financial_summary) {
            const financial = document.createElement('div');
            financial.className = 'json-viewer-section';
            
            const financialTitle = document.createElement('h3');
            financialTitle.textContent = 'Financial Summary';
            financial.appendChild(financialTitle);
            
            const financialTable = document.createElement('table');
            financialTable.className = 'json-viewer-table financial-table';
            
            // Create header row
            const headerRow = document.createElement('tr');
            
            const emptyTh = document.createElement('th');
            headerRow.appendChild(emptyTh);
            
            const years = Object.keys(data.financial_summary.revenue || {}).sort();
            years.forEach(year => {
                const th = document.createElement('th');
                th.textContent = year;
                headerRow.appendChild(th);
            });
            
            financialTable.appendChild(headerRow);
            
            // Create revenue row
            const revenueRow = document.createElement('tr');
            
            const revenueTh = document.createElement('th');
            revenueTh.textContent = 'Revenue';
            revenueRow.appendChild(revenueTh);
            
            years.forEach(year => {
                const td = document.createElement('td');
                const value = data.financial_summary.revenue[year];
                td.textContent = this.formatCurrency(value, data.financial_summary.currency);
                revenueRow.appendChild(td);
            });
            
            financialTable.appendChild(revenueRow);
            
            // Create profit row
            const profitRow = document.createElement('tr');
            
            const profitTh = document.createElement('th');
            profitTh.textContent = 'Profit';
            profitRow.appendChild(profitTh);
            
            years.forEach(year => {
                const td = document.createElement('td');
                const value = data.financial_summary.profit[year];
                td.textContent = this.formatCurrency(value, data.financial_summary.currency);
                profitRow.appendChild(td);
            });
            
            financialTable.appendChild(profitRow);
            
            // Create assets row
            const assetsRow = document.createElement('tr');
            
            const assetsTh = document.createElement('th');
            assetsTh.textContent = 'Assets';
            assetsRow.appendChild(assetsTh);
            
            years.forEach(year => {
                const td = document.createElement('td');
                const value = data.financial_summary.assets[year];
                td.textContent = this.formatCurrency(value, data.financial_summary.currency);
                assetsRow.appendChild(td);
            });
            
            financialTable.appendChild(assetsRow);
            
            financial.appendChild(financialTable);
            fragment.appendChild(financial);
        }
        
        // Create documents section
        if (data.documents && data.documents.length > 0) {
            const documents = document.createElement('div');
            documents.className = 'json-viewer-section';
            
            const documentsTitle = document.createElement('h3');
            documentsTitle.textContent = 'Documents';
            documents.appendChild(documentsTitle);
            
            const documentsTable = document.createElement('table');
            documentsTable.className = 'json-viewer-table';
            
            // Create header row
            const headerRow = document.createElement('tr');
            ['ID', 'Title', 'Date', 'URL'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            documentsTable.appendChild(headerRow);
            
            // Create data rows
            data.documents.forEach(doc => {
                const tr = document.createElement('tr');
                
                const idTd = document.createElement('td');
                idTd.textContent = doc.id;
                tr.appendChild(idTd);
                
                const titleTd = document.createElement('td');
                titleTd.textContent = doc.title;
                tr.appendChild(titleTd);
                
                const dateTd = document.createElement('td');
                dateTd.textContent = doc.date;
                tr.appendChild(dateTd);
                
                const urlTd = document.createElement('td');
                const urlLink = document.createElement('a');
                urlLink.href = doc.url;
                urlLink.textContent = 'View';
                urlLink.target = '_blank';
                urlTd.appendChild(urlLink);
                tr.appendChild(urlTd);
                
                documentsTable.appendChild(tr);
            });
            
            documents.appendChild(documentsTable);
            fragment.appendChild(documents);
        }
        
        // Create subsidiaries section if available
        if (data.subsidiaries && data.subsidiaries.length > 0) {
            const subsidiaries = document.createElement('div');
            subsidiaries.className = 'json-viewer-section';
            
            const subsidiariesTitle = document.createElement('h3');
            subsidiariesTitle.textContent = 'Subsidiaries';
            subsidiaries.appendChild(subsidiariesTitle);
            
            const subsidiariesTable = document.createElement('table');
            subsidiariesTable.className = 'json-viewer-table';
            
            // Create header row
            const headerRow = document.createElement('tr');
            ['Name', 'Ownership', 'Business'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            subsidiariesTable.appendChild(headerRow);
            
            // Create data rows
            data.subsidiaries.forEach(sub => {
                const tr = document.createElement('tr');
                
                const nameTd = document.createElement('td');
                nameTd.textContent = sub.name;
                tr.appendChild(nameTd);
                
                const ownershipTd = document.createElement('td');
                ownershipTd.textContent = sub.ownership;
                tr.appendChild(ownershipTd);
                
                const businessTd = document.createElement('td');
                businessTd.textContent = sub.business;
                tr.appendChild(businessTd);
                
                subsidiariesTable.appendChild(tr);
            });
            
            subsidiaries.appendChild(subsidiariesTable);
            fragment.appendChild(subsidiaries);
        }
        
        // Create shareholders section if available
        if (data.major_shareholders && data.major_shareholders.length > 0) {
            const shareholders = document.createElement('div');
            shareholders.className = 'json-viewer-section';
            
            const shareholdersTitle = document.createElement('h3');
            shareholdersTitle.textContent = 'Major Shareholders';
            shareholders.appendChild(shareholdersTitle);
            
            const shareholdersTable = document.createElement('table');
            shareholdersTable.className = 'json-viewer-table';
            
            // Create header row
            const headerRow = document.createElement('tr');
            ['Name', 'Ownership', 'Relationship'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            shareholdersTable.appendChild(headerRow);
            
            // Create data rows
            data.major_shareholders.forEach(shareholder => {
                const tr = document.createElement('tr');
                
                const nameTd = document.createElement('td');
                nameTd.textContent = shareholder.name;
                tr.appendChild(nameTd);
                
                const ownershipTd = document.createElement('td');
                ownershipTd.textContent = shareholder.ownership;
                tr.appendChild(ownershipTd);
                
                const relationshipTd = document.createElement('td');
                relationshipTd.textContent = shareholder.relationship;
                tr.appendChild(relationshipTd);
                
                shareholdersTable.appendChild(tr);
            });
            
            shareholders.appendChild(shareholdersTable);
            fragment.appendChild(shareholders);
        }
        
        return fragment;
    }
    
    renderGenericJson(data) {
        const container = document.createElement('div');
        container.className = 'json-viewer-generic';
        
        const pre = document.createElement('pre');
        pre.className = 'json-viewer-code';
        pre.textContent = JSON.stringify(data, null, 2);
        
        container.appendChild(pre);
        return container;
    }
    
    formatCurrency(value, currency) {
        if (typeof value !== 'number') {
            return value;
        }
        
        // Format large numbers in millions or billions
        if (value >= 1000000000) {
            return `${(value / 1000000000).toFixed(2)}B ${currency}`;
        } else if (value >= 1000000) {
            return `${(value / 1000000).toFixed(2)}M ${currency}`;
        } else {
            return `${value.toLocaleString()} ${currency}`;
        }
    }
}

// Initialize the viewer when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with the 'json-viewer' class
    const viewerElements = document.querySelectorAll('.json-viewer');
    
    viewerElements.forEach(element => {
        try {
            const dataStr = element.getAttribute('data-json');
            if (dataStr) {
                const data = JSON.parse(dataStr);
                new EnhancedJsonViewer({
                    container: element,
                    data: data,
                    theme: element.getAttribute('data-theme') || 'dark'
                });
            }
        } catch (error) {
            console.error('Error initializing JSON viewer:', error);
        }
    });
});
