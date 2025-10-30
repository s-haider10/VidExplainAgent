# backend/src/ingestion_pipeline.py

import os
import json
import logging
import re
from typing import List, Dict, Any, Union # Added Union
import chromadb
from google import genai
from google.genai import types
from chromadb.utils import embedding_functions


# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Configuration (Unchanged) ---
db_client = chromadb.PersistentClient(path="./db")
sentence_transformer_model = "BAAI/bge-large-en-v1.5"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=sentence_transformer_model
)
collection_name = "videxplainagent_v1"
collection = db_client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}
)

# --- F2.1: Smart Structured Rich Description ---
# GEMINI_PROMPT (Unchanged)
GEMINI_PROMPT = """
Transcribe the audio from this video, giving timestamps for salient events in the video for a blind student.
Also provide visual descriptions for each event for a blind user, describing any diagrams, models, or visual elements in detail.
Output in a structured JSON string.

The JSON structure should be a list of objects, where each object contains:
1. "timestamp_start_str": "HH:MM:SS" (string)
2. "timestamp_end_str": "HH:MM:SS" (string)
3. "transcript_snippet": "Full transcript for this event." (string)
4. "visual_description": "A detailed description of the visuals during this event." (string)
5. "key_concepts": ["Concept 1", "Concept 2"] (list of strings)

Example:
[
  {
    "timestamp_start_str": "00:01:15",
    "timestamp_end_str": "00:01:25",
    "transcript_snippet": "Now, as we see here, the derivative of x-squared is 2x.",
    "visual_description": "A hand writes 'd/dx(x^2) = 2x' on a digital blackboard. A graph of a parabola y=x^2 is shown to the right.",
    "key_concepts": ["Calculus", "Derivative", "Power Rule"]
  }
]
"""

# --- Modified to accept history_dir and save raw output ---
# --- Returns list on success, dict with error on failure ---
def extract_multimodal_data(video_url: str, history_dir: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Calls the Gemini API to extract structured data from a video URL.
    Saves raw response to history_dir.
    Returns list of extracted data on success, or {'error': message} on failure.
    """
    log.info(f"Starting multimodal extraction for URL: {video_url}")

    raw_response_path = os.path.join(history_dir, "gemini_extraction_raw_output.txt")
    parsed_json_path = os.path.join(history_dir, "gemini_extraction_parsed.json")

    client = genai.Client()
    try:
        video_part = types.Part(
            file_data=types.FileData(file_uri=video_url, mime_type="video/mp4")
        )
        prompt_part = types.Part(text=GEMINI_PROMPT)

        response = client.models.generate_content(
            model='models/gemini-2.5-flash', # Corrected model name if needed
            contents=types.Content(parts=[video_part, prompt_part]),
        )

        raw_text = response.text
        log.info("Gemini response received.")

        # --- Save Raw Response ---
        try:
            with open(raw_response_path, 'w', encoding='utf-8') as f:
                f.write(raw_text)
            log.info(f"Saved raw Gemini extraction response to {raw_response_path}")
        except Exception as save_err:
            log.error(f"Failed to save raw Gemini response: {save_err}")
        # --- End Save ---

        log.info("Attempting to parse JSON from response...")
        # Use regex to find the first valid JSON array (list)
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)

        if not json_match:
            error_msg = "No valid JSON array (starting with '[') found in Gemini response."
            log.error(error_msg)
            log.debug(f"Raw response was saved to {raw_response_path}")
            return {"error": error_msg} # Return error dictionary

        json_string = json_match.group(0)

        try:
            extracted_data = json.loads(json_string)
            # --- Save Parsed JSON ---
            try:
                with open(parsed_json_path, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, indent=2)
                log.info(f"Saved parsed Gemini extraction JSON to {parsed_json_path}")
            except Exception as save_err:
                log.error(f"Failed to save parsed Gemini JSON: {save_err}")
            # --- End Save ---
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse extracted JSON string: {e}"
            log.error(error_msg)
            log.debug(f"Extracted string (attempted parse): {json_string}")
            return {"error": error_msg} # Return error dictionary

        if not isinstance(extracted_data, list):
             error_msg = "Gemini response was valid JSON but not a list as expected."
             log.warning(error_msg)
             return {"error": error_msg} # Return error dictionary

        log.info(f"Successfully extracted {len(extracted_data)} events.")
        return extracted_data # Return data list on success

    except Exception as e:
        error_msg = f"Error during Gemini extraction API call: {e}"
        log.error(error_msg, exc_info=True)
        if "API key" in str(e):
            log.error("Please ensure the GEMINI_API_KEY environment variable is set correctly.")
        # Save the exception to the raw file if possible
        try:
            with open(raw_response_path, 'a', encoding='utf-8') as f:
                f.write("\n\n--- EXCEPTION DURING API CALL ---\n")
                import traceback
                traceback.print_exc(file=f)
        except Exception as save_err:
             log.error(f"Failed to save exception details: {save_err}")
        return {"error": error_msg} # Return error dictionary

# --- F3.1 & F3.2: Semantic Indexing (Unchanged) ---
def index_video_data(job_id: str, video_url: str, extracted_data: List[Dict[str, Any]]):
    # (Function remains unchanged)
    if not extracted_data:
        log.warning(f"No data to index for job_id: {job_id}")
        return

    log.info(f"Starting indexing for job_id: {job_id}. {len(extracted_data)} items to index.")
    documents, metadatas, ids = [], [], []
    for i, event in enumerate(extracted_data):
        try:
            document_text = f"Timestamp: {event.get('timestamp_start_str', 'N/A')}\nTranscript: {event.get('transcript_snippet', '')}\nVisuals: {event.get('visual_description', '')}\nKey Concepts: {', '.join(event.get('key_concepts', []))}"
            documents.append(document_text)
            metadata = {
                "job_id": job_id, "video_url": video_url, "event_index": i,
                "timestamp_start_str": event.get('timestamp_start_str', 'N/A'),
                "timestamp_end_str": event.get('timestamp_end_str', 'N/A'),
                "raw_transcript": event.get('transcript_snippet', ''),
                "raw_visuals": event.get('visual_description', ''),
                "key_concepts": ','.join(event.get('key_concepts', []))
            }
            metadatas.append(metadata)
            ids.append(f"{job_id}_event_{i}")
        except Exception as e:
            log.warning(f"Skipping an event due to malformed data: {e} - Event: {event}")
    if not documents:
        log.error(f"No valid documents were created for indexing job_id: {job_id}")
        return
    try:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        log.info(f"Successfully indexed {len(documents)} documents for job_id: {job_id}")
    except Exception as e:
        log.error(f"Error indexing data in ChromaDB: {e}")

# --- F4.2: Context-Aware Retrieval (Unchanged) ---
def query_chromadb(job_id: str, user_query: str, n_results: int = 5) -> Dict[str, Any]:
    # (Function remains unchanged)
    log.info(f"Querying ChromaDB for job_id: {job_id} with query: {user_query}")
    try:
        results = collection.query(query_texts=[user_query], n_results=n_results, where={"job_id": job_id})
        return results
    except Exception as e:
        log.error(f"Error querying ChromaDB: {e}")
        return {"documents": [], "metadatas": [], "ids": []}