#!/usr/bin/env python3
"""
Run End-to-End RAG Evaluation

Evaluates RAG system performance using RAGAS metrics.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import logging
from dotenv import load_dotenv
from rag_eval import run_rag_evaluation

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logging.info(f"Loaded environment from {env_path}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run end-to-end RAG system evaluation with RAGAS"
    )
    parser.add_argument(
        "--qa-pairs",
        type=str,
        required=True,
        help="Path to ground truth Q&A pairs JSON"
    )
    parser.add_argument(
        "--system-responses",
        type=str,
        required=True,
        help="Path to system-generated responses JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../results/rag_scores.json",
        help="Path to save evaluation results"
    )
    parser.add_argument(
        "--openai-key",
        type=str,
        default=None,
        help="OpenAI API key for RAGAS evaluation (uses env var if not provided)"
    )
    
    args = parser.parse_args()
    
    logger.info("="* 60)
    logger.info("END-TO-END RAG EVALUATION (RAGAS)")
    logger.info("=" * 60)
    logger.info(f"Q&A Pairs: {args.qa_pairs}")
    logger.info(f"System Responses: {args.system_responses}")
    logger.info(f"Output: {args.output}")
    logger.info("")
    
    try:
        results = run_rag_evaluation(
            args.qa_pairs,
            args.system_responses,
            args.output,
            args.openai_key
        )
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("EVALUATION COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Results saved to: {args.output}")
        logger.info("")
        logger.info("Summary Scores:")
        for metric, score in results['summary'].items():
            logger.info(f"  {metric}: {score:.4f}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

