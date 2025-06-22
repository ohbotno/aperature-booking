/**
 * Calendar Print Fallback
 * Aperture Booking
 * 
 * Provides a simple print-to-PDF fallback when library-based PDF export fails.
 */

class CalendarPrintFallback {
    constructor(calendar) {
        this.calendar = calendar;
        this.init();
    }
    
    init() {
        this.addPrintButton();
        this.createPrintStyles();
    }
    
    addPrintButton() {
        // Add print button to calendar toolbar
        const toolbar = document.querySelector('.btn-toolbar .btn-group');
        if (toolbar) {
            const printBtn = document.createElement('button');
            printBtn.type = 'button';
            printBtn.className = 'btn btn-sm btn-outline-secondary';
            printBtn.id = 'print-calendar-btn';
            printBtn.innerHTML = '<i class="bi bi-printer"></i> Print';
            printBtn.title = 'Print calendar view';
            
            toolbar.appendChild(printBtn);
            
            printBtn.addEventListener('click', () => this.showPrintDialog());
        }
    }
    
    showPrintDialog() {
        const printDialogHTML = `
            <div class="modal fade" id="printCalendarModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-printer"></i> Print Calendar
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="print-options-form">
                                <div class="mb-3">
                                    <label for="print-title" class="form-label">Document Title</label>
                                    <input type="text" class="form-control" id="print-title" 
                                           value="${this.getDefaultTitle()}" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="print-view" class="form-label">View to Print</label>
                                    <select class="form-select" id="print-view">
                                        <option value="current">Current View</option>
                                        <option value="month">Month View</option>
                                        <option value="week">Week View</option>
                                        <option value="day">Day View</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="print-include-header" checked>
                                        <label class="form-check-label" for="print-include-header">
                                            Include header with title and date
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="print-include-footer" checked>
                                        <label class="form-check-label" for="print-include-footer">
                                            Include footer with page info
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle"></i>
                                    <strong>Print Tips:</strong>
                                    <ul class="mb-0 mt-2">
                                        <li>Use landscape orientation for best results</li>
                                        <li>Enable "Print backgrounds" in browser settings</li>
                                        <li>Save as PDF in the print dialog</li>
                                    </ul>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="start-print">
                                <i class="bi bi-printer"></i> Print
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('printCalendarModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', printDialogHTML);
        
        const modal = new bootstrap.Modal(document.getElementById('printCalendarModal'));
        modal.show();
        
        // Bind print button
        document.getElementById('start-print').addEventListener('click', () => {
            this.printCalendar();
            modal.hide();
        });
    }
    
    getDefaultTitle() {
        const view = this.calendar.view;
        const currentDate = view.currentStart;
        const viewType = view.type;
        
        let title = 'Lab Booking Calendar - ';
        
        switch (viewType) {
            case 'dayGridMonth':
                title += currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
                break;
            case 'timeGridWeek':
                const weekEnd = new Date(currentDate);
                weekEnd.setDate(weekEnd.getDate() + 6);
                title += `Week of ${currentDate.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`;
                break;
            case 'timeGridDay':
                title += currentDate.toLocaleDateString('default', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
                break;
        }
        
        return title;
    }
    
    async printCalendar() {
        try {
            const options = this.getPrintOptions();
            const originalView = this.calendar.view.type;
            
            // Switch to requested view if different
            if (options.view !== 'current' && options.view !== originalView) {
                await this.switchView(options.view);
                await this.waitForRender();
            }
            
            // Prepare for printing
            this.prepareForPrint(options);
            
            // Open print dialog
            window.print();
            
            // Restore after printing
            setTimeout(() => {
                this.restoreAfterPrint();
                if (options.view !== 'current' && options.view !== originalView) {
                    this.calendar.changeView(originalView);
                }
            }, 1000);
            
        } catch (error) {
            console.error('Print error:', error);
            this.showErrorMessage('Failed to prepare calendar for printing.');
        }
    }
    
    getPrintOptions() {
        return {
            title: document.getElementById('print-title').value,
            view: document.getElementById('print-view').value,
            includeHeader: document.getElementById('print-include-header').checked,
            includeFooter: document.getElementById('print-include-footer').checked
        };
    }
    
    async switchView(viewType) {
        const viewMap = {
            'month': 'dayGridMonth',
            'week': 'timeGridWeek',
            'day': 'timeGridDay'
        };
        
        this.calendar.changeView(viewMap[viewType] || viewType);
    }
    
    waitForRender() {
        return new Promise(resolve => {
            setTimeout(resolve, 500);
        });
    }
    
    prepareForPrint(options) {
        // Add print class to body
        document.body.classList.add('calendar-print-mode');
        
        // Add print header if requested
        if (options.includeHeader) {
            this.addPrintHeader(options.title);
        }
        
        // Add print footer if requested
        if (options.includeFooter) {
            this.addPrintFooter();
        }
        
        // Hide non-essential elements
        const elementsToHide = [
            '.btn-toolbar',
            '.resource-filter',
            '.modal',
            '.alert',
            '.toast'
        ];
        
        elementsToHide.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                el.style.display = 'none';
            });
        });
    }
    
    addPrintHeader(title) {
        const header = document.createElement('div');
        header.id = 'print-header';
        header.innerHTML = `
            <div class="print-header">
                <h1>${title}</h1>
                <p>Generated on ${new Date().toLocaleString()}</p>
            </div>
        `;
        
        const calendarContainer = document.getElementById('calendar').parentElement;
        calendarContainer.insertBefore(header, calendarContainer.firstChild);
    }
    
    addPrintFooter() {
        const footer = document.createElement('div');
        footer.id = 'print-footer';
        footer.innerHTML = `
            <div class="print-footer">
                <p>Aperture Booking - Page 1</p>
            </div>
        `;
        
        const calendarContainer = document.getElementById('calendar').parentElement;
        calendarContainer.appendChild(footer);
    }
    
    restoreAfterPrint() {
        // Remove print class
        document.body.classList.remove('calendar-print-mode');
        
        // Remove print elements
        const printHeader = document.getElementById('print-header');
        if (printHeader) {
            printHeader.remove();
        }
        
        const printFooter = document.getElementById('print-footer');
        if (printFooter) {
            printFooter.remove();
        }
        
        // Restore hidden elements
        document.querySelectorAll('[style*="display: none"]').forEach(el => {
            el.style.display = '';
        });
    }
    
    createPrintStyles() {
        const printStyles = `
<style>
@media print {
    .calendar-print-mode {
        margin: 0;
        padding: 0;
    }
    
    .calendar-print-mode .main-content {
        margin: 0;
        padding: 0;
    }
    
    .print-header {
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #000;
        padding-bottom: 10px;
    }
    
    .print-header h1 {
        font-size: 18px;
        margin: 0;
        font-weight: bold;
    }
    
    .print-header p {
        font-size: 10px;
        margin: 5px 0 0 0;
        color: #666;
    }
    
    .print-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        font-size: 8px;
        color: #666;
        border-top: 1px solid #ccc;
        padding-top: 5px;
    }
    
    #calendar {
        font-size: 10px !important;
    }
    
    .fc-event {
        font-size: 8px !important;
        border: 1px solid #333 !important;
        color: #000 !important;
        background: #f0f0f0 !important;
    }
    
    .fc-daygrid-event {
        margin-bottom: 1px !important;
    }
    
    .fc-col-header-cell {
        background: #f5f5f5 !important;
        border: 1px solid #333 !important;
    }
    
    .fc-daygrid-day {
        border: 1px solid #ccc !important;
    }
    
    .fc-toolbar {
        display: none !important;
    }
    
    /* Hide Bootstrap elements that shouldn't print */
    .btn, .modal, .alert, .toast, .dropdown-menu {
        display: none !important;
    }
}
</style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', printStyles);
    }
    
    showErrorMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
}

// Export for use in other modules
window.CalendarPrintFallback = CalendarPrintFallback;