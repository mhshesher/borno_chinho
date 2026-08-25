from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import base64
import json
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from services.supervisor import Supervisor


@asynccontextmanager
async def lifespan(app:FastAPI):

    try:
        print("Application has been started successfully.")
    
    except Exception as e:
        print(f"Error while starting application: {e}")
    
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    return templates.TemplateResponse(request, "index.html")


@app.post("/upload_image")
async def upload_image(uploaded_file: UploadFile=File(...)):

    print(uploaded_file.content_type)

    if not uploaded_file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type."
        )

    content = await uploaded_file.read()

    image_name = uploaded_file.filename

    image_content = base64.b64encode(content).decode("utf-8")

    return {
        "name": image_name,
        "content": image_content
    }
    
@app.post("/upload_json")
async def upload_json(uploaded_file: UploadFile=File(...)):
    
    if not uploaded_file.content_type.endswith("json"):
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type."
        )
    
    content = await uploaded_file.read()

    json_name = uploaded_file.filename

    json_content = json.loads(content.decode("utf-8"))

    return {
        "name": json_name,
        "content": json_content
    }


@app.post("/validate_json")
async def validate_json(data: List[dict]):

    supervisor = Supervisor()

    all_errors = []
    for entry in data:
        try:
            if not supervisor.validate_schema(entry=entry):
                all_errors.append(f"Schema error has been found in: {entry}")
                continue
            
            if not supervisor.validate_category(category=entry["category"]):
                all_errors.append(f"Invalid category has been found in: {entry}")
                continue
            
            errors = []
            if not supervisor.validate_bbox(bbox=entry["bbox"]):
                errors.append("bbox")
            if not supervisor.validate_alignment(alignment=entry["page_alignment"]):
                errors.append("page alignment")
            
            if entry["category"] == "Picture":
                if len(errors)>0:
                    errors_all = ", ".join(errors)
                    all_errors.append(f"Invalid {errors_all} have been found in: {entry}")
                continue

            if not supervisor.validate_alignment(alignment=entry["alignment"]):
                errors.append("alignment")

            if entry["category"] == "Table":
                if len(errors)>0:
                    errors_all = ", ".join(errors)
                    all_errors.append(f"Invalid {errors_all} have been found in: {entry}")
                continue

            if not supervisor.validate_font_size(entry=entry):
                errors.append("font size")
            
            if not supervisor.validate_font_style(font_style=entry["font_style"]):
                errors.append("font style")

            if len(errors)>0:
                errors_all = ", ".join(errors)
                all_errors.append(f"Invalid {errors_all} have been found in: {entry}")
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Unknown error has occured while validating json."
            )

    return {
        "error_count": len(all_errors),
        "error_detail": all_errors
    }


@app.post("/validate_json_dev")
async def validate_json_dev(data: List[dict]):

    supervisor = Supervisor()
    for entry in data:
        if entry["category"]!="Table":
            continue

        errors = supervisor.validate_table_style(table_content=entry["text"])
        print(errors)

    return {"status": "All OK"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
