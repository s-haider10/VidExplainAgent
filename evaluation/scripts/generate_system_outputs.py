#!/usr/bin/env python3
"""
Generate System Outputs for Evaluation

Processes the test video through VidExplainAgent and collects:
1. Generated visual descriptions (from ingestion pipeline)
2. System responses to Q&A pairs (from explanation synthesis)
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import time
import requests
import argparse
import logging
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "http://localhost:8000"


def submit_video(video_url: str) -> str:
    """Submit video for processing and return video ID."""
    logger.info(f"Submitting video: {video_url}")
    
    response = requests.post(
        f"{BACKEND_URL}/upload-video-url",
        json={"video_url": video_url}
    )
    
    if response.status_code == 200:
        data = response.json()
        video_id = data.get("job_id")  # Changed from video_id to job_id
        logger.info(f"✅ Video submitted successfully! Job ID: {video_id}")
        return video_id
    else:
        raise Exception(f"Failed to submit video: {response.status_code} - {response.text}")


def wait_for_processing(video_id: str, timeout: int = 600) -> Dict[str, Any]:
    """Wait for video processing to complete."""
    logger.info(f"Waiting for video processing (ID: {video_id})...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{BACKEND_URL}/video-status/{video_id}")
        
        if response.status_code == 200:
            status_data = response.json()
            status = status_data.get("status")
            
            logger.info(f"Status: {status}")
            
            if status == "completed":
                logger.info("✅ Processing complete!")
                return status_data
            elif status == "failed":
                raise Exception(f"Video processing failed: {status_data.get('error')}")
            
        time.sleep(5)  # Check every 5 seconds
    
    raise Exception(f"Timeout waiting for video processing (>{timeout}s)")


def get_generated_descriptions(video_id: str) -> List[Dict[str, Any]]:
    """Extract generated visual descriptions from the system."""
    logger.info("Fetching generated visual descriptions...")
    
    # Try to get from the backend's history or database
    # For now, we'll need to access the indexed data
    # This would typically come from querying all chunks
    
    response = requests.post(
        f"{BACKEND_URL}/query-video",
        json={
            "job_id": video_id,
            "query": "Describe everything you see in the video from start to finish"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        # The retrieved_contexts should contain our indexed data
        # We need to extract the original indexed format
        
        logger.info(f"✅ Retrieved {len(data.get('retrieved_contexts', []))} chunks")
        return data.get('retrieved_contexts', [])
    else:
        raise Exception(f"Failed to retrieve descriptions: {response.status_code}")


def generate_qa_responses(video_id: str, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate system responses to Q&A pairs."""
    logger.info(f"Generating responses for {len(qa_pairs)} questions...")
    
    responses = []
    
    for i, qa in enumerate(qa_pairs, 1):
        logger.info(f"Processing question {i}/{len(qa_pairs)}: {qa['id']}")
        
        response = requests.post(
            f"{BACKEND_URL}/query-video",
            json={
                "job_id": video_id,
                "query": qa['question']
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            responses.append({
                "question_id": qa['id'],
                "question": qa['question'],
                "answer": data.get('explanation_text', ''),
                "retrieved_contexts": data.get('referenced_timestamps', [])
            })
            
            logger.info(f"✅ Response generated for {qa['id']}")
        else:
            logger.error(f"❌ Failed to get response for {qa['id']}: {response.status_code}")
            responses.append({
                "question_id": qa['id'],
                "question": qa['question'],
                "answer": "",
                "retrieved_contexts": [],
                "error": response.text
            })
        
        time.sleep(1)  # Rate limiting
    
    return responses


def main():
    parser = argparse.ArgumentParser(
        description="Generate system outputs for evaluation"
    )
    parser.add_argument(
        "--video-url",
        type=str,
        required=True,
        help="YouTube video URL to process"
    )
    parser.add_argument(
        "--qa-pairs",
        type=str,
        required=True,
        help="Path to Q&A pairs JSON file"
    )
    parser.add_argument(
        "--output-descriptions",
        type=str,
        default="../results/system_generated_descriptions.json",
        help="Path to save generated descriptions"
    )
    parser.add_argument(
        "--output-responses",
        type=str,
        default="../results/system_responses.json",
        help="Path to save Q&A responses"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("GENERATING SYSTEM OUTPUTS FOR EVALUATION")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        # Load Q&A pairs
        logger.info(f"Loading Q&A pairs from: {args.qa_pairs}")
        with open(args.qa_pairs, 'r') as f:
            qa_data = json.load(f)
        qa_pairs = qa_data['qa_pairs']
        logger.info(f"Loaded {len(qa_pairs)} Q&A pairs")
        logger.info("")
        
        # Submit video
        video_id = submit_video(args.video_url)
        logger.info("")
        
        # Wait for processing
        status = wait_for_processing(video_id)
        logger.info("")
        
        # Get generated descriptions
        descriptions = get_generated_descriptions(video_id)
        
        # Save descriptions
        with open(args.output_descriptions, 'w') as f:
            json.dump(descriptions, f, indent=2)
        logger.info(f"✅ Saved descriptions to: {args.output_descriptions}")
        logger.info("")
        
        # Generate Q&A responses
        responses = generate_qa_responses(video_id, qa_pairs)
        
        # Save responses
        response_data = {
            "video_id": video_id,
            "video_url": args.video_url,
            "responses": responses
        }
        with open(args.output_responses, 'w') as f:
            json.dump(response_data, f, indent=2)
        logger.info(f"✅ Saved responses to: {args.output_responses}")
        logger.info("")
        
        logger.info("=" * 70)
        logger.info("SYSTEM OUTPUT GENERATION COMPLETE!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("You can now run the evaluation scripts:")
        logger.info(f"  python scripts/run_all_evaluations.py \\")
        logger.info(f"    --ground-truth data/ground_truth/manual_annotations.json \\")
        logger.info(f"    --generated {args.output_descriptions} \\")
        logger.info(f"    --qa-pairs {args.qa_pairs} \\")
        logger.info(f"    --system-responses {args.output_responses}")
        
    except Exception as e:
        logger.error(f"Failed to generate system outputs: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

