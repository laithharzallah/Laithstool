/**
 * Enhanced JSON Viewer Component
 * Converts raw JSON data into interactive, collapsible UI elements
 */

class JSONViewer {
    constructor(options = {}) {
        this.options = {
            collapsed: false,
            rootCollapsible: true,
            withQuotes: false,
            withLinks: true,
            ...options
        };
    }

    /**
     * Renders JSON data into a DOM element
     * @param {Object|Array} json - The JSON data to render
     * @param {HTMLElement} container - The container element
     */
    render(json, container) {
        if (!container) {
            throw new Error('Container element is required');
        }

        // Clear container
        container.innerHTML = '';
        container.classList.add('json-viewer');

        // Create root element
        const rootElem = this._createNode(json);
        container.appendChild(rootElem);

        // Initialize collapsible behavior
        this._initCollapsible(container);
    }

    /**
     * Creates a DOM node for a JSON value
     * @param {any} value - The JSON value
     * @param {string} key - The key (for object properties)
     * @returns {HTMLElement} - The created DOM node
     */
    _createNode(value, key = null) {
        const elem = document.createElement('div');
        elem.classList.add('json-viewer-item');

        // Handle different types
        if (value === null) {
            return this._createSimpleNode(key, 'null', 'null');
        } else if (value === undefined) {
            return this._createSimpleNode(key, 'undefined', 'undefined');
        } else if (typeof value === 'boolean') {
            return this._createSimpleNode(key, value.toString(), 'boolean');
        } else if (typeof value === 'number') {
            return this._createSimpleNode(key, value.toString(), 'number');
        } else if (typeof value === 'string') {
            return this._createStringNode(key, value);
        } else if (Array.isArray(value)) {
            return this._createArrayNode(key, value);
        } else if (typeof value === 'object') {
            return this._createObjectNode(key, value);
        }

        return elem;
    }

    /**
     * Creates a node for simple values (null, boolean, number)
     */
    _createSimpleNode(key, value, type) {
        const elem = document.createElement('div');
        elem.classList.add('json-viewer-item', `json-viewer-${type}`);

        if (key !== null) {
            const keyElem = document.createElement('span');
            keyElem.classList.add('json-viewer-key');
            keyElem.textContent = this.options.withQuotes ? `"${key}":` : `${key}:`;
            elem.appendChild(keyElem);
        }

        const valueElem = document.createElement('span');
        valueElem.classList.add('json-viewer-value', `json-viewer-${type}`);
        valueElem.textContent = value;
        elem.appendChild(valueElem);

        return elem;
    }

    /**
     * Creates a node for string values with special handling for URLs
     */
    _createStringNode(key, value) {
        const elem = document.createElement('div');
        elem.classList.add('json-viewer-item', 'json-viewer-string');

        if (key !== null) {
            const keyElem = document.createElement('span');
            keyElem.classList.add('json-viewer-key');
            keyElem.textContent = this.options.withQuotes ? `"${key}":` : `${key}:`;
            elem.appendChild(keyElem);
        }

        const valueElem = document.createElement('span');
        valueElem.classList.add('json-viewer-value', 'json-viewer-string');

        // Check if the string is a URL and make it clickable
        if (this.options.withLinks && this._isUrl(value)) {
            const linkElem = document.createElement('a');
            linkElem.href = value;
            linkElem.target = '_blank';
            linkElem.rel = 'noopener noreferrer';
            linkElem.textContent = this.options.withQuotes ? `"${value}"` : value;
            valueElem.appendChild(linkElem);
        } else {
            valueElem.textContent = this.options.withQuotes ? `"${value}"` : value;
        }

        elem.appendChild(valueElem);
        return elem;
    }

    /**
     * Creates a node for array values
     */
    _createArrayNode(key, value) {
        const elem = document.createElement('div');
        elem.classList.add('json-viewer-item', 'json-viewer-array');

        // Create header with key and toggle
        const headerElem = document.createElement('div');
        headerElem.classList.add('json-viewer-header');

        if (key !== null) {
            const keyElem = document.createElement('span');
            keyElem.classList.add('json-viewer-key');
            keyElem.textContent = this.options.withQuotes ? `"${key}":` : `${key}:`;
            headerElem.appendChild(keyElem);
        }

        const toggleElem = document.createElement('span');
        toggleElem.classList.add('json-viewer-toggle');
        toggleElem.textContent = this.options.collapsed ? '▶' : '▼';
        headerElem.appendChild(toggleElem);

        const previewElem = document.createElement('span');
        previewElem.classList.add('json-viewer-preview');
        previewElem.textContent = `Array(${value.length})`;
        headerElem.appendChild(previewElem);

        elem.appendChild(headerElem);

        // Create content container
        const contentElem = document.createElement('div');
        contentElem.classList.add('json-viewer-content');
        if (this.options.collapsed) {
            contentElem.style.display = 'none';
        }

        // Add array items
        value.forEach((item, index) => {
            const itemElem = this._createNode(item, index);
            contentElem.appendChild(itemElem);
        });

        elem.appendChild(contentElem);
        return elem;
    }

    /**
     * Creates a node for object values
     */
    _createObjectNode(key, value) {
        const elem = document.createElement('div');
        elem.classList.add('json-viewer-item', 'json-viewer-object');

        // Create header with key and toggle
        const headerElem = document.createElement('div');
        headerElem.classList.add('json-viewer-header');

        if (key !== null) {
            const keyElem = document.createElement('span');
            keyElem.classList.add('json-viewer-key');
            keyElem.textContent = this.options.withQuotes ? `"${key}":` : `${key}:`;
            headerElem.appendChild(keyElem);
        }

        const toggleElem = document.createElement('span');
        toggleElem.classList.add('json-viewer-toggle');
        toggleElem.textContent = this.options.collapsed ? '▶' : '▼';
        headerElem.appendChild(toggleElem);

        const previewElem = document.createElement('span');
        previewElem.classList.add('json-viewer-preview');
        const keys = Object.keys(value);
        previewElem.textContent = `Object{${keys.length}}`;
        headerElem.appendChild(previewElem);

        elem.appendChild(headerElem);

        // Create content container
        const contentElem = document.createElement('div');
        contentElem.classList.add('json-viewer-content');
        if (this.options.collapsed) {
            contentElem.style.display = 'none';
        }

        // Add object properties
        for (const propKey in value) {
            if (Object.prototype.hasOwnProperty.call(value, propKey)) {
                const propElem = this._createNode(value[propKey], propKey);
                contentElem.appendChild(propElem);
            }
        }

        elem.appendChild(contentElem);
        return elem;
    }

    /**
     * Initializes collapsible behavior for the JSON viewer
     */
    _initCollapsible(container) {
        const toggles = container.querySelectorAll('.json-viewer-toggle');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const header = toggle.parentElement;
                const content = header.nextElementSibling;
                const isCollapsed = content.style.display === 'none';

                // Toggle display
                content.style.display = isCollapsed ? 'block' : 'none';
                toggle.textContent = isCollapsed ? '▼' : '▶';
            });
        });
    }

    /**
     * Checks if a string is a URL
     */
    _isUrl(str) {
        try {
            const url = new URL(str);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch {
            return false;
        }
    }

    /**
     * Formats a JSON string into a pretty-printed string
     */
    static formatJSON(json) {
        if (typeof json === 'string') {
            try {
                json = JSON.parse(json);
            } catch (e) {
                return json;
            }
        }
        return JSON.stringify(json, null, 2);
    }
}

// Add CSS styles for the JSON viewer
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        .json-viewer {
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            line-height: 1.5;
            color: var(--text-0, #e6ebf5);
            background: var(--bg-2, #1a2132);
            border-radius: 8px;
            padding: 16px;
            overflow: auto;
            max-height: 600px;
        }
        
        .json-viewer-item {
            margin: 2px 0;
            padding-left: 20px;
            position: relative;
        }
        
        .json-viewer-key {
            color: var(--brand-500, #3ea6ff);
            margin-right: 8px;
        }
        
        .json-viewer-value {
            color: var(--text-0, #e6ebf5);
        }
        
        .json-viewer-string {
            color: var(--accent-500, #11d6a5);
        }
        
        .json-viewer-number {
            color: var(--warn-500, #ffb020);
        }
        
        .json-viewer-boolean {
            color: var(--info-500, #3ea6ff);
        }
        
        .json-viewer-null, .json-viewer-undefined {
            color: var(--danger-500, #f55454);
        }
        
        .json-viewer-toggle {
            cursor: pointer;
            margin-right: 6px;
            color: var(--text-1, #a9b4c8);
            user-select: none;
        }
        
        .json-viewer-preview {
            color: var(--text-2, #7a869a);
            font-style: italic;
        }
        
        .json-viewer-header {
            cursor: pointer;
            padding: 2px 0;
        }
        
        .json-viewer-content {
            border-left: 1px dashed var(--border-1, rgba(255, 255, 255, 0.08));
            margin-left: 4px;
        }
        
        .json-viewer a {
            color: var(--brand-500, #3ea6ff);
            text-decoration: none;
        }
        
        .json-viewer a:hover {
            text-decoration: underline;
        }
    `;
    document.head.appendChild(style);
});
