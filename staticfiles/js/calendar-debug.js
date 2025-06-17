/**
 * Calendar Debug Helper
 * Aperture Booking
 * 
 * Provides debugging tools for calendar features.
 */

class CalendarDebug {
    constructor() {
        this.init();
    }
    
    init() {
        this.addDebugButton();
        this.bindEvents();
    }
    
    addDebugButton() {
        // Add debug button to calendar toolbar
        const toolbar = document.querySelector('.btn-toolbar .btn-group');
        if (toolbar) {
            const debugBtn = document.createElement('button');
            debugBtn.type = 'button';
            debugBtn.className = 'btn btn-sm btn-outline-warning';
            debugBtn.id = 'debug-btn';
            debugBtn.innerHTML = '<i class="bi bi-bug"></i>';
            debugBtn.title = 'Debug calendar features';
            
            toolbar.appendChild(debugBtn);
            
            debugBtn.addEventListener('click', () => this.showDebugInfo());
        }
    }
    
    bindEvents() {
        // Listen for errors
        window.addEventListener('error', (e) => {
            console.error('Global error:', e);
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e);
        });
    }
    
    showDebugInfo() {
        const debugInfo = {
            libraries: this.checkLibraries(),
            calendarState: this.getCalendarState(),
            domElements: this.checkDOMElements(),
            networkRequests: this.checkNetworkRequests()
        };
        
        console.group('📊 Calendar Debug Information');
        console.table(debugInfo.libraries);
        console.log('Calendar State:', debugInfo.calendarState);
        console.log('DOM Elements:', debugInfo.domElements);
        console.log('Network:', debugInfo.networkRequests);
        console.groupEnd();
        
        // Show debug modal
        this.showDebugModal(debugInfo);
    }
    
    checkLibraries() {
        return {
            'FullCalendar': typeof FullCalendar !== 'undefined' ? '✅ Loaded' : '❌ Missing',
            'html2canvas': typeof html2canvas !== 'undefined' ? '✅ Loaded' : '❌ Missing',
            'jsPDF': typeof window.jsPDF !== 'undefined' ? '✅ Loaded' : '❌ Missing',
            'Bootstrap': typeof bootstrap !== 'undefined' ? '✅ Loaded' : '❌ Missing',
            'jQuery': typeof $ !== 'undefined' ? '✅ Loaded' : '❌ Missing',
            'CalendarShortcuts': typeof CalendarShortcuts !== 'undefined' ? '✅ Loaded' : '❌ Missing',
            'CalendarPDFExport': typeof CalendarPDFExport !== 'undefined' ? '✅ Loaded' : '❌ Missing'
        };
    }
    
    getCalendarState() {
        const calendar = window.calendar; // Assuming calendar is global
        if (!calendar) return 'Calendar not initialized';
        
        return {
            view: calendar.view.type,
            currentDate: calendar.view.currentStart.toISOString(),
            events: calendar.getEvents().length,
            options: {
                selectable: calendar.getOption('selectable'),
                editable: calendar.getOption('editable')
            }
        };
    }
    
    checkDOMElements() {
        const elements = [
            'calendar',
            'resource-filter',
            'pdf-export-btn',
            'print-calendar-btn',
            'help-btn'
        ];
        
        const status = {};
        elements.forEach(id => {
            const element = document.getElementById(id);
            status[id] = element ? '✅ Found' : '❌ Missing';
        });
        
        return status;
    }
    
    checkNetworkRequests() {
        return {
            'CDN Access': navigator.onLine ? '✅ Online' : '❌ Offline',
            'CORS Policy': 'Check browser console for CORS errors',
            'API Endpoints': 'Check network tab for API failures'
        };
    }
    
    showDebugModal(debugInfo) {
        const debugModalHTML = `
            <div class="modal fade" id="debugModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-bug"></i> Calendar Debug Information
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="accordion" id="debugAccordion">
                                <!-- Libraries Section -->
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                                                data-bs-target="#librariesCollapse">
                                            📚 JavaScript Libraries
                                        </button>
                                    </h2>
                                    <div id="librariesCollapse" class="accordion-collapse collapse show">
                                        <div class="accordion-body">
                                            ${this.renderLibraryStatus(debugInfo.libraries)}
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- DOM Elements Section -->
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                                data-bs-target="#domCollapse">
                                            🏗️ DOM Elements
                                        </button>
                                    </h2>
                                    <div id="domCollapse" class="accordion-collapse collapse">
                                        <div class="accordion-body">
                                            ${this.renderDOMStatus(debugInfo.domElements)}
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Calendar State Section -->
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                                data-bs-target="#calendarCollapse">
                                            📅 Calendar State
                                        </button>
                                    </h2>
                                    <div id="calendarCollapse" class="accordion-collapse collapse">
                                        <div class="accordion-body">
                                            <pre>${JSON.stringify(debugInfo.calendarState, null, 2)}</pre>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Quick Tests Section -->
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                                data-bs-target="#testsCollapse">
                                            🧪 Quick Tests
                                        </button>
                                    </h2>
                                    <div id="testsCollapse" class="accordion-collapse collapse">
                                        <div class="accordion-body">
                                            <button class="btn btn-sm btn-primary me-2" onclick="window.debugInstance.testPDF()">
                                                Test PDF Export
                                            </button>
                                            <button class="btn btn-sm btn-secondary me-2" onclick="window.debugInstance.testCanvas()">
                                                Test Canvas Capture
                                            </button>
                                            <button class="btn btn-sm btn-info" onclick="window.debugInstance.testLibraryLoad()">
                                                Test Library Loading
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="window.debugInstance.exportDebugLog()">
                                Export Debug Log
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('debugModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', debugModalHTML);
        
        const modal = new bootstrap.Modal(document.getElementById('debugModal'));
        modal.show();
        
        // Store reference for tests
        window.debugInstance = this;
    }
    
    renderLibraryStatus(libraries) {
        return Object.entries(libraries)
            .map(([name, status]) => `
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <span><strong>${name}</strong></span>
                    <span>${status}</span>
                </div>
            `).join('');
    }
    
    renderDOMStatus(elements) {
        return Object.entries(elements)
            .map(([id, status]) => `
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <span><code>#${id}</code></span>
                    <span>${status}</span>
                </div>
            `).join('');
    }
    
    async testPDF() {
        try {
            console.log('Testing PDF export...');
            const calendarElement = document.getElementById('calendar');
            
            if (!calendarElement) {
                throw new Error('Calendar element not found');
            }
            
            if (typeof html2canvas === 'undefined') {
                throw new Error('html2canvas not loaded');
            }
            
            const canvas = await html2canvas(calendarElement, {
                scale: 1,
                logging: true
            });
            
            console.log('✅ Canvas created successfully:', canvas.width, 'x', canvas.height);
            
            if (typeof window.jsPDF === 'undefined') {
                console.log('⚠️ jsPDF not loaded, loading now...');
                await this.loadJsPDF();
            }
            
            const { jsPDF } = window;
            const pdf = new jsPDF();
            
            console.log('✅ PDF export test completed successfully');
            alert('PDF export test passed! Check console for details.');
            
        } catch (error) {
            console.error('❌ PDF export test failed:', error);
            alert(`PDF export test failed: ${error.message}`);
        }
    }
    
    async testCanvas() {
        try {
            console.log('Testing canvas capture...');
            const calendarElement = document.getElementById('calendar');
            
            const canvas = await html2canvas(calendarElement, {
                scale: 1,
                logging: true
            });
            
            // Show canvas in new window
            const newWindow = window.open('', '_blank');
            newWindow.document.write(`
                <html>
                    <head><title>Canvas Test</title></head>
                    <body>
                        <h2>Canvas Capture Test</h2>
                        <img src="${canvas.toDataURL()}" style="max-width: 100%; border: 1px solid #ccc;">
                    </body>
                </html>
            `);
            
            console.log('✅ Canvas test completed');
            
        } catch (error) {
            console.error('❌ Canvas test failed:', error);
            alert(`Canvas test failed: ${error.message}`);
        }
    }
    
    async testLibraryLoad() {
        try {
            console.log('Testing library loading...');
            
            // Test jsPDF loading
            await this.loadJsPDF();
            console.log('✅ jsPDF loaded successfully');
            
            // Test html2canvas
            if (typeof html2canvas === 'undefined') {
                throw new Error('html2canvas failed to load');
            }
            console.log('✅ html2canvas available');
            
            alert('Library loading test passed!');
            
        } catch (error) {
            console.error('❌ Library loading test failed:', error);
            alert(`Library loading test failed: ${error.message}`);
        }
    }
    
    async loadJsPDF() {
        return new Promise((resolve, reject) => {
            if (typeof window.jsPDF !== 'undefined') {
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    exportDebugLog() {
        const debugInfo = {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            libraries: this.checkLibraries(),
            calendarState: this.getCalendarState(),
            domElements: this.checkDOMElements(),
            networkRequests: this.checkNetworkRequests(),
            errors: this.getConsoleErrors()
        };
        
        const debugText = JSON.stringify(debugInfo, null, 2);
        
        const blob = new Blob([debugText], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `calendar-debug-${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
    
    getConsoleErrors() {
        // This would need to be implemented with a console error collector
        return 'Check browser console for error logs';
    }
}

// Auto-initialize in development - disabled by default
// Uncomment the following lines to enable debug mode in development:
/*
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        new CalendarDebug();
    });
}
*/

// Export for manual initialization
window.CalendarDebug = CalendarDebug;