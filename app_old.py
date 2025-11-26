from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
from pathlib import Path

app = FastAPI()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Store current image filename
current_image = {"filename": None}

@app.get("/", response_class=HTMLResponse)
async def get_home():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Annotation Tool</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .controls {
            padding: 20px;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        button:hover {
            background-color: #45a049;
        }
        
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        
        #fileInput {
            display: none;
        }
        
        .zoom-info {
            margin-left: auto;
            font-weight: bold;
            color: #333;
        }
        
        .main-content {
            display: flex;
            gap: 20px;
            padding: 20px;
        }
        
        .canvas-container {
            flex: 1;
            overflow: auto;
            max-height: 600px;
            background-color: #e8e8e8;
            position: relative;
            padding: 20px;
        }
        
        #canvas {
            border: 2px solid #333;
            cursor: crosshair;
            display: block;
            background-color: white;
        }
        
        .coordinates {
            width: 350px;
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 2px solid #e0e0e0;
            overflow-y: auto;
            max-height: 600px;
        }
        
        .coordinates h3 {
            margin-bottom: 10px;
            color: #333;
        }
        
        .coord-list {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }
        
        .coord-item {
            padding: 8px;
            margin-bottom: 10px;
            background-color: #f5f5f5;
            border-left: 3px solid #4CAF50;
            border-radius: 3px;
        }
        
        .no-image {
            text-align: center;
            padding: 100px 20px;
            color: #999;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Image Annotation Tool</h1>
            <p>Upload an image, zoom, and draw rectangles to get coordinates</p>
        </div>
        
        <div class="controls">
            <input type="file" id="fileInput" accept="image/*">
            <button onclick="document.getElementById('fileInput').click()">Upload Image</button>
            <button id="zoomInBtn" onclick="zoomIn()" disabled>Zoom In (+)</button>
            <button id="zoomOutBtn" onclick="zoomOut()" disabled>Zoom Out (-)</button>
            <button id="resetBtn" onclick="resetZoom()" disabled>Reset Zoom</button>
            <button id="clearBtn" onclick="clearRectangles()" disabled>Clear Rectangles</button>
            <span class="zoom-info" id="zoomLevel">Zoom: 100%</span>
        </div>
        
        <div class="main-content">
            <div class="canvas-container" id="canvasContainer">
                <div class="no-image">Please upload an image to begin</div>
                <canvas id="canvas"></canvas>
            </div>
            
            <div class="coordinates">
                <h3>Rectangle Coordinates:</h3>
                <div class="coord-list" id="coordList">
                    No rectangles drawn yet.
                </div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const fileInput = document.getElementById('fileInput');
        const coordList = document.getElementById('coordList');
        const canvasContainer = document.getElementById('canvasContainer');
        
        let image = null;
        let zoomLevel = 1.0;
        let rectangles = [];
        let isDrawing = false;
        let startX, startY;
        let currentRect = null;
        
        fileInput.addEventListener('change', uploadImage);
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
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    loadImage(data.filename);
                } else {
                    alert('Failed to upload image');
                }
            } catch (error) {
                alert('Error uploading image: ' + error);
            }
        }
        
        function loadImage(filename) {
            image = new Image();
            image.onload = function() {
                zoomLevel = 1.0;
                rectangles = [];
                displayImage();
                updateCoordinates();
                enableButtons();
                document.querySelector('.no-image').style.display = 'none';
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
            
            // Redraw rectangles
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
        }
        
        function enableButtons() {
            document.getElementById('zoomInBtn').disabled = false;
            document.getElementById('zoomOutBtn').disabled = false;
            document.getElementById('resetBtn').disabled = false;
            document.getElementById('clearBtn').disabled = false;
        }
        
        function getMousePos(event) {
            const rect = canvas.getBoundingClientRect();
            return {
                x: event.clientX - rect.left,
                y: event.clientY - rect.top
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
            
            // Redraw image and existing rectangles
            displayImage();
            
            // Draw current rectangle
            drawRectangle(startX, startY, pos.x, pos.y);
        }
        
        function stopDrawing(event) {
            if (!isDrawing) return;
            
            const pos = getMousePos(event);
            isDrawing = false;
            
            // Calculate original coordinates (accounting for zoom)
            const x1 = Math.min(startX, pos.x) / zoomLevel;
            const y1 = Math.min(startY, pos.y) / zoomLevel;
            const x2 = Math.max(startX, pos.x) / zoomLevel;
            const y2 = Math.max(startY, pos.y) / zoomLevel;
            
            // Only save if rectangle has some size
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
            }
            
            displayImage();
        }
        
        function drawRectangle(x1, y1, x2, y2) {
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
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
                        <strong>Rectangle ${index + 1}:</strong><br>
                        Top-Left: (${rect.original.x1}, ${rect.original.y1})<br>
                        Bottom-Right: (${rect.original.x2}, ${rect.original.y2})
                    </div>
                `;
            });
            
            coordList.innerHTML = html;
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        current_image["filename"] = file.filename
        return {"filename": file.filename, "message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/image/{filename}")
async def get_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)