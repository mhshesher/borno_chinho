const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const fileInput = document.getElementById('fileInput');
const jsonFileInput = document.getElementById('jsonFileInput');
const jsonEditor = document.getElementById('jsonEditor');
const coordList = document.getElementById('coordList');
const imagePlaceholder = document.getElementById('imagePlaceholder');

let image = null;
let zoomLevel = 1.0;
let rectangles = [];
let isDrawing = false;
let startX, startY;
let currentImageFile = null;
let currentJsonFile = null;

fileInput.addEventListener('change', uploadImage);
jsonFileInput.addEventListener('change', uploadJSONFile);
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseleave', stopDrawing);

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
        updateCoordinates();
        updateJSON();
        enableButtons();
        imagePlaceholder.style.display = 'none';
        canvas.style.display = 'block';
    };
    image.src = '/image/' + filename;
}

function displayImage() {
    if (!image) return;
    
    canvas.width = image.width * zoomLevel;
    canvas.height = image.height * zoomLevel;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    
    rectangles.forEach(rect => {
        drawRectangle(
            rect.original.x1 * zoomLevel,
            rect.original.y1 * zoomLevel,
            rect.original.x2 * zoomLevel,
            rect.original.y2 * zoomLevel
        );
    });
    
    document.getElementById('zoomLevel').textContent = `Zoom: ${Math.round(zoomLevel * 100)}%`;
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
    rectangles = [];
    displayImage();
    updateCoordinates();
    updateJSON();
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
    drawRectangle(startX, startY, pos.x, pos.y);
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
            }
        });
        
        updateCoordinates();
        updateJSON();
    }
    
    displayImage();
}

function drawRectangle(x1, y1, x2, y2) {
    ctx.strokeStyle = '#667eea';
    ctx.lineWidth = 3;
    ctx.shadowColor = 'rgba(102, 126, 234, 0.5)';
    ctx.shadowBlur = 8;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.shadowBlur = 0;
}

function updateCoordinates() {
    if (rectangles.length === 0) {
        coordList.innerHTML = 'No rectangles drawn yet.';
        return;
    }
    
    let html = '';
    rectangles.forEach((rect, index) => {
        html += `
            <div class="coord-item">
                <strong>Rectangle ${index + 1}:</strong>
                Top-Left: (${rect.original.x1}, ${rect.original.y1})
                Bottom-Right: (${rect.original.x2}, ${rect.original.y2})
            </div>
        `;
    });
    
    coordList.innerHTML = html;
}

function updateJSON() {
    const annotations = {
        image: currentImageFile || "no_image_loaded",
        rectangles: rectangles.map((rect, index) => ({
            id: index + 1,
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

async function saveJSON() {
    try {
        const jsonData = JSON.parse(jsonEditor.value);
        
        // Use the current JSON filename or default to annotations.json
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
            // Update the current filename to the saved one
            currentJsonFile = result.filename;
            alert('JSON saved successfully to: ' + result.filename);
        } else {
            alert('Failed to save JSON');
        }
    } catch (error) {
        alert('Invalid JSON format: ' + error.message);
    }
}
