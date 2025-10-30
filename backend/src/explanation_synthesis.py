# backend/src/explanation_synthesis.py

import os
import uuid
import logging
import wave
import json # Added for saving JSON
from typing import List, Dict, Any
from google import genai
from google.genai import types
from google.genai.client import Client as GenAIClient
from google.protobuf.json_format import MessageToDict # Added for saving proto

log = logging.getLogger(__name__)

# --- F5.1: LLM-powered Explanation Synthesis ---

RAG_PROMPT_TEMPLATE = """
You are a helpful and scholarly AI assistant for a Blind or Low Vision (BLV) learner.
Your goal is to answer the user's query based *only* on the provided video context.
Do not use any outside knowledge.
Be clear, concise, and descriptive.
When relevant, reference the timestamps from the context to help the user.

---
CONTEXT FROM VIDEO:
{context_str}
---

USER QUERY:
{query}

ANSWER:
"""

# --- Modified to accept history_dir and save raw output ---
def generate_text_explanation(client: GenAIClient, context_chunks: List[Dict[str, Any]], query: str, history_dir: str) -> Dict[str, Any]:
    """
    Synthesizes a textual explanation using Gemini 2.5-flash.
    Saves raw response to history_dir.
    Returns the text and the timestamps it was based on.
    """
    log.info(f"Synthesizing explanation for query: {query}")

    raw_response_path = os.path.join(history_dir, "gemini_text_raw_output.txt")
    parsed_response_path = os.path.join(history_dir, "gemini_text_parsed.json") # Saving structured proto

    context_str = "\n---\n".join(
        [
            f"Timestamp: {chunk.get('timestamp_start_str', 'N/A')}\n"
            f"Transcript: {chunk.get('raw_transcript', 'No transcript.')}\n"
            f"Visuals: {chunk.get('raw_visuals', 'No visual description.')}"
            for chunk in context_chunks
        ]
    )
    formatted_prompt = RAG_PROMPT_TEMPLATE.format(context_str=context_str, query=query)

    # Call the text-generation model
    response = client.models.generate_content(
        model='models/gemini-2.5-flash',
        contents=formatted_prompt
    )

    explanation_text = response.text

    # --- Save Raw Response ---
    try:
        with open(raw_response_path, 'w', encoding='utf-8') as f:
            f.write(explanation_text)
        log.info(f"Saved raw Gemini text response to {raw_response_path}")
    except Exception as save_err:
        log.error(f"Failed to save raw Gemini text response: {save_err}")
    # --- End Save ---

    # --- Save Parsed/Structured Response ---
    try:
        # Convert proto message to dictionary before saving
        resp_dict = MessageToDict(response._result)
        with open(parsed_response_path, 'w', encoding='utf-8') as f:
            json.dump(resp_dict, f, indent=2)
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

def _wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

# --- Modified to accept history_dir and save raw output ---
def generate_audio_explanation(client: GenAIClient, text_to_speak: str, history_dir: str) -> str:
    """
    Generates a .wav file from text using the new TTS model.
    Saves response details to history_dir.
    Returns the *relative URL* of the saved audio file.
    """
    log.info("Generating audio explanation...")

    audio_details_path = os.path.join(history_dir, "gemini_audio_details.json")

    audio_dir = "static/audio"
    os.makedirs(audio_dir, exist_ok=True)

    audio_uuid = str(uuid.uuid4())
    file_path = os.path.join(audio_dir, f"{audio_uuid}.wav")

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

        # --- Save Audio Response Details ---
        try:
            # Convert proto message to dictionary before saving
            resp_dict = MessageToDict(response._result)
            audio_details = {
                "saved_path_relative": f"/{file_path}",
                 # Save details excluding the large inline_data bytes
                "response_details": {k: v for k, v in resp_dict.items() if k != 'candidates'}
            }
             # Add candidate info without inline_data if available
            if 'candidates' in resp_dict and resp_dict['candidates']:
                 candidate = resp_dict['candidates'][0]
                 audio_details["response_details"]['candidate'] = {
                      k: v for k, v in candidate.items() if k != 'content'
                 }
                 if 'content' in candidate and candidate['content'].get('parts'):
                     audio_details["response_details"]['candidate']['content_part_info'] = {
                         k: v for k, v in candidate['content']['parts'][0].items() if k != 'inlineData'
                     }
            with open(audio_details_path, 'w', encoding='utf-8') as f:
                json.dump(audio_details, f, indent=2)
            log.info(f"Saved Gemini audio response details to {audio_details_path}")
        except Exception as save_err:
            log.error(f"Failed to save Gemini audio response details: {save_err}")
        # --- End Save ---


        data = response.candidates[0].content.parts[0].inline_data.data
        _wave_file(file_path, data)
        log.info(f"Audio file saved to: {file_path}")

        return f"/{file_path}"

    except Exception as e:
        log.error(f"Error during TTS generation: {e}", exc_info=True)
         # Save error info
        error_path = os.path.join(history_dir, "tts_error.txt")
        try:
            with open(error_path, mode='w', encoding='utf-8') as f:
                 f.write(f"Error during TTS generation:\n{str(e)}\n\nTraceback:\n")
                 import traceback
                 traceback.print_exc(file=f)
        except Exception as save_err:
            log.error(f"Failed to save TTS error log: {save_err}")
        return "" # Return empty string or indicate error