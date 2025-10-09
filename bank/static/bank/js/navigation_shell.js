/**
 * Bank Navigation Shell - Seamless AJAX Navigation System
 * Provides instant page transitions without full reloads
 */

class BankNavigationShell {
    constructor() {
        this.currentView = null;
        this.viewCache = new Map();
        this.isLoading = false;
        this.maxCacheSize = 3; // Keep last 3 views in memory
        this.transitionDuration = 300; // ms
        
        // View configuration
        this.viewEndpoints = {
            'dashboard': '/bank/ajax/dashboard/',
            'accounts': '/bank/ajax/accounts/',
            'weekly': '/bank/ajax/weekly/',
            'transactions': '/bank/ajax/transactions/',
            'payees': '/bank/ajax/payees/',
            'categories': '/bank/ajax/categories/'
        };
        
        this.init();
    }
    
    init() {
        console.log('🚀 Bank Navigation Shell initializing...');
        
        // Setup tab click handlers
        document.querySelectorAll('.shell-nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.currentTarget.dataset.view;
                this.loadView(view);
            });
            
            // Prefetch on hover (performance boost)
            tab.addEventListener('mouseenter', (e) => {
                const view = e.currentTarget.dataset.view;
                if (!this.viewCache.has(view)) {
                    this.prefetchView(view);
                }
            });
        });
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.view) {
                this.loadView(e.state.view, false);
            }
        });
        
        // Load initial view based on URL
        const initialView = this.getViewFromURL() || 'dashboard';
        this.loadView(initialView, false);
        
        // Update view status
        this.updateStatus('System initialized');
        
        console.log('✅ Bank Navigation Shell ready');
    }
    
    async loadView(viewName, pushState = true, queryParams = {}) {
        // Prevent concurrent loads
        if (this.isLoading) {
            console.log('⏳ Load already in progress, skipping...');
            return;
        }
        
        // Create cache key including query params for views that need it
        const cacheKey = Object.keys(queryParams).length > 0 
            ? `${viewName}?${new URLSearchParams(queryParams).toString()}`
            : viewName;
        
        // Don't reload same view with same params
        if (cacheKey === this.currentView) {
            console.log('📍 Already on', viewName);
            return;
        }
        
        console.log('📂 Loading view:', viewName, queryParams);
        this.isLoading = true;
        this.updateStatus(`Loading ${viewName}...`);
        
        // Update active tab
        this.updateActiveTab(viewName);
        
        // Play navigation sound
        if (window.ExpanseAudio && window.ExpanseAudio.audioContext) {
            window.ExpanseAudio.playClick();
        }
        
        const contentView = document.getElementById('shell-content-view');
        const contentLoader = document.getElementById('shell-content-loader');
        
        try {
            // Show loader, hide content
            contentView.style.opacity = '0';
            await this.delay(100);
            contentView.style.display = 'none';
            contentLoader.style.display = 'grid';
            
            // Fetch content (from cache or server)
            let content;
            if (this.viewCache.has(cacheKey)) {
                console.log('💾 Loading from cache');
                content = this.viewCache.get(cacheKey);
                await this.delay(200); // Simulate minimal load time for smooth transition
            } else {
                console.log('🌐 Fetching from server');
                content = await this.fetchViewContent(viewName, queryParams);
                this.cacheView(cacheKey, content);
            }
            
            // Update content
            contentView.innerHTML = content;
            
            // Hide loader, show content with fade in
            contentLoader.style.display = 'none';
            contentView.style.display = 'block';
            await this.delay(50);
            contentView.style.opacity = '1';
            
            // Update browser history
            if (pushState) {
                const url = viewName === 'dashboard' 
                    ? '/bank/' 
                    : `/bank/${viewName}/`;
                history.pushState({ view: viewName, params: queryParams }, '', url);
            }
            
            this.currentView = cacheKey;
            this.updateStatus(`${viewName.toUpperCase()} loaded`);
            
            // Re-initialize view-specific scripts
            this.initializeViewScripts(viewName);
            
            console.log('✅ View loaded:', viewName);
            
        } catch (error) {
            console.error('❌ Failed to load view:', error);
            this.showError(viewName, error);
        } finally {
            this.isLoading = false;
        }
    }
    
    async fetchViewContent(viewName, queryParams = {}) {
        const endpoint = this.viewEndpoints[viewName];
        
        if (!endpoint) {
            throw new Error(`Unknown view: ${viewName}`);
        }
        
        // Build URL with query parameters
        const url = Object.keys(queryParams).length > 0
            ? `${endpoint}?${new URLSearchParams(queryParams).toString()}`
            : endpoint;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status !== 'success') {
            throw new Error(data.error || 'Unknown error');
        }
        
        return data.html;
    }
    
    async prefetchView(viewName) {
        if (this.viewCache.has(viewName) || this.isLoading) {
            return;
        }
        
        console.log('🔮 Prefetching:', viewName);
        
        try {
            const content = await this.fetchViewContent(viewName);
            this.cacheView(viewName, content);
            console.log('✅ Prefetched:', viewName);
        } catch (error) {
            console.warn('Failed to prefetch:', viewName, error);
        }
    }
    
    cacheView(viewName, content) {
        // Implement LRU cache (keep last N views)
        if (this.viewCache.size >= this.maxCacheSize) {
            const firstKey = this.viewCache.keys().next().value;
            this.viewCache.delete(firstKey);
            console.log('🗑️ Evicted from cache:', firstKey);
        }
        
        this.viewCache.set(viewName, content);
        console.log('💾 Cached:', viewName, `(${this.viewCache.size}/${this.maxCacheSize})`);
    }
    
    updateActiveTab(viewName) {
        document.querySelectorAll('.shell-nav-tab').forEach(tab => {
            const isActive = tab.dataset.view === viewName;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-current', isActive ? 'page' : 'false');
        });
    }
    
    initializeViewScripts(viewName) {
        // Call view-specific initialization functions if they exist
        const initFunctions = {
            'dashboard': window.initDashboardView,
            'accounts': window.initAccountsView,
            'weekly': window.initWeeklyView,
            'transactions': window.initTransactionsView,
            'payees': window.initPayeesView,
            'categories': window.initCategoriesView
        };
        
        const initFn = initFunctions[viewName];
        if (initFn && typeof initFn === 'function') {
            console.log('🔧 Initializing view scripts:', viewName);
            initFn();
        }
        
        // Re-initialize Bootstrap tooltips if present
        if (window.bootstrap && bootstrap.Tooltip) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
        }
    }
    
    changeFaction(faction) {
        const spaceInterface = document.getElementById('bankShellInterface');
        if (spaceInterface) {
            spaceInterface.setAttribute('data-faction', faction);
            localStorage.setItem('bankFaction', faction);
            
            // Play faction change sound
            if (window.ExpanseAudio && window.ExpanseAudio.audioContext) {
                window.ExpanseAudio.playHover();
            }
            
            console.log('🎨 Faction changed to:', faction);
        }
    }
    
    getViewFromURL() {
        const path = window.location.pathname;
        
        // Match /bank/, /bank/accounts/, etc.
        if (path === '/bank' || path === '/bank/') {
            return 'dashboard';
        }
        
        const match = path.match(/\/bank\/([^\/]+)/);
        if (match) {
            const view = match[1];
            // Handle weekly-expanse redirect
            if (view === 'weekly-expanse') {
                return 'weekly';
            }
            return view;
        }
        
        return null;
    }
    
    updateStatus(message) {
        const statusEl = document.getElementById('viewStatus');
        if (statusEl) {
            statusEl.textContent = message.toUpperCase();
        }
    }
    
    showError(viewName, error) {
        const contentView = document.getElementById('shell-content-view');
        const contentLoader = document.getElementById('shell-content-loader');
        
        contentLoader.style.display = 'none';
        contentView.style.display = 'block';
        contentView.innerHTML = `
            <div class="shell-error-panel">
                <div class="error-icon">
                    <i class="bi bi-exclamation-triangle"></i>
                </div>
                <h2>SYSTEM ERROR</h2>
                <p>Failed to load ${viewName.toUpperCase()} module</p>
                <code>${error.message}</code>
                <button onclick="window.bankShell.loadView('${viewName}')" class="dashboard-action-btn">
                    <i class="bi bi-arrow-clockwise"></i>
                    <span>Retry</span>
                </button>
                <button onclick="window.bankShell.loadView('dashboard')" class="dashboard-action-btn">
                    <i class="bi bi-house"></i>
                    <span>Return to Command</span>
                </button>
            </div>
        `;
        contentView.style.opacity = '1';
        this.updateStatus('ERROR');
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    clearCache() {
        this.viewCache.clear();
        console.log('🗑️ Cache cleared');
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Restore saved faction
    const savedFaction = localStorage.getItem('bankFaction') || 'un';
    const spaceInterface = document.getElementById('bankShellInterface');
    if (spaceInterface) {
        spaceInterface.setAttribute('data-faction', savedFaction);
    }
    
    const factionSelector = document.getElementById('shellFactionSelector');
    if (factionSelector) {
        factionSelector.value = savedFaction;
    }
    
    // Initialize navigation shell
    window.bankShell = new BankNavigationShell();
});
