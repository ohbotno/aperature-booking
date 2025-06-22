/**
 * Calendar Keyboard Shortcuts
 * Aperture Booking
 * 
 * Provides keyboard navigation and shortcuts for the calendar interface.
 */

class CalendarShortcuts {
    constructor(calendar) {
        this.calendar = calendar;
        this.shortcuts = new Map();
        this.helpVisible = false;
        this.init();
    }
    
    init() {
        this.setupShortcuts();
        this.bindEvents();
        this.createHelpModal();
    }
    
    setupShortcuts() {
        // Navigation shortcuts
        this.shortcuts.set('t', () => this.calendar.today());
        this.shortcuts.set('ArrowLeft', () => this.calendar.prev());
        this.shortcuts.set('ArrowRight', () => this.calendar.next());
        
        // View shortcuts
        this.shortcuts.set('m', () => this.calendar.changeView('dayGridMonth'));
        this.shortcuts.set('w', () => this.calendar.changeView('timeGridWeek'));
        this.shortcuts.set('d', () => this.calendar.changeView('timeGridDay'));
        
        // Action shortcuts
        this.shortcuts.set('n', () => this.openNewBookingModal());
        this.shortcuts.set('r', () => this.calendar.refetchEvents());
        this.shortcuts.set('f', () => this.focusResourceFilter());
        this.shortcuts.set('p', () => this.exportToPDF());
        
        // Modal shortcuts
        this.shortcuts.set('Escape', () => this.closeModals());
        
        // Help shortcut
        this.shortcuts.set('h', () => this.toggleHelp());
        this.shortcuts.set('?', () => this.toggleHelp());
    }
    
    bindEvents() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in form fields
            if (this.isFormElement(e.target)) {
                return;
            }
            
            // Handle key combinations
            let key = e.key;
            if (e.ctrlKey || e.metaKey) {
                key = `${e.ctrlKey ? 'Ctrl+' : 'Cmd+'}${key}`;
            }
            if (e.shiftKey && !['?'].includes(e.key)) {
                key = `Shift+${key}`;
            }
            
            const action = this.shortcuts.get(key);
            if (action) {
                e.preventDefault();
                action();
            }
        });
    }
    
    isFormElement(element) {
        const formElements = ['INPUT', 'TEXTAREA', 'SELECT'];
        return formElements.includes(element.tagName) || 
               element.contentEditable === 'true' ||
               element.closest('.modal.show');
    }
    
    openNewBookingModal() {
        const modal = document.getElementById('bookingModal');
        if (modal) {
            new bootstrap.Modal(modal).show();
        }
    }
    
    focusResourceFilter() {
        const filter = document.getElementById('resource-filter');
        if (filter) {
            filter.focus();
        }
    }
    
    closeModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
    
    exportToPDF() {
        // Look for PDF export button and trigger it
        const pdfBtn = document.getElementById('export-pdf-btn');
        if (pdfBtn) {
            pdfBtn.click();
        } else {
            // Fallback: trigger custom event for PDF export
            const event = new CustomEvent('calendar:exportPDF');
            document.dispatchEvent(event);
        }
    }
    
    createHelpModal() {
        const helpModalHTML = `
            <div class="modal fade" id="keyboardHelpModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-keyboard"></i> Keyboard Shortcuts
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="fw-bold">Navigation</h6>
                                    <div class="shortcut-group">
                                        <div class="shortcut-item">
                                            <kbd>T</kbd>
                                            <span>Go to today</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>←</kbd>
                                            <span>Previous period</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>→</kbd>
                                            <span>Next period</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>R</kbd>
                                            <span>Refresh calendar</span>
                                        </div>
                                    </div>
                                    
                                    <h6 class="fw-bold mt-4">Views</h6>
                                    <div class="shortcut-group">
                                        <div class="shortcut-item">
                                            <kbd>M</kbd>
                                            <span>Month view</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>W</kbd>
                                            <span>Week view</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>D</kbd>
                                            <span>Day view</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <h6 class="fw-bold">Actions</h6>
                                    <div class="shortcut-group">
                                        <div class="shortcut-item">
                                            <kbd>N</kbd>
                                            <span>New booking</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>F</kbd>
                                            <span>Focus resource filter</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>P</kbd>
                                            <span>Export to PDF</span>
                                        </div>
                                        <div class="shortcut-item">
                                            <kbd>Esc</kbd>
                                            <span>Close modals</span>
                                        </div>
                                    </div>
                                    
                                    <h6 class="fw-bold mt-4">Help</h6>
                                    <div class="shortcut-group">
                                        <div class="shortcut-item">
                                            <kbd>H</kbd> or <kbd>?</kbd>
                                            <span>Show this help</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="alert alert-info mt-3">
                                <i class="bi bi-lightbulb"></i>
                                <strong>Tip:</strong> Shortcuts are disabled when typing in form fields.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', helpModalHTML);
    }
    
    toggleHelp() {
        const modal = document.getElementById('keyboardHelpModal');
        if (modal) {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
            bsModal.toggle();
        }
    }
    
    // Public method to add custom shortcuts
    addShortcut(key, action, description) {
        this.shortcuts.set(key, action);
    }
    
    // Public method to remove shortcuts
    removeShortcut(key) {
        this.shortcuts.delete(key);
    }
}

// CSS for help modal styling
const shortcutStyles = `
<style>
    .shortcut-group {
        margin-bottom: 1rem;
    }
    
    .shortcut-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.25rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .shortcut-item:last-child {
        border-bottom: none;
    }
    
    .shortcut-item kbd {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 3px;
        box-shadow: 0 1px 0 rgba(0,0,0,0.2);
        color: #495057;
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        line-height: 1;
        min-width: 2rem;
        padding: 0.25rem 0.4rem;
        text-align: center;
        vertical-align: baseline;
        white-space: nowrap;
    }
    
    .shortcut-item span {
        flex: 1;
        margin-left: 1rem;
        color: #6c757d;
    }
    
    .keyboard-shortcut-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.875rem;
        z-index: 1000;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .keyboard-shortcut-indicator.show {
        opacity: 1;
    }
</style>
`;

// Add styles to document head
document.head.insertAdjacentHTML('beforeend', shortcutStyles);

// Export for use in other modules
window.CalendarShortcuts = CalendarShortcuts;