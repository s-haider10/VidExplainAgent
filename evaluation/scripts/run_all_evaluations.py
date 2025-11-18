#!/usr/bin/env python3
"""
Run Complete Evaluation Suite

Runs all evaluations (component-level, RAG, visualization) and generates final report.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import logging
from component_eval import run_component_evaluation
from rag_eval import run_rag_evaluation
from utils import load_json, save_json, format_latex_table
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_final_report(
    component_results: dict,
    rag_results: dict,
    human_eval_results: dict = None,
    output_path: str = "../results/final_report.md"
):
    """Generate comprehensive evaluation report."""
    
    report = "# VidExplainAgent Evaluation Results\n\n"
    report += "## Executive Summary\n\n"
    
    # Component-level summary
    report += "### Component-Level (VLM) Performance\n\n"
    report += f"- **BLEU-4**: {component_results['summary']['BLEU-4_mean']:.4f}\n"
    report += f"- **ROUGE-L F1**: {component_results['summary']['ROUGE-L-F1_mean']:.4f}\n"
    report += f"- **BERTScore F1**: {component_results['summary']['BERTScore-F1_mean']:.4f}\n\n"
    
    # RAG summary
    report += "### End-to-End RAG Performance\n\n"
    for metric, score in rag_results['summary'].items():
        report += f"- **{metric}**: {score:.4f}\n"
    report += "\n"
    
    # Human evaluation summary
    if human_eval_results:
        report += "### Human Evaluation Summary\n\n"
        for dim, stats in human_eval_results['dimension_statistics'].items():
            dim_name = dim.replace('_score', '').capitalize()
            report += f"- **{dim_name}**: {stats['mean']:.2f} ± {stats['std']:.2f}\n"
        report += "\n"
    
    # Detailed tables
    report += "## Detailed Results\n\n"
    
    report += "### Component-Level Metrics (Per-Metric Statistics)\n\n"
    report += "| Metric | Mean | Median | Std | Min | Max |\n"
    report += "|--------|------|--------|-----|-----|-----|\n"
    for metric, stats in component_results['aggregated_scores'].items():
        report += f"| {metric} | {stats['mean']:.4f} | {stats['median']:.4f} | {stats['std']:.4f} | {stats['min']:.4f} | {stats['max']:.4f} |\n"
    report += "\n"
    
    report += "### RAG Metrics (Per-Metric Statistics)\n\n"
    report += "| Metric | Mean | Median | Std | Min | Max |\n"
    report += "|--------|------|--------|-----|-----|-----|\n"
    for metric, stats in rag_results['metric_statistics'].items():
        report += f"| {metric} | {stats['mean']:.4f} | {stats['median']:.4f} | {stats['std']:.4f} | {stats['min']:.4f} | {stats['max']:.4f} |\n"
    report += "\n"
    
    # Save report
    with open(output_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Final report saved to: {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Run complete evaluation suite"
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
        "--human-eval",
        type=str,
        default=None,
        help="Path to human evaluation results JSON (optional)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="../results",
        help="Directory to save all results"
    )
    parser.add_argument(
        "--openai-key",
        type=str,
        default=None,
        help="OpenAI API key for RAGAS"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("="* 70)
    logger.info("COMPLETE EVALUATION SUITE")
    logger.info("=" * 70)
    logger.info("")
    
    # Run component evaluation
    logger.info("Step 1/3: Running component-level evaluation...")
    component_results = run_component_evaluation(
        args.ground_truth,
        args.generated,
        os.path.join(args.output_dir, "component_scores.json")
    )
    logger.info("✅ Component evaluation complete!")
    logger.info("")
    
    # Run RAG evaluation
    logger.info("Step 2/3: Running RAG evaluation...")
    rag_results = run_rag_evaluation(
        args.qa_pairs,
        args.system_responses,
        os.path.join(args.output_dir, "rag_scores.json"),
        args.openai_key
    )
    logger.info("✅ RAG evaluation complete!")
    logger.info("")
    
    # Load human evaluation if provided
    human_eval_results = None
    if args.human_eval:
        logger.info("Step 3/3: Loading human evaluation results...")
        human_eval_results = load_json(args.human_eval)
        logger.info("✅ Human evaluation loaded!")
        logger.info("")
    
    # Generate final report
    logger.info("Generating final report...")
    report = generate_final_report(
        component_results,
        rag_results,
        human_eval_results,
        os.path.join(args.output_dir, "final_report.md")
    )
    logger.info("✅ Final report generated!")
    logger.info("")
    
    logger.info("=" * 70)
    logger.info("ALL EVALUATIONS COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Results saved to: {args.output_dir}/")
    logger.info("")
    logger.info("Files generated:")
    logger.info(f"  - component_scores.json")
    logger.info(f"  - rag_scores.json")
    logger.info(f"  - final_report.md")


if __name__ == "__main__":
    main()

