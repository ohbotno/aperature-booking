/**
 * Calendar PDF Export
 * Aperture Booking
 * 
 * Provides PDF export functionality for calendar views using jsPDF and html2canvas.
 */

class CalendarPDFExport {
    constructor(calendar) {
        this.calendar = calendar;
        this.init();
    }
    
    init() {
        this.addExportButton();
        this.bindEvents();
    }
    
    addExportButton() {
        // Add PDF export button to calendar toolbar
        const toolbar = document.querySelector('.btn-toolbar .btn-group');
        if (toolbar) {
            const exportBtn = document.createElement('button');
            exportBtn.type = 'button';
            exportBtn.className = 'btn btn-sm btn-outline-secondary';
            exportBtn.id = 'pdf-export-btn';
            exportBtn.innerHTML = '<i class="bi bi-file-pdf"></i> PDF';
            exportBtn.title = 'Export calendar to PDF (Press P)';
            
            toolbar.appendChild(exportBtn);
            
            exportBtn.addEventListener('click', () => this.showExportOptions());
        }
    }
    
    bindEvents() {
        // Listen for keyboard shortcut event
        document.addEventListener('calendar:exportPDF', () => {
            this.showExportOptions();
        });
    }
    
    showExportOptions() {
        const optionsModalHTML = `
            <div class="modal fade" id="pdfExportModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-file-pdf me-2"></i> Export Calendar to PDF
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="pdf-export-form">
                                <div class="row">
                                    <div class="col-md-8">
                                        <div class="mb-3">
                                            <label for="export-title" class="form-label fw-semibold">Document Title</label>
                                            <input type="text" class="form-control" id="export-title" 
                                                   value="${this.getDefaultTitle()}" required>
                                            <div class="form-text">This will appear as the main heading in your PDF</div>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label for="export-quality" class="form-label fw-semibold">Export Quality</label>
                                            <select class="form-select" id="export-quality">
                                                <option value="high">High Quality (Recommended)</option>
                                                <option value="medium">Medium Quality</option>
                                                <option value="low">Low Quality (Faster)</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="export-view" class="form-label fw-semibold">View to Export</label>
                                            <select class="form-select" id="export-view">
                                                <option value="current">Current View (${this.calendar.view.type})</option>
                                                <option value="month">Month View</option>
                                                <option value="week">Week View</option>
                                                <option value="day">Day View</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="export-orientation" class="form-label fw-semibold">Page Orientation</label>
                                            <select class="form-select" id="export-orientation">
                                                <option value="landscape">Landscape (Recommended for calendars)</option>
                                                <option value="portrait">Portrait</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-4">
                                    <label class="form-label fw-semibold mb-3">Additional Options</label>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="form-check mb-2">
                                                <input class="form-check-input" type="checkbox" id="include-details" checked>
                                                <label class="form-check-label" for="include-details">
                                                    <strong>Include booking details</strong><br>
                                                    <small class="text-muted">Filter settings and view info in footer</small>
                                                </label>
                                            </div>
                                            <div class="form-check mb-2">
                                                <input class="form-check-input" type="checkbox" id="include-legend" checked>
                                                <label class="form-check-label" for="include-legend">
                                                    <strong>Include status legend</strong><br>
                                                    <small class="text-muted">Color-coded booking status guide</small>
                                                </label>
                                            </div>
                                            <div class="form-check mb-2">
                                                <input class="form-check-input" type="checkbox" id="include-header" checked>
                                                <label class="form-check-label" for="include-header">
                                                    <strong>Enhanced header</strong><br>
                                                    <small class="text-muted">Professional header with timestamp</small>
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check mb-2">
                                                <input class="form-check-input" type="checkbox" id="multi-page" checked>
                                                <label class="form-check-label" for="multi-page">
                                                    <strong>Multi-page support</strong><br>
                                                    <small class="text-muted">Split large calendars across pages</small>
                                                </label>
                                            </div>
                                            <div class="form-check mb-2">
                                                <input class="form-check-input" type="checkbox" id="preserve-colors" checked>
                                                <label class="form-check-label" for="preserve-colors">
                                                    <strong>Preserve colors</strong><br>
                                                    <small class="text-muted">Maintain booking status colors</small>
                                                </label>
                                            </div>
                                            <div class="form-check mb-2">
                                                <input class="form-check-input" type="checkbox" id="compress-pdf">
                                                <label class="form-check-label" for="compress-pdf">
                                                    <strong>Compress PDF</strong><br>
                                                    <small class="text-muted">Smaller file size (may reduce quality)</small>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="alert alert-info border-0">
                                    <div class="d-flex">
                                        <i class="bi bi-info-circle me-2 mt-1"></i>
                                        <div>
                                            <strong>Export Tips:</strong>
                                            <ul class="mb-0 mt-1">
                                                <li>Apply resource filters before exporting to focus on specific equipment</li>
                                                <li>Landscape orientation works best for calendar layouts</li>
                                                <li>Large calendars will automatically split across multiple pages</li>
                                                <li>Export quality affects both file size and image clarity</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="text-center">
                                    <small class="text-muted">
                                        <i class="bi bi-clock me-1"></i>
                                        Current filter: <strong>${this.getCurrentFilter()}</strong> | 
                                        View: <strong>${this.calendar.view.type}</strong>
                                    </small>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer bg-light">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-success" id="start-export">
                                <i class="bi bi-download me-1"></i> Export PDF
                                <span class="spinner-border spinner-border-sm ms-2 d-none" id="export-spinner"></span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('pdfExportModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', optionsModalHTML);
        
        const modal = new bootstrap.Modal(document.getElementById('pdfExportModal'));
        modal.show();
        
        // Bind export button
        document.getElementById('start-export').addEventListener('click', () => {
            this.exportToPDF();
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
    
    async exportToPDF() {
        const startExportBtn = document.getElementById('start-export');
        const spinner = document.getElementById('export-spinner');
        
        try {
            console.log('Starting enhanced PDF export...');
            
            // Show loading states
            startExportBtn.disabled = true;
            spinner.classList.remove('d-none');
            this.showLoadingIndicator('Initializing export...');
            
            const options = this.getExportOptions();
            console.log('Export options:', options);
            
            const originalView = this.calendar.view.type;
            
            // Switch to requested view if different
            if (options.view !== 'current' && options.view !== originalView) {
                this.updateLoadingIndicator('Switching calendar view...');
                console.log('Switching view to:', options.view);
                await this.switchView(options.view);
                await this.waitForRender();
            }
            
            // Prepare calendar for export
            this.updateLoadingIndicator('Preparing calendar for export...');
            console.log('Preparing calendar for export...');
            this.prepareCalendarForExport(options);
            
            // Check if html2canvas is available
            if (typeof html2canvas === 'undefined') {
                throw new Error('html2canvas library not loaded');
            }
            
            // Get quality settings
            const qualitySettings = this.getQualitySettings(options.quality);
            
            // Capture calendar
            this.updateLoadingIndicator('Capturing calendar image...');
            console.log('Capturing calendar with html2canvas...');
            const calendarElement = document.getElementById('calendar');
            if (!calendarElement) {
                throw new Error('Calendar element not found');
            }
            
            const canvas = await html2canvas(calendarElement, {
                ...qualitySettings,
                useCORS: true,
                allowTaint: true,
                backgroundColor: options.preserveColors ? null : '#ffffff',
                width: calendarElement.scrollWidth,
                height: calendarElement.scrollHeight,
                logging: false  // Reduce console noise
            });
            
            console.log(`Canvas created: ${canvas.width}x${canvas.height} (${qualitySettings.scale}x scale)`);
            
            // Create PDF
            this.updateLoadingIndicator('Generating PDF document...');
            console.log('Creating enhanced PDF...');
            const pdf = await this.createPDF(canvas, options);
            
            // Download PDF
            this.updateLoadingIndicator('Preparing download...');
            console.log('Downloading PDF...');
            const filename = this.generateFilename(options.title);
            pdf.save(filename);
            
            // Restore original view
            if (options.view !== 'current' && options.view !== originalView) {
                this.calendar.changeView(originalView);
            }
            
            this.restoreCalendarAfterExport();
            this.hideLoadingIndicator();
            
            this.showSuccessMessage(`PDF exported successfully as "${filename}"!`);
            
        } catch (error) {
            console.error('PDF export error:', error);
            this.hideLoadingIndicator();
            
            // Offer fallback to print if jsPDF failed
            if (error.message.includes('jsPDF')) {
                this.showFallbackDialog();
            } else {
                this.showErrorMessage(`Failed to export PDF: ${error.message}`);
            }
        } finally {
            // Reset button states
            startExportBtn.disabled = false;
            spinner.classList.add('d-none');
        }
    }
    
    getExportOptions() {
        return {
            title: document.getElementById('export-title').value,
            view: document.getElementById('export-view').value,
            orientation: document.getElementById('export-orientation').value,
            quality: document.getElementById('export-quality').value,
            includeDetails: document.getElementById('include-details').checked,
            includeLegend: document.getElementById('include-legend').checked,
            includeHeader: document.getElementById('include-header').checked,
            multiPage: document.getElementById('multi-page').checked,
            preserveColors: document.getElementById('preserve-colors').checked,
            compressPdf: document.getElementById('compress-pdf').checked
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
            setTimeout(resolve, 500); // Give calendar time to render
        });
    }
    
    prepareCalendarForExport(options = {}) {
        const calendarEl = document.getElementById('calendar');
        
        // Add export class for styling
        calendarEl.classList.add('pdf-export-mode');
        
        // Add quality-specific class
        if (options.quality) {
            calendarEl.classList.add(`pdf-export-${options.quality}-quality`);
        }
        
        // Add color preservation class
        if (options.preserveColors) {
            calendarEl.classList.add('pdf-export-preserve-colors');
        }
        
        // Hide interactive elements that shouldn't appear in PDF
        const elementsToHide = [
            '.fc-toolbar-chunk button',
            '.fc-event-resizer',
            '.fc-event-main-frame .fc-event-resizer',
            '.fc-event-harness .fc-event-resizer'
        ];
        
        elementsToHide.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                el.style.setProperty('display', 'none', 'important');
            });
        });
        
        // Enhance text readability for PDF
        document.querySelectorAll('.fc-event-title').forEach(el => {
            el.style.setProperty('font-weight', 'bold', 'important');
            el.style.setProperty('text-shadow', 'none', 'important');
        });
        
        // Ensure proper contrast for PDF
        if (!options.preserveColors) {
            document.querySelectorAll('.fc-event').forEach(el => {
                el.style.setProperty('border', '1px solid #333', 'important');
                el.style.setProperty('color', '#000', 'important');
            });
        }
    }
    
    restoreCalendarAfterExport() {
        const calendarEl = document.getElementById('calendar');
        
        // Remove all export-related classes
        calendarEl.classList.remove('pdf-export-mode');
        calendarEl.classList.remove('pdf-export-high-quality');
        calendarEl.classList.remove('pdf-export-medium-quality');
        calendarEl.classList.remove('pdf-export-low-quality');
        calendarEl.classList.remove('pdf-export-preserve-colors');
        
        // Restore all modified styles
        document.querySelectorAll('[style*="display: none"]').forEach(el => {
            el.style.removeProperty('display');
        });
        
        document.querySelectorAll('.fc-event-title').forEach(el => {
            el.style.removeProperty('font-weight');
            el.style.removeProperty('text-shadow');
        });
        
        document.querySelectorAll('.fc-event').forEach(el => {
            el.style.removeProperty('border');
            el.style.removeProperty('color');
        });
        
        // Force calendar re-render to ensure clean state
        if (this.calendar) {
            this.calendar.render();
        }
    }
    
    async createPDF(canvas, options) {
        // Load jsPDF if not available
        if (typeof window.jsPDF === 'undefined') {
            await this.loadJsPDF();
        }
        
        // Check if jsPDF loaded correctly
        if (typeof window.jsPDF === 'undefined') {
            throw new Error('jsPDF failed to load');
        }
        
        const { jsPDF } = window;
        
        // Create PDF document with enhanced options
        const pdf = new jsPDF({
            orientation: options.orientation,
            unit: 'mm',
            format: 'a4',
            compress: true
        });
        
        // Calculate dimensions
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();
        const margin = 15; // Increased margin for better appearance
        const contentWidth = pageWidth - (margin * 2);
        const headerHeight = 35; // Space for enhanced header
        const footerHeight = 20; // Space for enhanced footer
        const availableHeight = pageHeight - headerHeight - footerHeight;
        
        // Add enhanced header
        this.addEnhancedHeader(pdf, options, pageWidth, margin);
        
        // Calculate image dimensions for multi-page support
        const imgAspectRatio = canvas.width / canvas.height;
        const maxSinglePageHeight = availableHeight - (options.includeLegend ? 40 : 0);
        
        let imgWidth = contentWidth;
        let imgHeight = imgWidth / imgAspectRatio;
        
        // Check if image needs to be split across multiple pages
        if (imgHeight > maxSinglePageHeight) {
            await this.addMultiPageImage(pdf, canvas, {
                pageWidth,
                pageHeight,
                margin,
                headerHeight,
                footerHeight,
                contentWidth,
                availableHeight,
                options
            });
        } else {
            // Single page image
            const imgData = canvas.toDataURL('image/png', 0.95); // Higher quality
            const yPosition = headerHeight;
            
            // Center the image if it's smaller than content width
            const xPosition = imgWidth < contentWidth ? 
                margin + (contentWidth - imgWidth) / 2 : margin;
            
            pdf.addImage(imgData, 'PNG', xPosition, yPosition, imgWidth, imgHeight);
            
            // Add legend below image
            if (options.includeLegend) {
                this.addEnhancedLegend(pdf, margin, yPosition + imgHeight + 10, contentWidth);
            }
        }
        
        // Add enhanced footer
        this.addEnhancedFooter(pdf, pageWidth, pageHeight, margin, options);
        
        // Add metadata
        this.addPDFMetadata(pdf, options);
        
        return pdf;
    }
    
    addLegendToPDF(pdf, x, y) {
        const statusColors = {
            'Pending': '#ffc107',
            'Confirmed': '#28a745',
            'Cancelled': '#6c757d',
            'Rejected': '#dc3545'
        };
        
        pdf.setFontSize(10);
        pdf.setFont(undefined, 'bold');
        pdf.text('Status Legend:', x, y);
        
        let currentY = y + 5;
        Object.entries(statusColors).forEach(([status, color]) => {
            // Draw color box
            pdf.setFillColor(color);
            pdf.rect(x, currentY, 3, 3, 'F');
            
            // Add status text
            pdf.setFont(undefined, 'normal');
            pdf.text(status, x + 5, currentY + 2);
            
            currentY += 5;
        });
    }
    
    addFooterToPDF(pdf, pageWidth, pageHeight, margin) {
        const footerY = pageHeight - 15;
        
        pdf.setFontSize(8);
        pdf.setFont(undefined, 'normal');
        pdf.text('Aperture Booking', margin, footerY);
        pdf.text(`Page 1`, pageWidth - margin - 20, footerY);
    }
    
    addEnhancedHeader(pdf, options, pageWidth, margin) {
        // Add decorative header background
        pdf.setFillColor(240, 240, 240);
        pdf.rect(0, 0, pageWidth, 35, 'F');
        
        // Try to add logo if available
        const logo = document.querySelector('img[alt="Aperture Booking"]');
        if (logo && logo.src) {
            try {
                // Add logo to PDF (24px height, proportional width)
                pdf.addImage(logo.src, 'PNG', margin, 8, 18, 18);
            } catch (e) {
                console.log('Could not add logo to PDF:', e);
            }
        }
        
        // Add title with enhanced styling (offset to account for logo)
        pdf.setFontSize(18);
        pdf.setFont(undefined, 'bold');
        pdf.setTextColor(40, 40, 40);
        const titleX = logo && logo.src ? margin + 25 : margin;
        pdf.text(options.title, titleX, 20);
        
        // Add subtitle/date range  
        pdf.setFontSize(10);
        pdf.setFont(undefined, 'normal');
        pdf.setTextColor(80, 80, 80);
        const subtitle = this.getDateRangeSubtitle();
        pdf.text(subtitle, titleX, 30);
        
        // Add generation info on the right
        pdf.setFontSize(8);
        pdf.setTextColor(120, 120, 120);
        const timestamp = new Date().toLocaleString();
        const textWidth = pdf.getStringUnitWidth(`Generated: ${timestamp}`) * 8 / pdf.internal.scaleFactor;
        pdf.text(`Generated: ${timestamp}`, pageWidth - margin - textWidth, 20);
        
        // Add user info if available
        const user = this.getCurrentUser();
        if (user) {
            const userText = `By: ${user}`;
            const userWidth = pdf.getStringUnitWidth(userText) * 8 / pdf.internal.scaleFactor;
            pdf.text(userText, pageWidth - margin - userWidth, 28);
        }
        
        // Add separator line
        pdf.setDrawColor(200, 200, 200);
        pdf.setLineWidth(0.5);
        pdf.line(margin, 32, pageWidth - margin, 32);
        
        // Reset colors
        pdf.setTextColor(0, 0, 0);
    }
    
    addEnhancedFooter(pdf, pageWidth, pageHeight, margin, options) {
        const totalPages = pdf.internal.getNumberOfPages();
        
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            
            // Add separator line
            pdf.setDrawColor(200, 200, 200);
            pdf.setLineWidth(0.5);
            pdf.line(margin, pageHeight - 18, pageWidth - margin, pageHeight - 18);
            
            // Footer background
            pdf.setFillColor(250, 250, 250);
            pdf.rect(0, pageHeight - 15, pageWidth, 15, 'F');
            
            // Left side - system info
            pdf.setFontSize(8);
            pdf.setFont(undefined, 'normal');
            pdf.setTextColor(100, 100, 100);
            pdf.text('Aperture Booking', margin, pageHeight - 8);
            
            // Center - additional info if requested
            if (options.includeDetails) {
                const centerText = `Filter: ${this.getCurrentFilter()} | View: ${this.calendar.view.type}`;
                const centerWidth = pdf.getStringUnitWidth(centerText) * 8 / pdf.internal.scaleFactor;
                pdf.text(centerText, (pageWidth - centerWidth) / 2, pageHeight - 8);
            }
            
            // Right side - page numbers
            const pageText = totalPages > 1 ? `Page ${i} of ${totalPages}` : 'Page 1';
            const pageWidth_text = pdf.getStringUnitWidth(pageText) * 8 / pdf.internal.scaleFactor;
            pdf.text(pageText, pageWidth - margin - pageWidth_text, pageHeight - 8);
            
            // Add website/contact info
            pdf.setFontSize(6);
            pdf.text('Generated from Lab Booking Calendar', margin, pageHeight - 3);
        }
        
        // Reset to first page
        pdf.setPage(1);
        pdf.setTextColor(0, 0, 0);
    }
    
    addEnhancedLegend(pdf, x, y, contentWidth) {
        const statusConfig = {
            'Pending': { color: '#ffc107', description: 'Awaiting approval' },
            'Approved': { color: '#28a745', description: 'Confirmed booking' },
            'Rejected': { color: '#dc3545', description: 'Booking denied' },
            'Cancelled': { color: '#6c757d', description: 'User cancelled' },
            'Completed': { color: '#17a2b8', description: 'Session finished' }
        };
        
        // Legend header
        pdf.setFontSize(12);
        pdf.setFont(undefined, 'bold');
        pdf.setTextColor(40, 40, 40);
        pdf.text('Booking Status Legend', x, y);
        
        // Legend background
        const legendHeight = Object.keys(statusConfig).length * 6 + 10;
        pdf.setFillColor(248, 249, 250);
        pdf.rect(x, y + 2, contentWidth, legendHeight, 'F');
        
        // Add border
        pdf.setDrawColor(220, 220, 220);
        pdf.setLineWidth(0.5);
        pdf.rect(x, y + 2, contentWidth, legendHeight);
        
        let currentY = y + 10;
        Object.entries(statusConfig).forEach(([status, config]) => {
            // Color box with border
            pdf.setFillColor(config.color);
            pdf.rect(x + 5, currentY - 2, 4, 4, 'F');
            pdf.setDrawColor(200, 200, 200);
            pdf.rect(x + 5, currentY - 2, 4, 4);
            
            // Status name
            pdf.setFontSize(9);
            pdf.setFont(undefined, 'bold');
            pdf.setTextColor(60, 60, 60);
            pdf.text(status, x + 12, currentY);
            
            // Description
            pdf.setFont(undefined, 'normal');
            pdf.setTextColor(100, 100, 100);
            pdf.text(`- ${config.description}`, x + 35, currentY);
            
            currentY += 6;
        });
        
        // Reset colors
        pdf.setTextColor(0, 0, 0);
    }
    
    async addMultiPageImage(pdf, canvas, layout) {
        const { pageWidth, pageHeight, margin, headerHeight, footerHeight, 
                contentWidth, availableHeight, options } = layout;
        
        // Calculate how many vertical sections we need
        const imgAspectRatio = canvas.width / canvas.height;
        const imgWidth = contentWidth;
        const fullImgHeight = imgWidth / imgAspectRatio;
        const sectionsNeeded = Math.ceil(fullImgHeight / availableHeight);
        
        console.log(`Multi-page export: ${sectionsNeeded} pages needed for image`);
        
        // Create sections
        for (let section = 0; section < sectionsNeeded; section++) {
            if (section > 0) {
                pdf.addPage();
                this.addEnhancedHeader(pdf, options, pageWidth, margin);
            }
            
            // Calculate section coordinates
            const sectionHeight = Math.min(availableHeight, fullImgHeight - (section * availableHeight));
            const sourceY = (section * availableHeight) / fullImgHeight * canvas.height;
            const sourceHeight = (sectionHeight / fullImgHeight) * canvas.height;
            
            // Create canvas for this section
            const sectionCanvas = document.createElement('canvas');
            const sectionCtx = sectionCanvas.getContext('2d');
            sectionCanvas.width = canvas.width;
            sectionCanvas.height = sourceHeight;
            
            // Draw section
            sectionCtx.drawImage(canvas, 0, sourceY, canvas.width, sourceHeight, 
                                0, 0, canvas.width, sourceHeight);
            
            // Add to PDF
            const sectionImgData = sectionCanvas.toDataURL('image/png', 0.95);
            pdf.addImage(sectionImgData, 'PNG', margin, headerHeight, imgWidth, sectionHeight);
            
            // Add page indicator for multi-page images
            if (sectionsNeeded > 1) {
                pdf.setFontSize(8);
                pdf.setTextColor(150, 150, 150);
                pdf.text(`Calendar section ${section + 1} of ${sectionsNeeded}`, 
                         margin, headerHeight + sectionHeight + 5);
                pdf.setTextColor(0, 0, 0);
            }
        }
        
        // Add legend on last page if requested
        if (options.includeLegend) {
            const lastPageUsedHeight = headerHeight + 
                (fullImgHeight - ((sectionsNeeded - 1) * availableHeight));
            
            if (pageHeight - lastPageUsedHeight - footerHeight > 50) {
                // Enough space on last page
                this.addEnhancedLegend(pdf, margin, lastPageUsedHeight + 10, contentWidth);
            } else {
                // Add new page for legend
                pdf.addPage();
                this.addEnhancedHeader(pdf, options, pageWidth, margin);
                this.addEnhancedLegend(pdf, margin, headerHeight + 10, contentWidth);
            }
        }
    }
    
    addPDFMetadata(pdf, options) {
        const now = new Date();
        
        pdf.setProperties({
            title: options.title,
            subject: 'Lab Booking Calendar Export',
            author: this.getCurrentUser() || 'Aperture Booking',
            creator: 'Aperture Booking',
            producer: 'Aperture Booking PDF Export',
            creationDate: now,
            modDate: now,
            keywords: 'lab booking, calendar, schedule'
        });
    }
    
    getDateRangeSubtitle() {
        const view = this.calendar.view;
        const currentDate = view.currentStart;
        const viewType = view.type;
        
        switch (viewType) {
            case 'dayGridMonth':
                return currentDate.toLocaleString('default', { 
                    month: 'long', 
                    year: 'numeric' 
                });
            case 'timeGridWeek':
                const weekEnd = new Date(currentDate);
                weekEnd.setDate(weekEnd.getDate() + 6);
                return `${currentDate.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`;
            case 'timeGridDay':
                return currentDate.toLocaleDateString('default', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
            default:
                return 'Calendar View';
        }
    }
    
    getCurrentUser() {
        // Try to get current user from various sources
        const userElement = document.querySelector('[data-user-name]');
        if (userElement) {
            return userElement.dataset.userName;
        }
        
        // Try to get from meta tag
        const userMeta = document.querySelector('meta[name="user-name"]');
        if (userMeta) {
            return userMeta.content;
        }
        
        // Try to get from global variable
        if (window.currentUser) {
            return window.currentUser.name || window.currentUser.username;
        }
        
        return null;
    }
    
    getCurrentFilter() {
        const filterSelect = document.getElementById('resource-filter');
        if (filterSelect && filterSelect.value) {
            const selectedOption = filterSelect.options[filterSelect.selectedIndex];
            return selectedOption.text;
        }
        return 'All Resources';
    }
    
    async loadJsPDF() {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (typeof window.jsPDF !== 'undefined') {
                resolve();
                return;
            }
            
            // Check if script tag already exists
            if (document.getElementById('jspdf-script')) {
                // Wait a bit more for loading
                setTimeout(() => {
                    if (typeof window.jsPDF !== 'undefined') {
                        resolve();
                    } else {
                        reject(new Error('jsPDF script loaded but library not available'));
                    }
                }, 1000);
                return;
            }
            
            // Try multiple CDN sources
            const cdnUrls = [
                'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js',
                'https://unpkg.com/jspdf@2.5.1/dist/jspdf.umd.min.js',
                'https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js'
            ];
            
            this.tryLoadFromCDNs(cdnUrls, 0, resolve, reject);
        });
    }
    
    tryLoadFromCDNs(urls, index, resolve, reject) {
        if (index >= urls.length) {
            reject(new Error('All CDN sources failed to load jsPDF'));
            return;
        }
        
        console.log(`Trying to load jsPDF from: ${urls[index]}`);
        
        const script = document.createElement('script');
        script.id = 'jspdf-script';
        script.src = urls[index];
        
        script.onload = () => {
            console.log('jsPDF script loaded, checking availability...');
            // Give it a moment to initialize
            setTimeout(() => {
                if (typeof window.jsPDF !== 'undefined') {
                    console.log('jsPDF successfully loaded');
                    resolve();
                } else {
                    console.warn('jsPDF script loaded but library not available, trying next CDN...');
                    script.remove();
                    this.tryLoadFromCDNs(urls, index + 1, resolve, reject);
                }
            }, 500);
        };
        
        script.onerror = () => {
            console.warn(`Failed to load jsPDF from ${urls[index]}, trying next CDN...`);
            script.remove();
            this.tryLoadFromCDNs(urls, index + 1, resolve, reject);
        };
        
        document.head.appendChild(script);
    }
    
    showLoadingIndicator(message = 'Generating PDF...') {
        const indicator = document.createElement('div');
        indicator.id = 'pdf-loading-indicator';
        indicator.className = 'position-fixed top-50 start-50 translate-middle';
        indicator.style.zIndex = '9999';
        indicator.innerHTML = `
            <div class="card text-center shadow-lg" style="min-width: 300px;">
                <div class="card-body">
                    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h6 class="card-title mb-2">Exporting Calendar</h6>
                    <p class="mb-0 text-muted" id="loading-message">${message}</p>
                    <div class="progress mt-3" style="height: 6px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 25%"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(indicator);
    }
    
    updateLoadingIndicator(message) {
        const messageEl = document.getElementById('loading-message');
        const progressBar = document.querySelector('#pdf-loading-indicator .progress-bar');
        
        if (messageEl) {
            messageEl.textContent = message;
        }
        
        // Update progress bar based on message
        if (progressBar) {
            let width = '25%';
            if (message.includes('Switching')) width = '40%';
            else if (message.includes('Preparing')) width = '55%';
            else if (message.includes('Capturing')) width = '70%';
            else if (message.includes('Generating')) width = '85%';
            else if (message.includes('download')) width = '95%';
            
            progressBar.style.width = width;
        }
    }
    
    getQualitySettings(quality) {
        const settings = {
            high: { scale: 2, quality: 0.95 },
            medium: { scale: 1.5, quality: 0.85 },
            low: { scale: 1, quality: 0.75 }
        };
        
        return settings[quality] || settings.high;
    }
    
    generateFilename(title) {
        const date = new Date();
        const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
        const cleanTitle = title.replace(/[^a-z0-9\s]/gi, '_').replace(/\s+/g, '_').toLowerCase();
        return `${cleanTitle}_${dateStr}.pdf`;
    }
    
    hideLoadingIndicator() {
        const indicator = document.getElementById('pdf-loading-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showToast(message, 'danger');
    }
    
    showFallbackDialog() {
        const fallbackDialogHTML = `
            <div class="modal fade" id="pdfFallbackModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle text-warning"></i> PDF Export Unavailable
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>PDF export is currently unavailable due to a library loading issue. 
                               This is usually caused by network restrictions or firewall settings.</p>
                            
                            <p><strong>Alternative options:</strong></p>
                            
                            <div class="d-grid gap-2">
                                <button type="button" class="btn btn-primary" id="use-print-fallback">
                                    <i class="bi bi-printer"></i> Use Print to PDF (Recommended)
                                </button>
                                <button type="button" class="btn btn-outline-secondary" id="try-browser-print">
                                    <i class="bi bi-file-pdf"></i> Try Browser Print (Ctrl+P)
                                </button>
                            </div>
                            
                            <div class="alert alert-info mt-3">
                                <small>
                                    <strong>Print to PDF:</strong> Most browsers allow you to "Save as PDF" 
                                    in the print dialog. This creates a high-quality PDF of the calendar.
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('pdfFallbackModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', fallbackDialogHTML);
        
        const modal = new bootstrap.Modal(document.getElementById('pdfFallbackModal'));
        modal.show();
        
        // Bind buttons
        document.getElementById('use-print-fallback').addEventListener('click', () => {
            modal.hide();
            // Trigger print fallback if available
            if (window.CalendarPrintFallback) {
                const printFallback = new CalendarPrintFallback(this.calendar);
                printFallback.showPrintDialog();
            } else {
                window.print();
            }
        });
        
        document.getElementById('try-browser-print').addEventListener('click', () => {
            modal.hide();
            window.print();
        });
    }
    
    showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
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

// Enhanced PDF export specific styles
const pdfExportStyles = `
<style>
    /* Base PDF export styles */
    .pdf-export-mode .fc-toolbar {
        display: none !important;
    }
    
    .pdf-export-mode .fc-event {
        font-size: 11px !important;
        padding: 3px 5px !important;
        margin: 1px !important;
        border-radius: 3px !important;
    }
    
    .pdf-export-mode .fc-event-title {
        font-weight: bold !important;
        line-height: 1.2 !important;
    }
    
    .pdf-export-mode .fc-event-time {
        font-size: 10px !important;
        font-weight: normal !important;
    }
    
    .pdf-export-mode .fc-daygrid-event {
        margin-bottom: 2px !important;
    }
    
    .pdf-export-mode .fc-timegrid-event {
        border-width: 1px !important;
    }
    
    /* Quality-specific styles */
    .pdf-export-high-quality .fc-event {
        font-size: 12px !important;
        padding: 4px 6px !important;
    }
    
    .pdf-export-medium-quality .fc-event {
        font-size: 11px !important;
        padding: 3px 5px !important;
    }
    
    .pdf-export-low-quality .fc-event {
        font-size: 10px !important;
        padding: 2px 4px !important;
    }
    
    /* Color preservation mode */
    .pdf-export-preserve-colors .fc-event {
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }
    
    /* Day grid improvements for PDF */
    .pdf-export-mode .fc-daygrid-day-number {
        font-weight: bold !important;
        font-size: 14px !important;
    }
    
    .pdf-export-mode .fc-col-header-cell {
        font-weight: bold !important;
        background: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .pdf-export-mode .fc-daygrid-day {
        border: 1px solid #dee2e6 !important;
    }
    
    /* Time grid improvements for PDF */
    .pdf-export-mode .fc-timegrid-slot {
        border-color: #e9ecef !important;
    }
    
    .pdf-export-mode .fc-timegrid-slot-label {
        font-size: 11px !important;
        color: #666 !important;
    }
    
    .pdf-export-mode .fc-timegrid-axis {
        background: #f8f9fa !important;
    }
    
    /* Print media styles */
    @media print {
        .pdf-export-mode {
            background: white !important;
        }
        
        .pdf-export-mode .fc-event {
            -webkit-print-color-adjust: exact !important;
            color-adjust: exact !important;
        }
        
        .pdf-export-mode .fc-event:not(.pdf-export-preserve-colors) {
            border: 1px solid #333 !important;
            color: #000 !important;
            background: white !important;
        }
        
        .pdf-export-mode .fc-daygrid-day,
        .pdf-export-mode .fc-col-header-cell {
            border: 1px solid #333 !important;
        }
    }
    
    /* Loading indicator enhancements */
    #pdf-loading-indicator .card {
        backdrop-filter: blur(10px);
        background: rgba(255, 255, 255, 0.95);
        border: none;
    }
    
    #pdf-loading-indicator .progress-bar {
        background: linear-gradient(45deg, #007bff, #0056b3);
    }
</style>
`;

// Add styles to document head
document.head.insertAdjacentHTML('beforeend', pdfExportStyles);

// Export for use in other modules
window.CalendarPDFExport = CalendarPDFExport;