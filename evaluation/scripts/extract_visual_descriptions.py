#!/usr/bin/env python3
"""
Extract Visual Descriptions from ChromaDB

Directly accesses the ChromaDB to extract all indexed visual descriptions.
"""

import sys
import json
from pathlib import Path

# Add backend src to path
backend_path = Path(__file__).parent.parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

import chromadb

def extract_descriptions(job_id: str, output_file: str):
    """Extract all visual descriptions from ChromaDB for a given job ID."""
    
    print(f"Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="../../backend/chroma_db")
    
    print(f"Getting collection for job {job_id}...")
    try:
        collection = client.get_collection(name=job_id)
    except Exception as e:
        print(f"❌ Error: Collection not found for job_id: {job_id}")
        print(f"   {e}")
        return
    
    print(f"Fetching all documents...")
    results = collection.get(
        include=['documents', 'metadatas']
    )
    
    print(f"✅ Retrieved {len(results['documents'])} chunks")
    
    # Convert to format matching manual annotations
    descriptions = []
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        descriptions.append({
            "timestamp_start_str": metadata.get('timestamp_start_str', ''),
            "timestamp_end_str": metadata.get('timestamp_end_str', ''),
            "visual_description": metadata.get('visual_description', ''),
            "transcript_snippet": metadata.get('transcript_snippet', ''),
            "cognitive_summary": metadata.get('cognitive_summary', ''),
            "key_concepts": metadata.get('key_concepts', '').split(', ') if metadata.get('key_concepts') else [],
            "speaker_name": metadata.get('speaker_name', ''),
            "difficulty_level": metadata.get('difficulty_level', ''),
        })
    
    # Sort by timestamp
    descriptions.sort(key=lambda x: x['timestamp_start_str'])
    
    print(f"Saving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(descriptions, f, indent=2)
    
    print(f"✅ Saved {len(descriptions)} descriptions")
    
    # Print first one as sample
    if descriptions:
        print(f"\n📄 Sample description:")
        print(f"   Timestamp: {descriptions[0]['timestamp_start_str']} - {descriptions[0]['timestamp_end_str']}")
        print(f"   Visual: {descriptions[0]['visual_description'][:100]}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_visual_descriptions.py <job_id> [output_file]")
        sys.exit(1)
    
    job_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "../results/system_generated_descriptions.json"
    
    extract_descriptions(job_id, output_file)

