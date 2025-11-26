const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const fileInput = document.getElementById('fileInput');
const jsonFileInput = document.getElementById('jsonFileInput');
const jsonEditor = document.getElementById('jsonEditor');
const imagePlaceholder = document.getElementById('imagePlaceholder');
const annotationsList = document.getElementById('annotationsList');
const annotationCount = document.getElementById('annotationCount');
const fileName = document.getElementById('fileName');
const cooridnatesPanel = document.getElementById('coordinatePanel');

let image = null;
let zoomLevel = 1.0;
let rectangles = [];
let isDrawing = false;
let startX, startY;
let currentImageFile = null;
let currentJsonFile = null;
let selectedAnnotation = null;
let currentCategory = 'text';
// JSON editor zoom state
let jsonZoomLevel = 1.0;
const baseJsonFontSize = 26; // matches CSS default

// Category colors mapping
const categoryColors = {
    'text': '#34d399',
    'section': '#fb923c',
    'image': '#a78bfa',
    'table': '#f87171'
};

fileInput.addEventListener('change', uploadImage);
jsonFileInput.addEventListener('change', uploadJSONFile);
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseleave', stopDrawing);

// Category selection
document.querySelectorAll('.category-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        currentCategory = this.dataset.category;
    });
});

async function uploadImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload-image', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            currentImageFile = data.filename;
            fileName.textContent = file.name;
            loadImage(data.filename);
        } else {
            alert('Failed to upload image');
        }
    } catch (error) {
        alert('Error uploading image: ' + error);
    }
}

async function uploadJSONFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload-json', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            currentJsonFile = data.filename;
            jsonEditor.value = JSON.stringify(data.content, null, 2);
        } else {
            alert('Failed to upload JSON');
        }
    } catch (error) {
        alert('Error uploading JSON: ' + error);
    }
}

function loadImage(filename) {
    image = new Image();
    image.onload = function() {
        zoomLevel = 1.0;
        rectangles = [];
        displayImage();
        updateAnnotationsList();
        enableButtons();
        imagePlaceholder.style.display = 'none';
        canvas.style.display = 'block';
        
        // Re-initialize Lucide icons if new elements were added
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    };
    image.src = '/image/' + filename;
}

function displayImage() {
    if (!image) return;
    
    canvas.width = image.width * zoomLevel;
    canvas.height = image.height * zoomLevel;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    
    rectangles.forEach((rect, index) => {
        const color = categoryColors[rect.category] || '#6366f1';
        const isSelected = selectedAnnotation === index;
        drawRectangle(
            rect.original.x1 * zoomLevel,
            rect.original.y1 * zoomLevel,
            rect.original.x2 * zoomLevel,
            rect.original.y2 * zoomLevel,
            color,
            isSelected
        );
    });
    
    document.getElementById('zoomLevel').textContent = `${Math.round(zoomLevel * 100)}%`;
}

function zoomIn() {
    zoomLevel *= 1.2;
    displayImage();
}

function zoomOut() {
    zoomLevel /= 1.2;
    displayImage();
}

function resetZoom() {
    zoomLevel = 1.0;
    displayImage();
}

function clearRectangles() {
    if (rectangles.length === 0) return;
    
    if (confirm('Are you sure you want to clear all annotations?')) {
        rectangles = [];
        selectedAnnotation = null;
        displayImage();
        updateAnnotationsList();
    }
}

function enableButtons() {
    document.getElementById('zoomInBtn').disabled = false;
    document.getElementById('zoomOutBtn').disabled = false;
    document.getElementById('resetBtn').disabled = false;
    document.getElementById('clearBtn').disabled = false;
}

function getMousePos(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
        x: (event.clientX - rect.left) * scaleX,
        y: (event.clientY - rect.top) * scaleY
    };
}

function startDrawing(event) {
    if (!image) return;
    
    const pos = getMousePos(event);
    startX = pos.x;
    startY = pos.y;
    isDrawing = true;
}

function draw(event) {
    if (!isDrawing) return;
    
    const pos = getMousePos(event);
    displayImage();
    const color = categoryColors[currentCategory] || '#6366f1';
    drawRectangle(startX, startY, pos.x, pos.y, color, false);
}

function stopDrawing(event) {
    if (!isDrawing) return;
    
    const pos = getMousePos(event);
    isDrawing = false;
    
    const x1 = Math.min(startX, pos.x) / zoomLevel;
    const y1 = Math.min(startY, pos.y) / zoomLevel;
    const x2 = Math.max(startX, pos.x) / zoomLevel;
    const y2 = Math.max(startY, pos.y) / zoomLevel;
    
    if (Math.abs(pos.x - startX) > 2 && Math.abs(pos.y - startY) > 2) {
        rectangles.push({
            original: {
                x1: Math.round(x1),
                y1: Math.round(y1),
                x2: Math.round(x2),
                y2: Math.round(y2)
            },
            category: currentCategory
        });
        
        // Auto-select the latest rectangle
        selectedAnnotation = rectangles.length - 1;
        updateCoordinatesDisplay();
        // Refresh annotations list and ensure coordinates panel visibility
        updateAnnotationsList();
    }
    
    // ensure coordinates panel is visible if there are annotations
    if (cooridnatesPanel) cooridnatesPanel.style.display = rectangles.length > 0 ? 'block' : 'none';

    displayImage();
}

function drawRectangle(x1, y1, x2, y2, color, isSelected) {
    ctx.strokeStyle = color;
    ctx.lineWidth = isSelected ? 4 : 3;
    
    if (isSelected) {
        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
    }
    
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.shadowBlur = 0;
}

function updateAnnotationsList() {
    if (!annotationCount) return;
    
    annotationCount.textContent = `(${rectangles.length})`;
    
    if (!annotationsList) return;
    
    if (rectangles.length === 0) {
        annotationsList.innerHTML = `
            <div class="empty-state">
                <i data-lucide="layers"></i>
                <p>No annotations yet</p>
                <small>Draw rectangles on the image</small>
            </div>
        `;
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        // hide coordinates panel when no annotations exist
        if (cooridnatesPanel) cooridnatesPanel.style.display = 'none';
        return;
    }
    
    let html = '';
    rectangles.forEach((rect, index) => {
        const color = categoryColors[rect.category] || '#6366f1';
        const isSelected = selectedAnnotation === index;
        html += `
            <div class="annotation-item ${isSelected ? 'selected' : ''}" 
                 onclick="selectAnnotation(${index})"
                 style="border-left-color: ${color};">
                <div class="annotation-header">
                    <span class="annotation-category">${capitalizeFirst(rect.category)}</span>
                    <span class="annotation-number">#${index + 1}</span>
                </div>
                <div class="annotation-coords">
                    [${rect.original.x1}, ${rect.original.y1}] → [${rect.original.x2}, ${rect.original.y2}]
                </div>
            </div>
        `;
    });
    
    annotationsList.innerHTML = html;
    // show coordinates panel because there are annotations
    if (cooridnatesPanel) cooridnatesPanel.style.display = rectangles.length > 0 ? 'block' : 'none';
}

function closeCoordinatesPanel() {
    if (cooridnatesPanel) cooridnatesPanel.style.display = 'none';
}

function selectAnnotation(index) {
    selectedAnnotation = index;
    updateAnnotationsList();
    updateCoordinatesDisplay();
    displayImage();
}

function updateCoordinatesDisplay() {
    const coordinatesDisplay = document.getElementById('coordinatesDisplay');
    
    if (selectedAnnotation === null || !rectangles[selectedAnnotation]) {
        coordinatesDisplay.innerHTML = `
            <div class="coord-empty">
                <p>No rectangle selected</p>
            </div>
        `;
        return;
    }
    
    const rect = rectangles[selectedAnnotation];
    coordinatesDisplay.innerHTML = `
        <div class="coord-item">
            <div class="coord-label">Upper-Left Point</div>
            <div class="coord-value">X: ${rect.original.x1}, Y: ${rect.original.y1}</div>
        </div>
        <div class="coord-item">
            <div class="coord-label">Bottom-Right Point</div>
            <div class="coord-value">X: ${rect.original.x2}, Y: ${rect.original.y2}</div>
        </div>
    `;
}

function syntaxHighlightJSON(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="json-' + cls + '">' + match + '</span>';
    });
}

function displayColorfulJSON(jsonData) {
    const jsonEditor = document.getElementById('jsonEditor');
    const jsonString = JSON.stringify(jsonData, null, 2);
    jsonEditor.value = jsonString;
    
    // Create a styled version for display
    const highlighted = syntaxHighlightJSON(jsonString);
    const jsonDisplay = document.getElementById('jsonEditorDisplay');
    if (jsonDisplay) {
        jsonDisplay.innerHTML = highlighted;
    }
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function updateJSON() {
    const annotations = {
        image: currentImageFile || "no_image_loaded",
        rectangles: rectangles.map((rect, index) => ({
            id: index + 1,
            category: rect.category,
            top_left: {
                x: rect.original.x1,
                y: rect.original.y1
            },
            bottom_right: {
                x: rect.original.x2,
                y: rect.original.y2
            }
        }))
    };
    
    jsonEditor.value = JSON.stringify(annotations, null, 2);
}

function triggerSaveDialog() {
    try {
        const jsonData = JSON.parse(jsonEditor.value);
        const filename = currentJsonFile || 'annotations.json';
        
        const dataStr = JSON.stringify(jsonData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', filename);
        linkElement.click();
    } catch (error) {
        alert('Error saving JSON: ' + error.message);
    }
}

async function saveJSON() {
    try {
        const jsonData = JSON.parse(jsonEditor.value);
        
        const filename = currentJsonFile || 'annotations.json';
        
        const response = await fetch('/save-json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                data: jsonData
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            currentJsonFile = result.filename;
            
            // Show success feedback
            const saveBtn = document.getElementById('saveJsonBtn');
            const originalHTML = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i data-lucide="check"></i> Saved!';
            saveBtn.style.background = '#34d399';
            
            // Re-initialize icon
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            
            setTimeout(() => {
                saveBtn.innerHTML = originalHTML;
                saveBtn.style.background = '';
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }, 2000);
        } else {
            alert('Failed to save JSON');
        }
    } catch (error) {
        alert('Invalid JSON format: ' + error.message);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Delete selected annotation with Delete or Backspace key
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedAnnotation !== null) {
        e.preventDefault();
        rectangles.splice(selectedAnnotation, 1);
        selectedAnnotation = null;
        displayImage();
        updateAnnotationsList();
        updateCoordinatesDisplay();
    }
    
    // Zoom shortcuts
    if (e.ctrlKey || e.metaKey) {
        if (e.key === '=' || e.key === '+') {
            e.preventDefault();
            if (image) zoomIn();
        } else if (e.key === '-' || e.key === '_') {
            e.preventDefault();
            if (image) zoomOut();
        } else if (e.key === '0') {
            e.preventDefault();
            if (image) resetZoom();
        }
        
        // Find and Replace toggle (Ctrl+H or Cmd+H)
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            const container = document.getElementById('findReplaceContainer');
            if (container.style.display === 'none') {
                container.style.display = 'flex';
                document.getElementById('findInput').focus();
            } else {
                closeFindReplace();
            }
        }
    }
});

// Initialize on page load
window.addEventListener('load', function() {
    jsonEditor.value = '';
    // initialize JSON editor font-size based on zoom
    if (jsonEditor) {
        jsonEditor.style.fontSize = `${baseJsonFontSize * jsonZoomLevel}px`;
    }
    // initialize JSON zoom display
    const zEl = document.getElementById('jsonZoomLevel');
    if (zEl) zEl.textContent = `${Math.round(jsonZoomLevel * 100)}%`;
});

// JSON zoom functions
function updateJsonZoomDisplay() {
    const zEl = document.getElementById('jsonZoomLevel');
    if (zEl) zEl.textContent = `${Math.round(jsonZoomLevel * 100)}%`;
    if (jsonEditor) jsonEditor.style.fontSize = `${baseJsonFontSize * jsonZoomLevel}px`;
}

function zoomJsonIn() {
    jsonZoomLevel = Math.min(3.0, jsonZoomLevel * 1.15);
    updateJsonZoomDisplay();
}

function zoomJsonOut() {
    jsonZoomLevel = Math.max(0.5, jsonZoomLevel / 1.15);
    updateJsonZoomDisplay();
}

function resetJsonZoom() {
    jsonZoomLevel = 1.0;
    updateJsonZoomDisplay();
}

// Find and Replace Functions
let findIndex = 0;

function closeFindReplace() {
    document.getElementById('findReplaceContainer').style.display = 'none';
    jsonEditor.focus();
}

function findMatches(searchTerm) {
    const text = jsonEditor.value;
    const matches = [];
    let start = 0;
    
    while ((start = text.indexOf(searchTerm, start)) !== -1) {
        matches.push(start);
        start += searchTerm.length;
    }
    
    return matches;
}

function updateFindCounter() {
    const findInput = document.getElementById('findInput').value;
    const counter = document.getElementById('findCounter');
    
    if (!findInput) {
        counter.textContent = '';
        return;
    }
    
    const matches = findMatches(findInput);
    counter.textContent = matches.length > 0 ? `${findIndex + 1} of ${matches.length}` : 'No matches';
}

function findNext() {
    const findInput = document.getElementById('findInput').value;
    if (!findInput) return;
    
    const matches = findMatches(findInput);
    if (matches.length === 0) return;
    
    findIndex = (findIndex + 1) % matches.length;
    const start = matches[findIndex];
    
    jsonEditor.setSelectionRange(start, start + findInput.length);
    jsonEditor.focus();
    updateFindCounter();
}

function findPrev() {
    const findInput = document.getElementById('findInput').value;
    if (!findInput) return;
    
    const matches = findMatches(findInput);
    if (matches.length === 0) return;
    
    findIndex = (findIndex - 1 + matches.length) % matches.length;
    const start = matches[findIndex];
    
    jsonEditor.setSelectionRange(start, start + findInput.length);
    jsonEditor.focus();
    updateFindCounter();
}

function replaceOne() {
    const findInput = document.getElementById('findInput').value;
    const replaceInput = document.getElementById('replaceInput').value;
    
    if (!findInput) return;
    
    const matches = findMatches(findInput);
    if (matches.length === 0) return;
    
    const start = matches[findIndex];
    const before = jsonEditor.value.substring(0, start);
    const after = jsonEditor.value.substring(start + findInput.length);
    
    jsonEditor.value = before + replaceInput + after;
    updateFindCounter();
    findNext();
}

function replaceAll() {
    const findInput = document.getElementById('findInput').value;
    const replaceInput = document.getElementById('replaceInput').value;
    
    if (!findInput) return;
    
    jsonEditor.value = jsonEditor.value.replaceAll(findInput, replaceInput);
    findIndex = 0;
    updateFindCounter();
}

// Set up find input listener for counter update
document.addEventListener('DOMContentLoaded', function() {
    const findInput = document.getElementById('findInput');
    if (findInput) {
        findInput.addEventListener('input', function() {
            findIndex = 0;
            updateFindCounter();
        });
    }
});