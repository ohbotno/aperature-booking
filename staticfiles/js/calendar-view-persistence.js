/**
 * Calendar View Persistence
 * Aperture Booking
 * 
 * Saves and restores user calendar view preferences including:
 * - Current view type (month/week/day)
 * - Selected resource filter
 * - Calendar date position
 * - Window size and layout preferences
 */

class CalendarViewPersistence {
    constructor(calendar) {
        this.calendar = calendar;
        this.storageKey = 'aperture_calendar_preferences';
        this.debounceTimeout = null;
        this.defaultPreferences = {
            view: 'dayGridMonth',
            date: null,
            resourceFilter: '',
            sidebarCollapsed: false,
            timezone: null,
            businessHours: true,
            weekendsVisible: true
        };
        this.init();
    }
    
    init() {
        this.loadPreferences();
        this.bindEventListeners();
        this.setupPeriodicSave();
    }
    
    loadPreferences() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            const preferences = stored ? JSON.parse(stored) : this.defaultPreferences;
            
            // Merge with defaults to handle new preference keys
            this.preferences = { ...this.defaultPreferences, ...preferences };
            
            this.applyPreferences();
            
        } catch (error) {
            console.warn('Failed to load calendar preferences:', error);
            this.preferences = { ...this.defaultPreferences };
        }
    }
    
    applyPreferences() {
        // Apply view type
        if (this.preferences.view && this.calendar.view.type !== this.preferences.view) {
            this.calendar.changeView(this.preferences.view);
        }
        
        // Apply date if stored and recent (within 30 days)
        if (this.preferences.date) {
            const storedDate = new Date(this.preferences.date);
            const daysDiff = Math.abs(new Date() - storedDate) / (1000 * 60 * 60 * 24);
            
            if (daysDiff <= 30) {
                this.calendar.gotoDate(storedDate);
            }
        }
        
        // Apply resource filter
        const resourceFilter = document.getElementById('resource-filter');
        if (resourceFilter && this.preferences.resourceFilter) {
            resourceFilter.value = this.preferences.resourceFilter;
            // Trigger change event to update calendar
            resourceFilter.dispatchEvent(new Event('change'));
        }
        
        // Apply business hours visibility
        this.calendar.setOption('businessHours', this.preferences.businessHours);
        
        // Apply weekends visibility
        this.calendar.setOption('weekends', this.preferences.weekendsVisible);
        
        // Apply sidebar state if applicable
        this.applySidebarState();
        
        console.log('Calendar preferences applied:', this.preferences);
    }
    
    applySidebarState() {
        const sidebar = document.querySelector('.sidebar, .filters-sidebar');
        const toggleBtn = document.querySelector('[data-bs-target="#filters-collapse"]');
        
        if (sidebar && this.preferences.sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            if (toggleBtn) {
                toggleBtn.setAttribute('aria-expanded', 'false');
            }
        }
    }
    
    bindEventListeners() {
        // Save preferences when view changes
        this.calendar.on('viewChange', () => {
            this.debouncedSave();
        });
        
        // Save when date navigation occurs
        this.calendar.on('dateChange', () => {
            this.debouncedSave();
        });
        
        // Save when resource filter changes
        const resourceFilter = document.getElementById('resource-filter');
        if (resourceFilter) {
            resourceFilter.addEventListener('change', () => {
                this.debouncedSave();
            });
        }
        
        // Save when window resizes (indicates layout preference)
        window.addEventListener('resize', () => {
            this.debouncedSave();
        });
        
        // Save when sidebar is toggled
        const sidebarToggle = document.querySelector('[data-bs-target="#filters-collapse"]');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                // Delay to allow Bootstrap animation to complete
                setTimeout(() => this.debouncedSave(), 300);
            });
        }
        
        // Save when page is about to unload
        window.addEventListener('beforeunload', () => {
            this.savePreferences();
        });
        
        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.savePreferences();
            }
        });
    }
    
    setupPeriodicSave() {
        // Save preferences every 30 seconds if there are unsaved changes
        setInterval(() => {
            if (this.hasUnsavedChanges()) {
                this.savePreferences();
            }
        }, 30000);
    }
    
    debouncedSave() {
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        
        this.debounceTimeout = setTimeout(() => {
            this.savePreferences();
        }, 1000); // Save 1 second after last change
    }
    
    hasUnsavedChanges() {
        const current = this.getCurrentPreferences();
        return JSON.stringify(current) !== JSON.stringify(this.preferences);
    }
    
    getCurrentPreferences() {
        const resourceFilter = document.getElementById('resource-filter');
        const sidebar = document.querySelector('.sidebar, .filters-sidebar');
        
        return {
            view: this.calendar.view.type,
            date: this.calendar.getDate().toISOString(),
            resourceFilter: resourceFilter ? resourceFilter.value : '',
            sidebarCollapsed: sidebar ? sidebar.classList.contains('collapsed') : false,
            timezone: this.calendar.getOption('timeZone') || Intl.DateTimeFormat().resolvedOptions().timeZone,
            businessHours: this.calendar.getOption('businessHours') !== false,
            weekendsVisible: this.calendar.getOption('weekends') !== false
        };
    }
    
    savePreferences() {
        try {
            const current = this.getCurrentPreferences();
            this.preferences = current;
            
            localStorage.setItem(this.storageKey, JSON.stringify(this.preferences));
            
            console.log('Calendar preferences saved:', this.preferences);
            
        } catch (error) {
            console.warn('Failed to save calendar preferences:', error);
            
            // If localStorage is full, try to clear old data
            if (error.name === 'QuotaExceededError') {
                this.clearOldPreferences();
                try {
                    localStorage.setItem(this.storageKey, JSON.stringify(this.preferences));
                } catch (retryError) {
                    console.error('Failed to save preferences after cleanup:', retryError);
                }
            }
        }
    }
    
    clearOldPreferences() {
        // Remove old preference keys if they exist
        const oldKeys = [
            'calendar_view',
            'calendar_date',
            'calendar_resource_filter',
            'fullcalendar_preferences'
        ];
        
        oldKeys.forEach(key => {
            localStorage.removeItem(key);
        });
        
        console.log('Cleared old calendar preference keys');
    }
    
    resetPreferences() {
        this.preferences = { ...this.defaultPreferences };
        try {
            localStorage.removeItem(this.storageKey);
            console.log('Calendar preferences reset to defaults');
            
            // Apply defaults immediately
            this.applyPreferences();
            
        } catch (error) {
            console.warn('Failed to reset preferences:', error);
        }
    }
    
    exportPreferences() {
        return {
            ...this.preferences,
            exportedAt: new Date().toISOString(),
            version: '1.0'
        };
    }
    
    importPreferences(preferences) {
        try {
            if (preferences && typeof preferences === 'object') {
                // Validate preference structure
                const validKeys = Object.keys(this.defaultPreferences);
                const filteredPrefs = {};
                
                validKeys.forEach(key => {
                    if (preferences.hasOwnProperty(key)) {
                        filteredPrefs[key] = preferences[key];
                    }
                });
                
                this.preferences = { ...this.defaultPreferences, ...filteredPrefs };
                this.savePreferences();
                this.applyPreferences();
                
                console.log('Calendar preferences imported successfully');
                return true;
            }
        } catch (error) {
            console.error('Failed to import preferences:', error);
        }
        return false;
    }
    
    // Public methods for external control
    setViewPreference(viewType) {
        if (['dayGridMonth', 'timeGridWeek', 'timeGridDay'].includes(viewType)) {
            this.calendar.changeView(viewType);
            this.debouncedSave();
        }
    }
    
    setResourceFilter(resourceId) {
        const resourceFilter = document.getElementById('resource-filter');
        if (resourceFilter) {
            resourceFilter.value = resourceId;
            resourceFilter.dispatchEvent(new Event('change'));
            this.debouncedSave();
        }
    }
    
    toggleBusinessHours() {
        const current = this.calendar.getOption('businessHours');
        this.calendar.setOption('businessHours', !current);
        this.debouncedSave();
    }
    
    toggleWeekends() {
        const current = this.calendar.getOption('weekends');
        this.calendar.setOption('weekends', !current);
        this.debouncedSave();
    }
    
    // Debug methods
    getStorageInfo() {
        try {
            const used = new Blob([localStorage.getItem(this.storageKey) || '']).size;
            const available = 5 * 1024 * 1024; // Approximate localStorage limit
            
            return {
                storageKey: this.storageKey,
                bytesUsed: used,
                bytesAvailable: available,
                percentageUsed: ((used / available) * 100).toFixed(2) + '%'
            };
        } catch (error) {
            return { error: error.message };
        }
    }
    
    getPreferences() {
        return { ...this.preferences };
    }
}

// CSS for persistence indicator
const persistenceStyles = `
<style>
    .preference-saved-indicator {
        position: fixed;
        bottom: 20px;
        left: 20px;
        background: rgba(25, 135, 84, 0.9);
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
        z-index: 9999;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
        pointer-events: none;
    }
    
    .preference-saved-indicator.show {
        opacity: 1;
        transform: translateY(0);
    }
    
    .preference-saved-indicator .bi {
        margin-right: 8px;
    }
</style>
`;

// Add styles to document head
document.head.insertAdjacentHTML('beforeend', persistenceStyles);

// Export for use in other modules
window.CalendarViewPersistence = CalendarViewPersistence;