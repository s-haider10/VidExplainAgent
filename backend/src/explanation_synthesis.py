# backend/src/explanation_synthesis.py

import os
import uuid
import logging
import wave
import json # Added for saving JSON
import asyncio
import aiofiles
from typing import List, Dict, Any, Optional, Literal
from google import genai
from google.genai import types
from google.genai.client import Client as GenAIClient

log = logging.getLogger(__name__)

# TTS Provider type
TTSProvider = Literal["macos", "gemini"]
DEFAULT_TTS_PROVIDER: TTSProvider = "macos"  # Default to macOS native TTS (best for Mac users)

# --- F5.1: LLM-powered Explanation Synthesis ---

RAG_PROMPT_TEMPLATE = """
You are a friendly, concise, and engaging science communicator. You create accessible and vivid explanations for Blind and Low Vision (BLV) learners.

YOUR CORE MISSION:
Answer the user's query using ONLY the provided video context. Your goal is maximum clarity and minimal cognitive load. **Be extremely concise.**

CRITICAL RULES - YOU MUST FOLLOW THESE:

1.  **BE CONCISE - THIS IS THE MOST IMPORTANT RULE.**
    * **DO NOT** write long, multi-paragraph essays.
    * Keep the **ENTIRE** response under 120 words.
    * Break complex ideas into very short, simple paragraphs (2-3 sentences MAX).

2.  **PROGRESSIVE DISCLOSURE (SIMPLE):**
    * **Step 1:** Start with a 1-2 sentence **Direct Answer** or overview.
    * **Step 2:** Add 1-2 **Key Details** that build on the answer, using simple language.
    * **Step 3:** If the query is technical, add **Technical Specifics** (like formulas), but always explain them simply.

3.  **ACCESSIBILITY FOR BLV LEARNERS:**
    * Focus on the explanation. Verbally describe key visual elements mentioned in the context (e.g., "The video shows electrons as green dots...").
    * Describe spatial relationships simply.

4.  **SYNTHESIZE, DON'T JUST LIST:**
    * Integrate information from multiple timestamps into a coherent, simple narrative.
    * Don't Reference timestamps in your explanation.

WHAT TO AVOID:
* **AVOID LONG PARAGRAPHS.** (This is the most common mistake.)
* **AVOID JARGON.** If a technical term from the video is necessary, define it immediately.
* **AVOID REPETITION.** Don't re-explain the same concept.
* **AVOID EXTERNAL KNOWLEDGE.** Stick 100% to the provided context.
* **AVOID CONVERSATIONAL FILLER.** Be friendly, but get straight to the point.
* **AVOID "Educational Context"** like prerequisites or difficulty levels. Focus only on the answer.

---
CONTEXT FROM VIDEO:
{context_str}
---

USER QUERY:
{query}

ANSWER (Short, simple, and following all rules above):
"""

# --- Modified to accept history_dir and save raw output (NOW ASYNC) ---
async def generate_text_explanation(client: GenAIClient, context_chunks: List[Dict[str, Any]], query: str, history_dir: str) -> Dict[str, Any]:
    """
    Synthesizes a textual explanation using Gemini 2.5-flash.
    Saves raw response to history_dir using async file operations.
    Returns the text and the timestamps it was based on.
    """
    log.info(f"Synthesizing explanation for query: {query}")

    raw_response_path = os.path.join(history_dir, "gemini_text_raw_output.txt")
    parsed_response_path = os.path.join(history_dir, "gemini_text_parsed.json") # Saving structured proto

    # Build enriched context string with all available metadata
    context_str = "\n---\n".join(
        [
            f"Timestamp: {chunk.get('timestamp_start_str', 'N/A')} - {chunk.get('timestamp_end_str', 'N/A')}\n"
            f"Summary: {chunk.get('cognitive_summary', 'N/A')}\n"
            f"Speaker: {chunk.get('speaker_name', 'Unknown')} ({chunk.get('speaker_role', 'N/A')})\n"
            f"Transcript: {chunk.get('raw_transcript', 'No transcript.')}\n"
            f"Visual Description: {chunk.get('raw_visuals', 'No visual description.')}\n"
            f"Technical Details: {chunk.get('technical_details', 'None')}\n"
            f"Key Concepts: {chunk.get('key_concepts', 'N/A')}\n"
            f"Difficulty: {chunk.get('difficulty_level', 'N/A')}\n"
            f"Prerequisites: {chunk.get('prerequisites', 'None')}"
            for chunk in context_chunks
        ]
    )
    formatted_prompt = RAG_PROMPT_TEMPLATE.format(context_str=context_str, query=query)

    # Call the text-generation model with retry logic for transient errors
    log.info("📡 Calling Gemini API for text generation...")
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=formatted_prompt
            )
            explanation_text = response.text
            log.info(f"✅ Received text response from Gemini ({len(explanation_text)} chars)")
            break  # Success, exit retry loop
            
        except Exception as api_error:
            error_msg = str(api_error).lower()
            error_code = str(api_error)
            
            # Check for transient errors (503, 429, overload)
            is_transient = (
                "503" in error_code or 
                "overloaded" in error_msg or 
                "unavailable" in error_msg or
                "429" in error_code
            )
            
            # Check for rate limit errors
            is_rate_limit = "rate" in error_msg or "quota" in error_msg or "limit" in error_msg
            
            if is_transient and attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                log.warning(f"⚠️ Gemini API temporarily unavailable (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            elif is_rate_limit:
                log.error(f"🚫 Gemini API rate limit exceeded: {api_error}")
                raise Exception(f"API rate limit exceeded. Please wait a moment and try again. (Gemini free tier: 3 RPM, 10K TPM)")
            else:
                log.error(f"❌ Gemini API error: {api_error}")
                raise
    else:
        # All retries exhausted
        raise Exception("Gemini API is currently overloaded. Please try again in a few moments.")

    # --- Save Raw Response (async file I/O) ---
    try:
        async with aiofiles.open(raw_response_path, 'w', encoding='utf-8') as f:
            await f.write(explanation_text)
        log.info(f"Saved raw Gemini text response to {raw_response_path}")
    except Exception as save_err:
        log.error(f"Failed to save raw Gemini text response: {save_err}")
    # --- End Save ---

    # --- Save Parsed/Structured Response (async file I/O) ---
    try:
        # Try to save response metadata (API structure may vary)
        resp_dict = {
            "text": explanation_text,
            "model": "gemini-2.5-flash",
            "char_count": len(explanation_text)
        }
        async with aiofiles.open(parsed_response_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(resp_dict, indent=2))
        log.info(f"Saved structured Gemini text response to {parsed_response_path}")
    except Exception as save_err:
        log.error(f"Failed to save structured Gemini text response: {save_err}")
    # --- End Save ---


    referenced_timestamps = sorted(
        list(set([chunk.get('timestamp_start_str') for chunk in context_chunks if chunk.get('timestamp_start_str')]))
    )

    return {
        "text": explanation_text,
        "timestamps": referenced_timestamps
    }

# --- F5.2: Auditory Output (TTS) ---

async def _generate_audio_macos_tts(text_to_speak: str, file_path: str) -> None:
    """
    Generate audio using macOS native TTS (FREE, high quality, no limits).
    Uses the same voices as Siri - excellent quality on Mac.
    """
    import asyncio
    
    try:
        # Use macOS 'say' command with high-quality voice
        # Available voices: Samantha (female), Alex (male), Daniel (British), Karen (Australian)
        voice = "Alex"  # Clear male voice, similar to Siri
        
        # Create temporary AIFF file first (say command native format)
        temp_aiff = file_path.replace('.wav', '.aiff')
        
        # Run 'say' command asynchronously (AIFF is native format)
        process = await asyncio.create_subprocess_exec(
            'say',
            '-v', voice,
            '-o', temp_aiff,
            text_to_speak,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"macOS say command failed: {error_msg}")
        
        # Convert AIFF to WAV using afconvert (built-in macOS tool)
        convert_process = await asyncio.create_subprocess_exec(
            'afconvert',
            '-f', 'WAVE',
            '-d', 'LEI16@24000',  # 16-bit PCM, 24kHz (same as Gemini)
            temp_aiff,
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await convert_process.communicate()
        
        if convert_process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"Audio conversion failed: {error_msg}")
        
        # Clean up temp file
        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)
        
        log.info(f"✅ macOS TTS audio generated successfully: {file_path}")
        
    except Exception as e:
        log.error(f"❌ macOS TTS generation failed: {e}", exc_info=True)
        raise


async def _generate_audio_gemini_tts(client: GenAIClient, text_to_speak: str, file_path: str) -> None:
    """
    Generate audio using Gemini TTS (requires API calls, subject to rate limits).
    Higher quality but limited to 1-3 RPM on free tier.
    """
    tts_prompt = f"Say aloud in a warm and scholarly tone: {text_to_speak}"
    
    try:
        response = client.models.generate_content(
           model="gemini-2.5-flash-preview-tts",
           contents=tts_prompt,
           config=types.GenerateContentConfig(
              response_modalities=["AUDIO"],
              speech_config=types.SpeechConfig(
                 voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                       voice_name='Sadaltager',
                    )
                 )
              ),
           )
        )
        log.info("✅ Received TTS response from Gemini")
        
        # Extract audio data and write to file
        data = response.candidates[0].content.parts[0].inline_data.data
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(data)
        log.info(f"✅ Gemini TTS audio written successfully: {file_path}")
        
    except Exception as api_error:
        error_msg = str(api_error).lower()
        if "rate" in error_msg or "quota" in error_msg or "limit" in error_msg:
            log.error(f"🚫 Gemini TTS API rate limit exceeded: {api_error}")
            raise Exception(f"API rate limit exceeded for text-to-speech. Please wait a moment and try again. (Gemini TTS free tier: 3 RPM)")
        else:
            log.error(f"❌ Gemini TTS API error: {api_error}")
            raise


# --- Modified to accept history_dir, TTS provider, and save raw output (NOW ASYNC) ---
async def generate_audio_explanation(
    client: Optional[GenAIClient], 
    text_to_speak: str, 
    history_dir: str,
    tts_provider: TTSProvider = DEFAULT_TTS_PROVIDER
) -> str:
    """
    Generates a .wav file from text using specified TTS provider.
    Supports: edge (free, no limits) or gemini (higher quality, rate limited).
    Returns the *relative URL* of the saved audio file.
    """
    log.info(f"Generating audio explanation using {tts_provider} TTS...")

    audio_details_path = os.path.join(history_dir, "audio_details.json")

    audio_dir = "static/audio"
    os.makedirs(audio_dir, exist_ok=True)

    audio_uuid = str(uuid.uuid4())
    file_path = os.path.join(audio_dir, f"{audio_uuid}.wav")

    try:
        # Route to appropriate TTS provider
        if tts_provider == "macos":
            log.info("🎤 Using macOS native TTS (free, high quality, no limits)")
            await _generate_audio_macos_tts(text_to_speak, file_path)
            provider_info = {
                "provider": "macos",
                "voice": "Alex (Siri-quality)",
                "cost": "free",
                "rate_limits": "none"
            }
        elif tts_provider == "gemini":
            if not client:
                raise ValueError("Gemini TTS requires a client but none was provided")
            log.info("🎤 Using Gemini TTS (high quality, rate limited)")
            await _generate_audio_gemini_tts(client, text_to_speak, file_path)
            provider_info = {
                "provider": "gemini",
                "voice": "Sadaltager",
                "cost": "api_calls",
                "rate_limits": "3 RPM (free tier)"
            }
        else:
            raise ValueError(f"Unknown TTS provider: {tts_provider}")

        # --- Save Audio Metadata (async file I/O) ---
        try:
            audio_details = {
                "saved_path_relative": f"/{file_path}",
                "file_uuid": audio_uuid,
                "text_length": len(text_to_speak),
                **provider_info
            }
            async with aiofiles.open(audio_details_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(audio_details, indent=2))
            log.info(f"Saved audio metadata to {audio_details_path}")
        except Exception as save_err:
            log.error(f"Failed to save audio metadata: {save_err}")
        # --- End Save ---

        log.info(f"✅ Audio file saved to: {file_path}")
        return f"/{file_path}"

    except Exception as e:
        log.error(f"❌ Error during TTS generation: {e}", exc_info=True)
        # Save error info (async file I/O)
        error_path = os.path.join(history_dir, "tts_error.txt")
        try:
            import traceback
            error_content = f"Error during TTS generation:\nProvider: {tts_provider}\nError: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            async with aiofiles.open(error_path, mode='w', encoding='utf-8') as f:
                await f.write(error_content)
        except Exception as save_err:
            log.error(f"Failed to save TTS error log: {save_err}")
        raise  # Re-raise the exception so it's handled by the caller