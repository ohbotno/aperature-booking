# Calendar Features Troubleshooting Guide

## PDF Export Issues

### Quick Debugging Steps

1. **Open Browser Console** (F12 → Console tab)
2. **Look for the debug button** (🐛 icon) in the calendar toolbar
3. **Click the debug button** to see feature status
4. **Run built-in tests** from the debug modal

### Common Issues and Solutions

#### 1. PDF Export Button Missing
- **Cause**: JavaScript not loading properly
- **Solution**: Check browser console for JavaScript errors
- **Check**: Ensure static files are being served correctly

#### 2. "html2canvas library not loaded" Error
- **Cause**: CDN blocked or network issues
- **Solution**: Check network connectivity
- **Alternative**: Use the Print button instead for PDF generation

#### 3. PDF Export Fails Silently
- **Cause**: Browser security restrictions
- **Solution**: 
  - Allow popups for the site
  - Check if "Save to PDF" is available in browser print dialog
  - Try using the Print fallback feature

#### 4. Blank or Corrupted PDF
- **Cause**: CSS/rendering issues
- **Solution**:
  - Wait for calendar to fully load before exporting
  - Try different view modes (month/week/day)
  - Check if events are visible on screen

### Fallback Options

If PDF export fails, use these alternatives:

#### Option 1: Print to PDF (Recommended)
1. Click the **Print** button (🖨️) in calendar toolbar
2. Choose print options in the modal
3. Click **Print**
4. In browser print dialog, select "Save as PDF"
5. Choose landscape orientation for best results

#### Option 2: Browser Screenshot
1. Use browser's built-in screenshot feature
2. Press `Ctrl+Shift+S` (Firefox) or `Ctrl+Shift+I` → Screenshot tool
3. Select calendar area
4. Save as image

#### Option 3: Manual Browser Print
1. Press `Ctrl+P` to open print dialog
2. Select "Save as PDF" as destination
3. Choose landscape orientation
4. Enable "Print backgrounds" option

### Debug Information

The debug modal provides:

- **Library Status**: Shows which JavaScript libraries loaded successfully
- **DOM Elements**: Verifies all calendar components are present
- **Calendar State**: Current view, events, and configuration
- **Quick Tests**: Interactive tests for PDF and canvas functionality

### Environment-Specific Issues

#### Development (localhost)
- Debug button automatically appears
- More detailed console logging
- CORS restrictions may apply to CDN resources

#### Production
- Debug button hidden by default
- Enable by adding `?debug=1` to URL
- Check if CDN resources are accessible
- Verify static file serving is configured correctly

### Browser Compatibility

#### Chrome/Edge
- Full PDF export support
- Best performance and compatibility

#### Firefox
- PDF export supported
- May require popup permission
- Print fallback works reliably

#### Safari
- Limited PDF export support
- Use print fallback for best results
- May require additional security permissions

### Manual Testing Commands

Open browser console and run these commands:

```javascript
// Test if libraries are loaded
console.log('html2canvas:', typeof html2canvas);
console.log('jsPDF:', typeof window.jsPDF);

// Test calendar access
console.log('Calendar:', window.calendar);

// Test canvas capture
html2canvas(document.getElementById('calendar')).then(canvas => {
    console.log('Canvas created:', canvas.width, 'x', canvas.height);
});
```

### Performance Tips

1. **Reduce calendar complexity** before export:
   - Filter to specific resources
   - Use day or week view for detailed exports
   - Ensure all events are visible on screen

2. **Browser optimization**:
   - Close unnecessary tabs
   - Disable browser extensions temporarily
   - Clear browser cache if issues persist

3. **Network considerations**:
   - Ensure stable internet connection for CDN resources
   - Try export during low network usage times

### Getting Help

If issues persist:

1. **Export debug log** using the debug modal
2. **Check browser console** for error messages
3. **Try different browsers** to isolate compatibility issues
4. **Use print fallback** as reliable alternative

### Keyboard Shortcuts Troubleshooting

#### Shortcuts Not Working
- **Check**: Are you typing in a form field? Shortcuts are disabled in inputs
- **Check**: Is a modal open? Press Esc to close modals first
- **Solution**: Click outside any form fields and try again

#### Help Modal Not Showing
- **Shortcut**: Press `H` or `?` keys
- **Button**: Click the help button (❓) in toolbar
- **Check**: Ensure Bootstrap JavaScript is loaded

### Success Indicators

Working features should show:
- ✅ PDF button appears in toolbar
- ✅ Print button appears in toolbar
- ✅ Help button shows shortcut modal
- ✅ Debug button appears (in development)
- ✅ Keyboard shortcuts respond
- ✅ Export modals open without errors

### Last Resort: Simple Print

If all else fails, use basic browser print:

1. Go to calendar page
2. Press `Ctrl+P` (or `Cmd+P` on Mac)
3. Select "Save as PDF"
4. Choose landscape orientation
5. Print

This method always works but has limited formatting options.