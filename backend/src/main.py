# backend/src/main.py

import os
import re
import uuid
from typing import Dict, List, Optional
import logging # Added for logging
import json # Added for saving JSON
from contextlib import asynccontextmanager
import time
import asyncio

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

# --- Configuration ---
REQUEST_TIMEOUT_SECONDS = 180  # 3 minutes timeout for query processing
API_TIMEOUT_SECONDS = 120  # 2 minutes timeout per API call

# --- Global genai client (singleton pattern) ---
genai_client: Optional[genai.Client] = None

# --- Request tracking for monitoring ---
active_requests = 0

HISTORY_DIR = "history"   # Define history directory
os.makedirs(HISTORY_DIR, exist_ok=True) # Ensure history dir exists

# --- Application Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize and cleanup resources for the application lifecycle.
    This ensures a single genai client is reused across all requests.
    """
    global genai_client
    # Startup: Initialize global client
    log.info("🚀 Starting up VidExplainAgent backend...")
    try:
        genai_client = genai.Client()
        log.info("✅ Initialized global genai client (singleton pattern)")
    except Exception as e:
        log.error(f"❌ Failed to initialize genai client: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown: Clean up client
    log.info("🔄 Shutting down VidExplainAgent backend...")
    if genai_client:
        genai_client = None
        log.info("✅ Cleaned up genai client resources")

app = FastAPI(
    title="VidExplainAgent API",
    version="0.0.1",
    lifespan=lifespan,  # Add lifespan handler for resource management
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
    tts_provider: Optional[str] = Field("macos", description="TTS provider: 'macos' (native Mac, free, instant) or 'gemini' (premium quality, rate limited)")

class QueryResponse(BaseModel):
    explanation_text: str
    audio_url: str
    referenced_timestamps: List[str] = Field(..., description="List of 'HH:MM:SS' timestamps")


# --- Background Worker ---
def process_and_index_video(job_id: str, video_url: str):
    """
    Background task to process and index video.
    Uses global genai client.
    """
    global genai_client
    
    # Create history directory for this job
    job_history_dir = os.path.join(HISTORY_DIR, job_id)
    os.makedirs(job_history_dir, exist_ok=True)
    
    try:
        if not genai_client:
            log.error("❌ Global genai client not available for background task!")
            raise Exception("Service initialization error - genai client not available")
        
        video_jobs[job_id]["status"] = "processing_video"
        log.info(f"🎬 Processing video for job_id: {job_id}")
        
        # Pass global client to extraction function
        extraction_result = ingestion_pipeline.extract_multimodal_data(
            video_url=video_url,
            history_dir=job_history_dir,
            client=genai_client  # Pass shared client
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
    """Basic health check endpoint"""
    return {"status": "OK", "version": "0.0.1"}

@app.get("/health", tags=["Health Check"])
def health_check():
    """Detailed health check with resource monitoring"""
    global genai_client, active_requests
    return {
        "status": "healthy",
        "version": "0.0.1",
        "genai_client_initialized": genai_client is not None,
        "active_requests": active_requests,
        "timestamp": time.time()
    }

@app.post("/upload-video-url", tags=["Video Processing"], response_model=UploadResponse)
def upload_video(
    request: UploadRequest,
    background_tasks: BackgroundTasks
) -> UploadResponse:
    """
    F2: Submit a YouTube URL for processing.
    Validates the URL format and starts background processing.
    """
    # Validate URL is provided
    if not request.video_url or not request.video_url.strip():
        log.warning("Upload request received without video URL")
        raise HTTPException(
            status_code=400, 
            detail="Please provide a valid YouTube video URL."
        )
    
    # Validate YouTube URL format
    if not YOUTUBE_URL_PATTERN.match(request.video_url):
        log.warning(f"Invalid YouTube URL format: {request.video_url}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid YouTube URL format. Please provide a valid YouTube video URL (e.g., https://www.youtube.com/watch?v=...)"
        )
    
    job_id = str(uuid.uuid4())
    video_jobs[job_id] = {"status": "pending", "video_url": request.video_url}
    log.info(f"📤 Created new video processing job: {job_id} for URL: {request.video_url}")
    
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
async def query_video(request: QueryRequest) -> QueryResponse:
    """
    F4.1: Submits a natural language query for a processed video.
    Now with timeout protection and resource monitoring.
    """
    global active_requests
    active_requests += 1
    
    start_time = time.time()
    log.info(f"📥 Received query request for job_id: {request.job_id} (Active requests: {active_requests})")
    
    try:
        # Wrap the entire query processing in a timeout
        return await asyncio.wait_for(
            _process_query(request, start_time),
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        log.error(f"⏱️ Query timeout after {REQUEST_TIMEOUT_SECONDS}s for job_id: {request.job_id}")
        raise HTTPException(
            status_code=504, 
            detail=f"Request timeout after {REQUEST_TIMEOUT_SECONDS} seconds. Please try again."
        )
    finally:
        active_requests -= 1
        duration = time.time() - start_time
        log.info(f"📊 Request completed in {duration:.2f}s (Active requests: {active_requests})")


async def _process_query(request: QueryRequest, start_time: float) -> QueryResponse:
    """Internal function to process query (for timeout wrapping)"""
    
    # Validate job_id is provided
    if not request.job_id or not request.job_id.strip():
        log.warning("Query request received without job_id")
        raise HTTPException(
            status_code=400, 
            detail="No video has been uploaded yet. Please upload a YouTube video first before asking questions."
        )
    
    # Validate query is provided
    if not request.query or not request.query.strip():
        log.warning(f"Query request received without query text for job_id: {request.job_id}")
        raise HTTPException(
            status_code=400, 
            detail="Please provide a question to ask about the video."
        )
    
    job = video_jobs.get(request.job_id)
    if not job:
        log.warning(f"Job ID not found: {request.job_id}")
        raise HTTPException(
            status_code=404, 
            detail="Video not found. Please upload a YouTube video first, or the video processing session may have expired."
        )
    if job.get("status") != "completed":
        status = job.get("status", "unknown")
        log.info(f"Query attempted on incomplete video. Job ID: {request.job_id}, Status: {status}")
        raise HTTPException(
            status_code=400, 
            detail=f"Video is still being processed. Current status: {status}. Please wait until processing is complete."
        )

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

    # --- Use global singleton client (no creation/cleanup needed) ---
    global genai_client
    if not genai_client:
        log.error("❌ Global genai client not initialized!")
        raise HTTPException(status_code=500, detail="Service initialization error. Please contact administrator.")
    
    try:
        log.info("🔍 Starting text explanation synthesis...")
        # F5.1: Synthesize text explanation (now async)
        explanation_data = await explanation_synthesis.generate_text_explanation(
            client=genai_client,  # Use shared client
            context_chunks=context_chunks, 
            query=query_text,
            history_dir=query_history_dir
        )
        explanation_text = explanation_data["text"]
        log.info(f"✅ Text explanation generated ({len(explanation_text)} chars)")
        
        # Validate TTS provider
        tts_provider = request.tts_provider or "macos"
        if tts_provider not in ["macos", "gemini"]:
            log.warning(f"Invalid TTS provider '{tts_provider}', defaulting to 'macos'")
            tts_provider = "macos"
        
        log.info(f"🎵 Starting audio explanation synthesis with {tts_provider} TTS...")
        # F5.2: Synthesize audio explanation (now async with TTS provider)
        audio_url = await explanation_synthesis.generate_audio_explanation(
            client=genai_client if tts_provider == "gemini" else None,  # Only pass client for Gemini TTS
            text_to_speak=explanation_text,
            history_dir=query_history_dir,
            tts_provider=tts_provider
        )
        log.info(f"✅ Audio explanation generated ({tts_provider} TTS): {audio_url}")

        duration = time.time() - start_time
        log.info(f"✨ Query completed successfully in {duration:.2f}s")
        
        # F5.3: Return the final response
        response = QueryResponse(
            explanation_text=explanation_text,
            audio_url=audio_url,
            referenced_timestamps=explanation_data["timestamps"]
        )
        log.info("📤 Sending response to client...")
        return response
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