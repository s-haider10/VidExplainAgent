#!/usr/bin/env python3
"""
Run Component-Level Evaluation (VLM)

Evaluates visual description quality using BLEU, ROUGE, and BERTScore.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import logging
from component_eval import run_component_evaluation
from utils import load_json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run component-level evaluation of visual descriptions"
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        required=True,
        help="Path to ground truth annotations JSON"
    )
    parser.add_argument(
        "--generated",
        type=str,
        required=True,
        help="Path to system-generated descriptions JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../results/component_scores.json",
        help="Path to save evaluation results"
    )
    
    args = parser.parse_args()
    
    logger.info("="* 60)
    logger.info("COMPONENT-LEVEL EVALUATION (VLM)")
    logger.info("=" * 60)
    logger.info(f"Ground Truth: {args.ground_truth}")
    logger.info(f"Generated: {args.generated}")
    logger.info(f"Output: {args.output}")
    logger.info("")
    
    try:
        results = run_component_evaluation(
            args.ground_truth,
            args.generated,
            args.output
        )
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("EVALUATION COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Results saved to: {args.output}")
        logger.info("")
        logger.info("Summary Scores:")
        logger.info(f"  BLEU-4: {results['summary']['BLEU-4_mean']:.4f}")
        logger.info(f"  ROUGE-L F1: {results['summary']['ROUGE-L-F1_mean']:.4f}")
        logger.info(f"  BERTScore F1: {results['summary']['BERTScore-F1_mean']:.4f}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

