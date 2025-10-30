# backend/src/main.py

import os
import re
import uuid
from typing import Dict, List, Optional
import logging # Added for logging
import json # Added for saving JSON

# --- Load .env file BEFORE any other modules are imported ---
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google import genai # Import genai

from . import ingestion_pipeline
from . import explanation_synthesis

# --- Setup ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

HISTORY_DIR = "history"   # Define history directory
os.makedirs(HISTORY_DIR, exist_ok=True) # Ensure history dir exists

app = FastAPI(
    title="VidExplainAgent API",
    version="0.0.1",
)

# --- CORS (Unchanged) ---
origins = [
    "http://localhost:3000",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Static Directory (Unchanged) ---
os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Job Store (Unchanged) ---
video_jobs: Dict[str, Dict] = {}

# --- Regex (Unchanged) ---
YOUTUBE_URL_PATTERN = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
)

# --- API Models (Unchanged) ---
class UploadRequest(BaseModel):
    video_url: str = Field(..., example="https://www.youtube.com/watch?v=rHLEWRxRGiM")

class UploadResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    message: str | None = None

class QueryRequest(BaseModel):
    job_id: str
    query: str
    timestamp: Optional[float] = Field(None, description="Optional timestamp in seconds for context.")

class QueryResponse(BaseModel):
    explanation_text: str
    audio_url: str
    referenced_timestamps: List[str] = Field(..., description="List of 'HH:MM:SS' timestamps")


# --- Background Worker ---
def process_and_index_video(job_id: str, video_url: str):
    # Create history directory for this job
    job_history_dir = os.path.join(HISTORY_DIR, job_id)
    os.makedirs(job_history_dir, exist_ok=True)
    try:
        video_jobs[job_id]["status"] = "processing_video"
        # Pass history dir to extraction function
        extraction_result = ingestion_pipeline.extract_multimodal_data(
            video_url=video_url,
            history_dir=job_history_dir # Pass directory path
        )
        # Check if result is the expected data list
        if isinstance(extraction_result, list):
             extracted_data = extraction_result
        elif isinstance(extraction_result, dict) and "error" in extraction_result:
             raise Exception(extraction_result["error"]) # Raise error if extraction failed
        else:
             raise Exception("Unexpected return type from extract_multimodal_data")


        if not extracted_data:
            raise Exception("No data extracted from video.")

        video_jobs[job_id]["status"] = "indexing_data"
        ingestion_pipeline.index_video_data(job_id, video_url, extracted_data)
        video_jobs[job_id]["status"] = "completed"
        video_jobs[job_id]["message"] = f"Successfully processed {len(extracted_data)} events."

    except Exception as e:
        log.error(f"Background processing error: {e}", exc_info=True)
        video_jobs[job_id]["status"] = "failed"
        video_jobs[job_id]["message"] = str(e)
        # Save error info
        error_path = os.path.join(job_history_dir, "extraction_error.txt")
        try:
            with open(error_path, mode='w', encoding='utf-8') as f:
                 f.write(f"Error during video processing:\n{str(e)}\n\nTraceback:\n")
                 import traceback
                 traceback.print_exc(file=f)
        except Exception as save_err:
            log.error(f"Failed to save extraction error log: {save_err}")


# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "OK", "version": "0.0.1"}

@app.post("/upload-video-url", tags=["Video Processing"], response_model=UploadResponse)
def upload_video(
    request: UploadRequest,
    background_tasks: BackgroundTasks
) -> UploadResponse:
    # (Unchanged)
    if not YOUTUBE_URL_PATTERN.match(request.video_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL format.")
    job_id = str(uuid.uuid4())
    video_jobs[job_id] = {"status": "pending", "video_url": request.video_url}
    background_tasks.add_task(process_and_index_video, job_id, request.video_url)
    return UploadResponse(job_id=job_id, status="processing")

@app.get("/video-status/{job_id}", tags=["Video Processing"], response_model=JobStatusResponse)
def get_video_status(job_id: str) -> JobStatusResponse:
    # (Unchanged)
    job = video_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return JobStatusResponse(
        job_id=job_id,
        status=job.get("status"),
        message=job.get("message")
    )

@app.post("/query-video", tags=["Query & Explanation"], response_model=QueryResponse)
def query_video(request: QueryRequest) -> QueryResponse:
    """
    F4.1: Submits a natural language query for a processed video.
    """
    job = video_jobs.get(request.job_id)
    # ... (all job checks) ...
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Video is still processing. Status: {job.get('status')}")

    # ... (all query_text and ChromaDB logic) ...
    query_text = request.query
    if request.timestamp:
        minutes = int(request.timestamp // 60)
        seconds = int(request.timestamp % 60)
        time_str = f"{minutes:02}:{seconds:02}"
        query_text = f"At or around timestamp {time_str}, {request.query}"
    
    query_results = ingestion_pipeline.query_chromadb(
        job_id=request.job_id,
        user_query=query_text
    )
    
    context_chunks = query_results.get("metadatas", [[]])[0]
    if not context_chunks:
        raise HTTPException(status_code=404, detail="No relevant context found for this query in the video.")
        
    # ... (all history saving logic) ...
    query_id = str(uuid.uuid4())
    query_history_dir = os.path.join(HISTORY_DIR, request.job_id, "queries", query_id)
    os.makedirs(query_history_dir, exist_ok=True)
    query_info = {
        "query": request.query,
        "timestamp": request.timestamp,
        "processed_query_text": query_text,
        "retrieved_context": context_chunks 
    }
    query_info_path = os.path.join(query_history_dir, "query_info.json")
    try:
        with open(query_info_path, mode='w', encoding='utf-8') as f:
            json.dump(query_info, f, indent=2)
    except Exception as save_err:
        log.error(f"Failed to save query info log: {save_err}")

    # --- FIX: REMOVE try...finally and client.close() ---
    client = genai.Client()
    try:
        # F5.1: Synthesize text explanation
        explanation_data = explanation_synthesis.generate_text_explanation(
            client=client, 
            context_chunks=context_chunks, 
            query=query_text,
            history_dir=query_history_dir
        )
        explanation_text = explanation_data["text"]
        
        # F5.2: Synthesize audio explanation
        audio_url = explanation_synthesis.generate_audio_explanation(
            client=client, 
            text_to_speak=explanation_text,
            history_dir=query_history_dir
        )

        # F5.3: Return the final response
        return QueryResponse(
            explanation_text=explanation_text,
            audio_url=audio_url,
            referenced_timestamps=explanation_data["timestamps"]
        )
    except Exception as e:
        log.error(f"Error during query synthesis: {e}", exc_info=True)
        # (Error saving logic is fine)
        error_path = os.path.join(query_history_dir, "query_error.txt")
        try:
            with open(error_path, mode='w', encoding='utf-8') as f:
                 f.write(f"Error during query processing:\n{str(e)}\n\nTraceback:\n")
                 import traceback
                 traceback.print_exc(file=f)
        except Exception as save_err:
            log.error(f"Failed to save query error log: {save_err}")
        raise HTTPException(status_code=500, detail=f"Error during synthesis: {str(e)}")
    # --- END FIX ---