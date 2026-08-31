import json
import base64
import uvicorn
from typing import List
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException, Request

from services.supervisor import Supervisor
from logger import setup_logging, get_logger
from config import HOST, PORT

setup_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app:FastAPI):

    logger.info("Application started.")

    yield

    logger.info("Application stopped.")
    

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

    if not uploaded_file.content_type.startswith("image/"):
        logger.warning(f"Image upload rejected: '{uploaded_file.filename}' has unsupported type '{uploaded_file.content_type}'.")
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
        logger.warning(f"Json upload rejected: '{uploaded_file.filename}' has unsupported type '{uploaded_file.content_type}'.")
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type."
        )

    content = await uploaded_file.read()

    json_name = uploaded_file.filename

    try:
        json_content = json.loads(content.decode("utf-8"))

    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning(f"Json upload rejected: '{json_name}' could not be parsed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Malformed json file."
        )

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
            
            if entry["category"] == "Picture":
                if len(errors)>0:
                    errors_all = ", ".join(errors)
                    all_errors.append(f"Invalid {errors_all} have been found in: {entry}")
                continue

            if entry["category"] == "Table":
                if len(errors)>0:
                    errors_all = ", ".join(errors)
                    all_errors.append(f"Invalid {errors_all} have been found in: {entry}")
                continue

            if len(errors)>0:
                errors_all = ", ".join(errors)
                all_errors.append(f"Invalid {errors_all} have been found in: {entry}")
        
        except Exception:
            logger.exception(f"Validation failed on entry: {entry}")
            raise HTTPException(
                status_code=500,
                detail="Unknown error has occured while validating json."
            )

    logger.info(f"Validated {len(data)} entries, found {len(all_errors)} errors.")

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
        if len(errors)>0:
            logger.info(f"Table style errors: {errors}")

    return {"status": "All OK"}



if __name__ == "__main__":
    logger.info("\n\n")

    uvicorn.run("app:app", 
                host=HOST, 
                port=PORT, 
                reload=True
            )
