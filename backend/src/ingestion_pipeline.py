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
# GEMINI_PROMPT - Enhanced for comprehensive, accessible extraction
GEMINI_PROMPT = """
You are an expert educational content analyzer creating rich, accessible descriptions for Blind and Low Vision (BLV) learners.

Your task is to transcribe and analyze this video comprehensively, capturing:
- Complete audio transcription with precise timestamps
- Detailed visual descriptions (spatial layout, colors, movements, text, diagrams)
- Speaker/person information (who appears, their role, visual characteristics)
- Technical content with precise notation (formulas, equations, code, diagrams)
- Educational context (difficulty level, prerequisites, concept relationships)
- Cognitive summaries for quick understanding

Output a structured JSON list where each object represents a significant event/segment.

CRITICAL GUIDELINES:
1. VISUAL DESCRIPTIONS: Describe ALL visual elements in detail for BLV users:
   - Spatial relationships (left/right, top/bottom, foreground/background)
   - Colors, shapes, sizes, and movements
   - Text content (equations, labels, code, diagrams) - transcribe character-by-character
   - Gestures, pointing, or physical demonstrations
   - Diagrams: describe structure, axes, labels, relationships between components

2. SPEAKER TRACKING: When a new person appears or speaks:
   - Identify them if name/role is mentioned or shown
   - Describe their visual appearance (clothing, position, distinctive features)
   - Note changes in speakers throughout the video

3. TECHNICAL CONTENT: For formulas, equations, code, or diagrams:
   - Provide exact notation (e.g., "d/dx(x^2) = 2x" not "derivative of x squared")
   - Describe mathematical symbols precisely
   - For code: include language, syntax, and structure
   - For diagrams: describe all components, labels, arrows, and relationships

4. EDUCATIONAL CONTEXT: Assess and capture:
   - Difficulty level (beginner/intermediate/advanced)
   - Prerequisites needed to understand this segment
   - How concepts relate to broader topics
   - Teaching approach or methodology used

5. COGNITIVE SUMMARY: Write a brief 1-2 sentence overview that captures the essence of each segment for quick scanning.

JSON STRUCTURE (list of objects):
{
  "timestamp_start_str": "HH:MM:SS",
  "timestamp_end_str": "HH:MM:SS",
  "cognitive_summary": "Brief 1-2 sentence overview of what happens in this segment",
  "speaker_info": {
    "name": "Speaker name (or 'Unknown' if not identified)",
    "role": "Instructor/Student/Guest Expert/etc.",
    "visual_description": "Physical appearance, clothing, position in frame"
  },
  "transcript_snippet": "Complete, verbatim transcript of all spoken words in this segment",
  "visual_description": "Comprehensive description of ALL visual elements: layout, colors, text, diagrams, movements, gestures, spatial relationships. Be extremely detailed.",
  "technical_details": "Precise notation for any formulas, equations, code, or technical diagrams. Include exact mathematical symbols, operators, and structure.",
  "key_concepts": ["Primary Concept 1", "Primary Concept 2"],
  "educational_context": {
    "difficulty_level": "beginner|intermediate|advanced",
    "prerequisites": ["Prerequisite concept 1", "Prerequisite concept 2"],
    "related_concepts": ["Related topic 1", "Related topic 2"]
  }
}

EXAMPLE:
[
  {
    "timestamp_start_str": "00:01:15",
    "timestamp_end_str": "00:01:25",
    "cognitive_summary": "Instructor introduces the power rule for derivatives using a visual example on the board.",
    "speaker_info": {
      "name": "Dr. Sarah Chen",
      "role": "Instructor",
      "visual_description": "Woman in blue blazer, standing at whiteboard on left side of frame, holding red marker"
    },
    "transcript_snippet": "Now, as we see here, the derivative of x-squared is 2x. This is an application of the power rule, which states that if we have x to the n, the derivative is n times x to the n minus one.",
    "visual_description": "Digital whiteboard occupies center of frame with white background. On the left side in red marker: 'd/dx(x²) = 2x' written in large text. To the right, a blue parabola graph labeled 'y = x²' with x and y axes marked. Below the equation, a boxed formula reads 'Power Rule: d/dx(xⁿ) = n·xⁿ⁻¹'. Instructor's hand points to the exponent in the equation with the marker.",
    "technical_details": "Main equation: d/dx(x²) = 2x. General power rule formula: d/dx(xⁿ) = n·xⁿ⁻¹. Graph shows parabola y = x² with standard Cartesian axes.",
    "key_concepts": ["Calculus", "Derivative", "Power Rule", "Differentiation"],
    "educational_context": {
      "difficulty_level": "beginner",
      "prerequisites": ["Basic algebra", "Function notation", "Exponents"],
      "related_concepts": ["Chain rule", "Product rule", "Integration", "Limits"]
    }
  }
]

JSON FORMATTING REQUIREMENTS (CRITICAL - FOLLOW EXACTLY):
- Use ONLY double quotes (") for all strings and property names, never single quotes
- Put a comma (,) between EVERY object in the array - do NOT forget commas
- NO trailing commas after the last item in arrays or objects
- All objects must be separated by commas: [{...},{...},{...}]
- Properly escape special characters: use \" for quotes, \n for newlines, \\ for backslashes
- Keep all text on single lines or use \n for line breaks within strings
- Ensure ALL brackets [ ] and braces { } are properly closed
- Every opening { must have a closing }
- Every opening [ must have a closing ]
- Valid JSON only - no comments, no explanatory text
- Do NOT use markdown code blocks

COMMON MISTAKES TO AVOID:
- Missing commas between array objects: [{...}{...}] ❌ Should be: [{...},{...}] ✓
- Trailing commas: [{...},] ❌ Should be: [{...}] ✓
- Single quotes: {'name': 'value'} ❌ Should be: {"name": "value"} ✓
- Unescaped quotes in strings: "He said "hello"" ❌ Should be: "He said \"hello\"" ✓
- Malformed string endings: "text."." ❌ Should be: "text." ✓
- Double punctuation at end: "text"." ❌ Should be: "text." ✓

IMPORTANT: Return ONLY the valid JSON array. No markdown, no explanation, just pure JSON starting with [ and ending with ].
"""

# --- Modified to accept history_dir, client, and save raw output ---
# --- Returns list on success, dict with error on failure ---
def extract_multimodal_data(video_url: str, history_dir: str, client: genai.Client) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Calls the Gemini API to extract structured data from a video URL.
    Uses the provided client instance (no client creation/cleanup).
    Saves raw response to history_dir.
    Returns list of extracted data on success, or {'error': message} on failure.
    """
    log.info(f"Starting multimodal extraction for URL: {video_url}")

    raw_response_path = os.path.join(history_dir, "gemini_extraction_raw_output.txt")
    parsed_json_path = os.path.join(history_dir, "gemini_extraction_parsed.json")

    try:
        log.info("📡 Calling Gemini API for video extraction...")
        video_part = types.Part(
            file_data=types.FileData(file_uri=video_url, mime_type="video/mp4")
        )
        prompt_part = types.Part(text=GEMINI_PROMPT)

        try:
            response = client.models.generate_content(
                model='models/gemini-2.5-flash', # Corrected model name if needed
                contents=types.Content(parts=[video_part, prompt_part]),
            )
            raw_text = response.text
            log.info("✅ Gemini extraction response received.")
        except Exception as api_error:
            error_msg = str(api_error).lower()
            if "rate" in error_msg or "quota" in error_msg or "limit" in error_msg:
                log.error(f"🚫 Gemini API rate limit exceeded during video extraction: {api_error}")
                return {"error": f"API rate limit exceeded. Please wait a moment and try again. (Gemini free tier: 3 RPM, 10K TPM)"}
            else:
                raise

        # --- Save Raw Response ---
        try:
            with open(raw_response_path, 'w', encoding='utf-8') as f:
                f.write(raw_text)
            log.info(f"Saved raw Gemini extraction response to {raw_response_path}")
        except Exception as save_err:
            log.error(f"Failed to save raw Gemini response: {save_err}")
        # --- End Save ---

        log.info("Attempting to parse JSON from response...")
        
        # Clean up response: remove markdown code blocks if present
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```"):
            # Remove markdown code blocks
            cleaned_text = re.sub(r'^```(?:json)?\s*\n', '', cleaned_text)
            cleaned_text = re.sub(r'\n```\s*$', '', cleaned_text)
        
        # Use regex to find the first valid JSON array (list)
        json_match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)

        if not json_match:
            error_msg = "No valid JSON array (starting with '[') found in Gemini response."
            log.error(error_msg)
            log.debug(f"Raw response was saved to {raw_response_path}")
            return {"error": error_msg} # Return error dictionary

        json_string = json_match.group(0)
        
        # Try to fix common JSON issues
        def fix_json_string(s: str) -> str:
            """Attempt to fix common JSON formatting issues"""
            # Remove trailing commas before closing brackets/braces
            s = re.sub(r',(\s*[}\]])', r'\1', s)
            
            # Fix duplicated quote-period patterns: ."." → ."
            s = re.sub(r'\."\."', '."', s)
            
            # Fix missing commas between array elements (common with line breaks)
            # This pattern looks for: } followed by whitespace and { (missing comma between objects)
            s = re.sub(r'}\s+{', '},{', s)
            
            # Fix missing commas between string values and objects
            s = re.sub(r'"\s+{', '",{', s)
            
            # Fix missing commas between closing brace and string
            s = re.sub(r'}\s+"', '},"', s)
            
            # Fix malformed string endings: ". at end of value → "
            s = re.sub(r'\."(\s*[,\}\]])', r'"\1', s)
            
            # Remove any control characters that might cause issues
            s = ''.join(char for char in s if ord(char) >= 32 or char in '\n\r\t')
            
            return s
        
        json_string = fix_json_string(json_string)

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
            log.error(f"JSON error at line {e.lineno}, column {e.colno}: {e.msg}")
            log.debug(f"Problematic JSON section (first 500 chars): {json_string[:500]}")
            
            # Save the problematic JSON for debugging
            error_json_path = os.path.join(history_dir, "gemini_extraction_failed_json.txt")
            try:
                with open(error_json_path, 'w', encoding='utf-8') as f:
                    f.write("=== FAILED TO PARSE THIS JSON ===\n\n")
                    f.write(json_string)
                    f.write(f"\n\n=== ERROR DETAILS ===\n")
                    f.write(f"Line {e.lineno}, Column {e.colno}: {e.msg}\n")
                log.info(f"Saved failed JSON to {error_json_path} for debugging")
            except Exception as save_err:
                log.error(f"Failed to save problematic JSON: {save_err}")
            
            return {"error": f"{error_msg}. The video extraction completed but returned invalid JSON format. Please try again or contact support."} # Return error dictionary

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

# --- F3.1 & F3.2: Semantic Indexing - Enhanced for new data structure ---
def index_video_data(job_id: str, video_url: str, extracted_data: List[Dict[str, Any]]):
    """
    Index enriched video data with comprehensive metadata including speaker info,
    educational context, and technical details.
    """
    if not extracted_data:
        log.warning(f"No data to index for job_id: {job_id}")
        return

    log.info(f"Starting indexing for job_id: {job_id}. {len(extracted_data)} items to index.")
    documents, metadatas, ids = [], [], []
    for i, event in enumerate(extracted_data):
        try:
            # Extract speaker information (ensure strings)
            speaker_info = event.get('speaker_info', {})
            speaker_name = str(speaker_info.get('name', 'Unknown')) if isinstance(speaker_info, dict) else 'Unknown'
            speaker_role = str(speaker_info.get('role', 'N/A')) if isinstance(speaker_info, dict) else 'N/A'
            
            # Extract educational context (convert lists to strings)
            edu_context = event.get('educational_context', {})
            difficulty = str(edu_context.get('difficulty_level', 'N/A')) if isinstance(edu_context, dict) else 'N/A'
            prerequisites = edu_context.get('prerequisites', []) if isinstance(edu_context, dict) else []
            prerequisites_str = ', '.join(str(p) for p in prerequisites) if prerequisites else 'None'
            
            # Convert all list fields to comma-separated strings
            key_concepts = event.get('key_concepts', [])
            key_concepts_str = ', '.join(str(k) for k in key_concepts) if key_concepts else 'None'
            
            # Build comprehensive document text for semantic search
            document_text = f"""Timestamp: {event.get('timestamp_start_str', 'N/A')}
Speaker: {speaker_name} ({speaker_role})
Summary: {event.get('cognitive_summary', '')}
Transcript: {event.get('transcript_snippet', '')}
Visual Description: {event.get('visual_description', '')}
Technical Details: {event.get('technical_details', '')}
Key Concepts: {key_concepts_str}
Difficulty: {difficulty}
Prerequisites: {prerequisites_str}"""
            
            documents.append(document_text)
            
            # Store rich metadata for retrieval (ChromaDB only accepts scalar values: str, int, float, bool, None)
            metadata = {
                "job_id": str(job_id),
                "video_url": str(video_url),
                "event_index": int(i),
                "timestamp_start_str": str(event.get('timestamp_start_str', 'N/A')),
                "timestamp_end_str": str(event.get('timestamp_end_str', 'N/A')),
                "cognitive_summary": str(event.get('cognitive_summary', '')),
                "speaker_name": str(speaker_name),
                "speaker_role": str(speaker_role),
                "raw_transcript": str(event.get('transcript_snippet', '')),
                "raw_visuals": str(event.get('visual_description', '')),
                "technical_details": str(event.get('technical_details', '')),
                "key_concepts": str(key_concepts_str),
                "difficulty_level": str(difficulty),
                "prerequisites": str(prerequisites_str)
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
    
