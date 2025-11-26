from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import json

app = FastAPI()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store current files
current_files = {"image": None, "json": None}


@app.get("/")
async def get_home():
    """Serve the main HTML file"""
    return FileResponse("static/index.html")


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    try:
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        current_files["image"] = file.filename
        return {"filename": file.filename, "message": "Image uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-json")
async def upload_json(file: UploadFile = File(...)):
    """Upload a JSON annotations file"""
    try:
        file_path = UPLOAD_DIR / file.filename
        content = await file.read()
        json_content = json.loads(content.decode('utf-8'))
        
        with file_path.open("w") as f:
            json.dump(json_content, f, indent=2)
        
        current_files["json"] = file.filename
        return {"filename": file.filename, "content": json_content, "message": "JSON uploaded successfully"}
    except Exception as e:
        print(f"Error while uploading json: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-json")
async def save_json(data: dict):
    """Save JSON annotations"""
    try:
        filename = data.get("filename", "annotations.json")
        json_data = data.get("data", {})
        
        file_path = UPLOAD_DIR / filename
        with file_path.open("w") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        return {"message": "JSON saved successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/image/{filename}")
async def get_image(filename: str):
    """Serve an uploaded image"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
